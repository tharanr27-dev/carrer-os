/**
 * Typed client for the CareerOS FastAPI backend (/api/v1).
 *
 * - Attaches the stored access token automatically and transparently refreshes it once on 401.
 * - Normalises FastAPI `detail` errors and the `{success,data,errors}` envelope into `ApiError`.
 * - Endpoint functions return plain data: the envelope is unwrapped where the backend wraps it.
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

// ─── Envelope & errors ───────────────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
  errors?: string[] | null;
  request_id?: string | null;
  timestamp?: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly errors: string[];

  constructor(message: string, status: number, errors: string[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errors = errors;
  }
}

/** Best-effort user-facing message for anything thrown by the client. */
export function errorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

function messageFromPayload(payload: unknown, status: number): { message: string; errors: string[] } {
  const body = (payload ?? {}) as {
    detail?: unknown;
    message?: string;
    errors?: string[] | null;
  };

  if (typeof body.detail === "string") return { message: body.detail, errors: [] };

  if (Array.isArray(body.detail)) {
    const errors = body.detail.map((item: { loc?: unknown[]; msg?: string }) => {
      const field = Array.isArray(item.loc) ? String(item.loc[item.loc.length - 1]) : "";
      return field ? `${field}: ${item.msg}` : String(item.msg);
    });
    return { message: errors.join("; "), errors };
  }

  if (body.errors?.length) return { message: body.errors.join("; "), errors: body.errors };
  if (body.message) return { message: body.message, errors: [] };
  return { message: `Request failed with status ${status}`, errors: [] };
}

// ─── Token storage ───────────────────────────────────────────────────────────

const TOKEN_STORAGE_KEY = "careeros_auth_tokens";

export interface StoredTokens {
  accessToken: string;
  refreshToken: string;
}

export function getStoredTokens(): StoredTokens | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as StoredTokens) : null;
  } catch {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    return null;
  }
}

export function setStoredTokens(tokens: StoredTokens) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));
  } catch {
    /* storage unavailable: session lasts only until reload */
  }
}

export function clearStoredTokens() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

let sessionExpiredHandler: (() => void) | null = null;

/** The auth store registers this so an unrecoverable 401 logs the user out. */
export function onSessionExpired(handler: () => void) {
  sessionExpiredHandler = handler;
}

// ─── Core request ────────────────────────────────────────────────────────────

type Query = Record<string, string | number | boolean | undefined | null>;

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  form?: FormData;
  query?: Query;
  /** Set false for public endpoints (login/register/refresh). */
  auth?: boolean;
}

function buildUrl(path: string, query?: Query) {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const tokens = getStoredTokens();
  if (!tokens?.refreshToken) return false;

  refreshInFlight ??= (async () => {
    try {
      const response = await fetch(buildUrl("/auth/refresh"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: tokens.refreshToken }),
      });
      if (!response.ok) return false;
      const fresh = (await response.json()) as AuthTokenResponse;
      setStoredTokens({ accessToken: fresh.access_token, refreshToken: fresh.refresh_token });
      return true;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

async function send(path: string, options: RequestOptions, token: string | null): Promise<Response> {
  const headers: Record<string, string> = {};
  if (!options.form) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    return await fetch(buildUrl(path, options.query), {
      method: options.method ?? "GET",
      headers,
      body: options.form ?? (options.body !== undefined ? JSON.stringify(options.body) : undefined),
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check your connection and try again.", 0);
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const useAuth = options.auth !== false;
  let response = await send(path, options, useAuth ? (getStoredTokens()?.accessToken ?? null) : null);

  if (response.status === 401 && useAuth) {
    if (await refreshTokens()) {
      response = await send(path, options, getStoredTokens()?.accessToken ?? null);
    }
    if (response.status === 401) {
      clearStoredTokens();
      sessionExpiredHandler?.();
    }
  }

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const { message, errors } = messageFromPayload(payload, response.status);
    throw new ApiError(message, response.status, errors);
  }

  return payload as T;
}

/** Calls an enveloped endpoint and returns `data`. */
async function data<T>(path: string, options?: RequestOptions): Promise<T> {
  const envelope = await request<ApiResponse<T>>(path, options);
  return envelope.data as T;
}

/** Calls an endpoint and returns `null` on 404 (the backend uses 404 for "nothing yet"). */
async function orNull<T>(call: () => Promise<T>): Promise<T | null> {
  try {
    return await call();
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

// ─── Types (mirror backend Pydantic schemas) ─────────────────────────────────

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthUserResponse {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface MeResponse extends AuthUserResponse {
  roles: string[];
  permissions: string[];
  company_id: string | null;
  college_id: string | null;
}

export interface ExperienceResponse {
  id: string;
  company: string;
  title: string;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  description?: string | null;
}

export interface SocialLinks {
  linkedin?: string | null;
  github?: string | null;
  portfolio?: string | null;
  twitter?: string | null;
}

export interface ProfileResponse {
  id: string;
  user_id: string;
  first_name?: string | null;
  last_name?: string | null;
  headline?: string | null;
  bio?: string | null;
  profile_image_url?: string | null;
  social_links?: SocialLinks | null;
  role_specific_data?: Record<string, unknown> | null;
  completion_percentage: number;
  experiences: ExperienceResponse[];
}

export interface ProfileUpdate {
  first_name?: string;
  last_name?: string;
  headline?: string;
  bio?: string;
  profile_image_url?: string;
  social_links?: SocialLinks;
  role_specific_data?: Record<string, unknown>;
}

// analytics
export interface StudentDashboard {
  career_readiness: number;
  resume_score: number;
  interview_score: number;
  today_interviews: number;
  today_tasks: number;
  trends: { ats_score_delta: number; interview_score_delta: number };
}

export interface AIUsageAnalyticsCreate {
  module: string;
  provider?: string | null;
  model?: string | null;
  prompt_version?: string | null;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  estimated_cost_usd?: number;
  latency_ms?: number | null;
  success?: boolean;
  error_message?: string | null;
  retry_count?: number;
}

export interface AIUsageAnalyticsResponse {
  id: string;
  user_id?: string | null;
  module: string;
  provider?: string | null;
  model?: string | null;
  prompt_version?: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  latency_ms?: number | null;
  success: boolean;
  error_message?: string | null;
  retry_count: number;
  created_at: string;
}

// discovery
export interface AssessmentQuestion {
  id: string;
  question_text: string;
  question_type: string;
  options: string[] | null;
  order_index: number;
}
export interface AssessmentTemplate {
  id: string;
  title: string;
  description: string | null;
  version: string | null;
  questions: AssessmentQuestion[];
}
export interface AnswerSubmission {
  question_id: string;
  answer_text?: string;
  selected_options?: string[];
}
export interface CareerMatch {
  job_title: string;
  suitability_score: number;
  confidence_score: number;
  reasoning: string;
}
export interface CareerReport {
  id: string;
  personality_analysis: Record<string, unknown>;
  interest_analysis: Record<string, unknown>;
  skill_gaps: Record<string, unknown>;
  career_timeline: Record<string, unknown>;
  matches: CareerMatch[];
}

// resumes
export interface ResumeSummary {
  id: string;
  file_name: string;
  status: string;
  created_at: string;
}
export interface ResumeUpload {
  id: string;
  file_name: string;
  status: string;
  message: string;
}
export interface ResumeSuggestion {
  category: string;
  suggestion_text: string;
  impact: string;
}
export interface ResumeAnalysis {
  id: string;
  ats_score: number;
  grammar_score: number;
  quality_score: number;
  keyword_analysis: Record<string, unknown>;
  suggestions: ResumeSuggestion[];
}

// mentor
export interface MentorMessage {
  id: string;
  role: string;
  content: string;
}
export interface MentorSession {
  id: string;
  title: string;
  status: string;
  messages: MentorMessage[];
}
export interface GoalMilestone {
  id: string;
  title: string;
  status: string;
}
export interface CareerGoal {
  id: string;
  title: string;
  description: string | null;
  status: string;
  source: string;
  milestones: GoalMilestone[];
}

// interviews & communication
export interface InterviewSession {
  id: string;
  interview_type: string;
  status: string;
}
export interface CommunicationSession {
  id: string;
  mode: string;
  status: string;
}

export interface InterviewReport {
  session_id: string;
  overall_score: number;
  technical_score: number;
  communication_score: number;
  detailed_analysis: Record<string, unknown> | null;
  recommended_learning: string[] | null;
}
export interface CommunicationReport {
  session_id: string;
  overall_score: number;
  grammar_score: number;
  vocabulary_score: number;
  tone_score: number;
  fluency_score: number;
  strengths: string[];
  weaknesses: string[];
  improvement_suggestions: string[];
}

// learning
export interface LearningTask {
  id: string;
  title: string;
  description: string | null;
  resource_url: string | null;
  resource_type: string | null;
  estimated_minutes: number | null;
  difficulty: string;
  status: string;
}
export interface LearningModule {
  id: string;
  title: string;
  description: string | null;
  order_index: number;
  estimated_hours: number | null;
  status: string;
  tasks: LearningTask[];
}
export interface LearningRoadmap {
  id: string;
  title: string;
  target_role: string | null;
  target_company: string | null;
  version: number;
  status: string;
  modules: LearningModule[];
}

// recommendations
export interface Recommendation {
  id: string;
  category: string;
  title: string;
  description: string | null;
  confidence_score: number;
  estimated_impact: number;
  difficulty: string;
  priority: number;
  reason: string | null;
  related_skills: string[] | null;
  source_modules: string[] | null;
  status: string;
  expires_at: string | null;
  version: number;
}
export interface RecommendationFeed {
  user_id: string;
  generated_at: string;
  recommendations: Recommendation[];
  total: number;
}

// community
export interface Tag {
  id: string;
  name: string;
}
export interface Post {
  id: string;
  user_id: string;
  title: string;
  content: string;
  category: string;
  status: string;
  views_count: number;
  reactions_count: number;
  comments_count: number;
  tags: Tag[];
  created_at: string;
  updated_at: string;
}
export interface FeedItem {
  post: Post;
  relevance_score: number | null;
}
export interface Comment {
  id: string;
  post_id: string;
  user_id: string;
  content: string;
  parent_id: string | null;
  status: string;
  reactions_count: number;
  created_at: string;
}

// recruiters
export interface Company {
  id: string;
  name: string;
  domain: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
}
export interface Job {
  id: string;
  company_id: string;
  title: string;
  description: string;
  location: string | null;
  status: string;
  requirements: string[] | null;
  benefits: string[] | null;
  pipeline_stages: string[] | null;
  created_at: string;
}
export interface OpenJob extends Job {
  company_name: string | null;
}
export interface JobCreate {
  title: string;
  description: string;
  location?: string;
  requirements?: string[];
  benefits?: string[];
  pipeline_stages?: string[];
}
export interface JobApplication {
  id: string;
  job_id: string;
  candidate_id: string;
  status: string;
  fit_score: string | null;
  match_details: Record<string, unknown> | null;
  ai_insights: Record<string, unknown> | null;
  created_at: string;
}

export interface RecommendedJobMatch {
  score: number;
  matched_skills: string[];
  reason: string;
}

export interface RecommendedJobItem {
  id: string;
  title: string;
  company: string;
  company_slug: string | null;
  company_logo: string | null;
  location: string;
  remote: boolean;
  eligible_countries: string[];
  employment_type: string | null;
  seniority: string[];
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  salary_period: string | null;
  description: string;
  posted_at: string | null;
  expires_at: string | null;
  apply_url: string;
  source: string;
  match: RecommendedJobMatch | null;
}

export interface RecommendedJobsResponse {
  success: boolean;
  source: string;
  attribution: { name: string; url: string };
  filters: {
    query: string | null;
    country: string | null;
    page: number;
    seniority: string | null;
    employment_type: string | null;
    worldwide: boolean | null;
    exclude_worldwide: boolean | null;
  };
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  match_method: string | null;
  jobs: RecommendedJobItem[];
}

export interface RecommendedJobsParams {
  q?: string;
  country?: string;
  page?: number;
  employment_type?: string;
  seniority?: string;
  worldwide?: boolean;
  exclude_worldwide?: boolean;
}
// â”€â”€â”€ Interview Preparation (training) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export type TrainingRound = "aptitude" | "technical" | "coding" | "communication" | "hr" | "resume" | "managerial";
export type TrainingMode = "practice" | "exam" | "mock";

export interface TrainingMeta {
  rounds: {
    key: TrainingRound;
    label: string;
    stage: number;
    groups: { name: string; topics: { slug: string; label: string; questions: number }[] }[];
  }[];
  target_roles: string[];
  levels: string[];
  difficulties: string[];
  ai_available: boolean;
  ai_note: string | null;
  labels: string[];
  disclaimer: string;
}

export interface TrainingCoding {
  title: string;
  input_format: string;
  output_format: string;
  constraints: string[];
  examples: { input: string; output: string; note?: string }[];
  hints: string[];
  tests: { input: string; output: string }[];
  time_complexity: string;
  space_complexity: string;
  concepts: string[];
  language?: string;
  schema_sql?: string;
}

export interface TrainingEvaluation {
  method?: string;
  disclaimer?: string;
  criteria?: Record<string, number>;
  strengths?: string[];
  improvements?: string[];
  structure_note?: string;
  stronger_answer?: string | null;
  fallback_reason?: string;
  self_passed?: number;
  self_total?: number;
}

export interface TrainingResult {
  is_correct: boolean | null;
  correct_index: number | null;
  explanation: string | null;
  model_answer: string | null;
  score: number | null;
  score_kind: "objective" | "ai_estimate" | "keyword_estimate" | "self_assessed" | null;
  evaluation: TrainingEvaluation | null;
}

export interface TrainingItem {
  id: string;
  position: number;
  round: TrainingRound;
  topic: string;
  topic_label: string;
  difficulty: string;
  qtype: "mcq" | "text" | "code";
  prompt: string;
  options: string[] | null;
  label: string | null;
  source: string;
  review_status: string;
  is_follow_up: boolean;
  coding: TrainingCoding | null;
  answered: boolean;
  answer: { index?: number; text?: string } | null;
  time_taken_sec: number | null;
  result: TrainingResult | null;
}

export interface TrainingSummary {
  total_questions: number;
  answered: number;
  skipped: number;
  correct: number;
  objective_total: number;
  objective_pct: number | null;
  estimated_pct: number | null;
  self_assessed_pct: number | null;
  overall_pct: number | null;
  total_time_sec: number | null;
  avg_time_sec: number | null;
  by_topic: { round: TrainingRound; topic: string; label: string; attempted: number; score_pct: number }[];
  by_round: Record<string, { label: string; attempted: number; score_pct: number | null; objective_pct: number | null; estimated_pct: number | null }>;
  strengths: string[];
  weak_areas: string[];
  suggestions: TrainingAction[];
  change_vs_previous: number | null;
  previous_overall_pct: number | null;
  score_notes: string;
  readiness_note?: string;
}

export interface TrainingAction {
  title: string;
  reason: string;
  action: { type: "practice" | "mock"; round?: TrainingRound; topic?: string | null; difficulty?: string | null; mode?: TrainingMode };
  rule?: string;
}

export interface TrainingAttempt {
  id: string;
  mode: TrainingMode;
  round: TrainingRound | "mock";
  topic: string | null;
  difficulty: string | null;
  status: "IN_PROGRESS" | "COMPLETED";
  config: { notices?: string[]; rounds?: string[]; role?: string; planned_count?: number } | null;
  time_limit_sec: number | null;
  started_at: string;
  deadline: string | null;
  ended_at: string | null;
  summary: TrainingSummary | null;
  items: TrainingItem[];
  ai_available: boolean;
}

export interface TrainingAttemptRow {
  id: string;
  mode: TrainingMode;
  round: string;
  topic: string | null;
  difficulty: string | null;
  status: "IN_PROGRESS" | "COMPLETED";
  started_at: string;
  ended_at: string | null;
  overall_pct: number | null;
  planned: number | null;
}

export interface TrainingRoundProgress {
  label: string;
  stage: number;
  attempted: number;
  objective_pct: number | null;
  estimated_pct: number | null;
  self_assessed_pct: number | null;
  combined_pct: number | null;
  avg_time_sec: number | null;
  status: "not_started" | "in_progress" | "needs_work" | "on_track" | "strong";
  last_practised: string | null;
}

export interface TrainingProfile {
  target_role: string | null;
  level: "fresher" | "junior" | "mid";
  language: "en" | "ta";
  resume_data: {
    projects: { title: string; description?: string | null; tech_stack?: string | null }[];
    skills: string[];
    degree?: string | null;
    source: "student_edited" | "profile";
  };
}

export interface TrainingProgress {
  overall_pct: number | null;
  total_scored_answers: number;
  rounds: Record<TrainingRound, TrainingRoundProgress>;
  current_stage: { round: string; label: string; status: string };
  weakest_topics: { round: TrainingRound; topic: string; label: string; attempted: number; score_pct: number }[];
  strongest_topics: { round: TrainingRound; topic: string; label: string; attempted: number; score_pct: number }[];
  completion_rate: number | null;
  attempts_total: number;
  attempts_completed: number;
  trend: { attempt_id: string; date: string | null; round: string; topic: string | null; overall_pct: number }[];
  improvement_pct_points: number | null;
  recent_attempts: TrainingAttemptRow[];
  recommendations: TrainingAction[];
  scoring_rules: string[];
  resume_attempt: TrainingAttemptRow | null;
  profile: TrainingProfile;
}

export interface TrainingAttemptCreate {
  mode: TrainingMode;
  round?: TrainingRound;
  topic?: string | null;
  difficulty?: string | null;
  count?: number;
  time_limit_sec?: number | null;
  adaptive?: boolean;
  generate?: boolean;
  qtype?: "mcq" | "text";
  mock?: {
    role?: string | null;
    level: string;
    rounds: TrainingRound[];
    duration_min: number;
    difficulty?: string | null;
    language: "en" | "ta";
  };
}

export interface TrainingAnswerBody {
  item_id: string;
  index?: number;
  text?: string;
  self_passed?: number;
  self_total?: number;
  time_taken_sec?: number;
}

export interface TrainingAnswerResponse {
  saved: boolean;
  item_id?: string;
  item?: TrainingItem;
  follow_up?: TrainingItem | null;
}

export interface MyApplication {
  id: string;
  job_id: string;
  job_title: string | null;
  company_name: string | null;
  status: string;
  fit_score: string | null;
  created_at: string;
}

// placements
export interface College {
  id: string;
  name: string;
  domain: string;
  address: string | null;
  is_active: boolean;
  created_at: string;
}
export interface PlacementDrive {
  id: string;
  college_id: string;
  company_id: string | null;
  title: string;
  description: string | null;
  drive_type: string;
  status: string;
  date_of_drive: string | null;
  requirements: Record<string, unknown> | null;
  created_at: string;
}
export interface DriveCreate {
  title: string;
  description?: string;
  drive_type?: string;
  date_of_drive?: string;
  requirements?: Record<string, unknown>;
}
export interface DriveRegistration {
  id: string;
  drive_id: string;
  student_id: string;
  status: string;
  created_at: string;
}
export interface OfferLetter {
  id: string;
  registration_id: string;
  package_details: string | null;
  status: string;
  created_at: string;
}
export interface AcceptedResponse {
  status: string;
  message?: string;
}

// admin
export interface AdminUser {
  id: string;
  email: string;
  status: string;
  roles: string[];
  created_at: string;
}
export interface AdminDashboardSummary {
  total_users: number;
  active_users: number;
  pending_moderation_count: number;
  system_status: string;
  unresolved_reports: number;
  ai_daily_token_usage: number;
  ai_monthly_cost_usd: number;
}
export interface SystemHealth {
  database_ok: boolean;
  redis_ok: boolean;
  celery_ok: boolean;
  storage_ok: boolean;
  details?: Record<string, unknown> | null;
  checked_at: string;
}
export interface FeatureFlag {
  id: string;
  key: string;
  is_enabled: boolean;
  description: string | null;
  allowed_roles: string[] | null;
  allowed_users: string[] | null;
  rollout_percentage: number;
  created_at: string;
}
export interface PlatformSetting {
  id: string;
  key: string;
  value: string | null;
  value_type: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}
export interface ModerationItem {
  id: string;
  entity_type: string;
  entity_id: string;
  reason: string | null;
  reported_by: string | null;
  status: string;
  created_at: string;
}
export interface Announcement {
  id: string;
  title: string;
  content: string;
  severity: string;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
}
export interface AuditLog {
  id: string;
  admin_id: string;
  action: string;
  target_type: string | null;
  target_id: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}
export interface LlmProvider {
  id: string;
  name: string;
  api_key_vault_ref: string | null;
  is_active: boolean;
  priority: number;
  failover_provider_name: string | null;
  daily_token_limit: number;
  monthly_token_limit: number;
  provider_status: string;
  created_at: string;
}
export interface ModelConfig {
  id: string;
  provider_name: string;
  model_name: string;
  temperature: number;
  top_p: number;
  max_tokens: number;
  retry_count: number;
  timeout: number;
  is_active: boolean;
  created_at: string;
}
export interface PromptVersion {
  id: string;
  module: string;
  version: string;
  prompt_text: string;
  is_active: boolean;
  published_by: string | null;
  created_at: string;
}
export interface Role {
  id: string;
  name: string;
  description: string | null;
}
export interface Permission {
  id: string;
  name: string;
  description: string | null;
}
export interface MaintenanceStatus {
  [key: string]: unknown;
}
export interface BackgroundJob {
  id: string;
  job_name: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
}
export interface AiProviderTestResult {
  status: string;
  response_text: string;
  latency_ms: number;
  tokens_used: number;
}

// ─── Endpoints ───────────────────────────────────────────────────────────────

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<AuthTokenResponse>("/auth/login", { method: "POST", body: { email, password }, auth: false }),
  register: (email: string, password: string) =>
    request<AuthUserResponse>("/auth/register", { method: "POST", body: { email, password }, auth: false }),
  refreshToken: (refreshToken: string) =>
    request<AuthTokenResponse>("/auth/refresh", { method: "POST", body: { refresh_token: refreshToken }, auth: false }),
  me: () => request<MeResponse>("/auth/me"),

  // Users
  getProfile: () => data<ProfileResponse>("/users/me/profile"),
  updateProfile: (profile: ProfileUpdate) =>
    data<ProfileResponse>("/users/me/profile", { method: "PUT", body: profile }),

  // Analytics
  studentDashboard: () => request<StudentDashboard>("/analytics/dashboard/student"),
  logEvent: (event: { event_type: string; module: string; entity_id?: string; payload?: Record<string, unknown> }) =>
    request<{ status: string }>("/analytics/events", { method: "POST", body: event }),
  logAiUsage: (usage: AIUsageAnalyticsCreate) =>
    request<AIUsageAnalyticsResponse>("/analytics/ai-usage", { method: "POST", body: usage }),

  // Career discovery
  discoveryTemplates: () => data<AssessmentTemplate[]>("/discovery/templates"),
  submitAssessment: (templateId: string, answers: AnswerSubmission[]) =>
    data<{ assessment_id: string; status: string }>(`/discovery/assessments/${templateId}/submit`, {
      method: "POST",
      body: { answers },
    }),
  /** Accepts the report id or the assessment id returned by submitAssessment. `null` = still processing. */
  discoveryReport: (id: string) => orNull(() => data<CareerReport>(`/discovery/reports/${id}`)),

  // Resumes
  listResumes: () => data<ResumeSummary[]>("/resumes"),
  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return data<ResumeUpload>("/resumes/upload", { method: "POST", form });
  },
  /** `null` = analysis not ready yet. */
  resumeAnalysis: (resumeId: string) => orNull(() => data<ResumeAnalysis>(`/resumes/${resumeId}/analysis`)),
  resumeDownloadUrl: (resumeId: string) => data<{ url: string }>(`/resumes/${resumeId}/download`),

  // Mentor
  createMentorSession: () => data<MentorSession>("/mentor/sessions", { method: "POST" }),
  /** `null` = no conversation yet. */
  latestMentorSession: () => orNull(() => data<MentorSession>("/mentor/sessions/latest")),
  listGoals: () => data<CareerGoal[]>("/mentor/goals"),
  sendMentorMessage: (sessionId: string, content: string) =>
    data<MentorMessage>(`/mentor/sessions/${sessionId}/message`, { method: "POST", body: { content } }),
  createGoal: (goal: { title: string; description?: string; milestones?: { title: string }[] }) =>
    data<CareerGoal>("/mentor/goals", { method: "POST", body: goal }),

  // Interviews & communication (REST part; live turns go over WebSocket, see openSessionSocket)
  createInterviewSession: (body: { interview_type?: string; company?: string; difficulty?: string }) =>
    data<InterviewSession>("/interviews/sessions", { method: "POST", body }),
  createCommunicationSession: (mode = "WORKPLACE") =>
    data<CommunicationSession>("/communication/sessions", { method: "POST", body: { mode } }),
  /** `null` = report still being generated. */
  interviewReport: (sessionId: string) => orNull(() => data<InterviewReport>(`/interviews/sessions/${sessionId}/report`)),
  communicationReport: (sessionId: string) =>
    orNull(() => data<CommunicationReport>(`/communication/sessions/${sessionId}/report`)),

  // Learning
  generateRoadmap: (body: { target_role?: string; target_company?: string }) =>
    data<{ roadmap_id: string; status: string }>("/learning/roadmaps/generate", { method: "POST", body }),
  /** `null` = no roadmap yet. */
  activeRoadmap: () => orNull(() => data<LearningRoadmap>("/learning/roadmaps/active")),
  completeTask: (taskId: string) =>
    data<{ task_id: string; status: string }>("/learning/tasks/complete", {
      method: "POST",
      body: { task_id: taskId },
    }),

  // Recommendations
  /** `null` = no feed generated yet. */
  recommendationFeed: () => orNull(() => data<RecommendationFeed>("/recommendations/feed")),
  refreshRecommendations: () => data<{ status: string; message: string }>("/recommendations/refresh", { method: "POST" }),
  recommendationFeedback: (recommendationId: string, action: string, feedbackText?: string) =>
    data<{ feedback_id: string; action: string }>("/recommendations/feedback", {
      method: "POST",
      body: { recommendation_id: recommendationId, action, feedback_text: feedbackText },
    }),

  // Community
  latestFeed: (limit = 20, offset = 0) => request<FeedItem[]>("/community/feed/latest", { query: { limit, offset } }),
  trendingFeed: (limit = 20, offset = 0) =>
    request<FeedItem[]>("/community/feed/trending", { query: { limit, offset } }),
  searchPosts: (q: string, limit = 20, offset = 0) =>
    request<Post[]>("/community/search", { query: { q, limit, offset } }),
  createPost: (post: { title: string; content: string; category: string; tags?: string[] }) =>
    request<Post>("/community/posts", { method: "POST", body: post }),
  getPost: (postId: string) => request<Post>(`/community/posts/${postId}`),
  getComments: (postId: string) => request<Comment[]>(`/community/posts/${postId}/comments`),
  addComment: (postId: string, content: string, parentId?: string) =>
    request<Comment>(`/community/posts/${postId}/comments`, {
      method: "POST",
      body: { content, parent_id: parentId },
    }),
  react: (entityType: "post" | "comment", entityId: string, reactionType = "like") =>
    request<{ status: string }>("/community/reactions", {
      method: "POST",
      body: { entity_type: entityType, entity_id: entityId, reaction_type: reactionType },
    }),

  // Recruiters
  createCompany: (body: { name: string; domain: string; description?: string }) =>
    request<Company>("/recruiters/company", { method: "POST", body }),
  createJob: (job: JobCreate) => request<Job>("/recruiters/jobs", { method: "POST", body: job }),
  companyJobs: () => request<Job[]>("/recruiters/jobs"),
  openJobs: () => request<OpenJob[]>("/recruiters/jobs/open"),
  recommendedJobs: (params?: RecommendedJobsParams) =>
    request<RecommendedJobsResponse>("/jobs/recommended", { query: { ...params } }),
  trainingMeta: () => data<TrainingMeta>("/training/meta"),
  trainingProfile: () => data<TrainingProfile>("/training/profile"),
  updateTrainingProfile: (body: { target_role?: string | null; level?: string; language?: string; resume_data?: { projects: { title: string; description?: string | null; tech_stack?: string | null }[]; skills: string[]; degree?: string | null }; reset_resume_data?: boolean }) =>
    data<TrainingProfile>("/training/profile", { method: "PUT", body }),
  trainingProgress: () => data<TrainingProgress>("/training/progress"),
  trainingStart: (body: TrainingAttemptCreate) => data<TrainingAttempt>("/training/attempts", { method: "POST", body }),
  trainingAttempt: (id: string) => data<TrainingAttempt>(`/training/attempts/${id}`),
  trainingAnswer: (id: string, body: TrainingAnswerBody) =>
    data<TrainingAnswerResponse>(`/training/attempts/${id}/answer`, { method: "POST", body }),
  trainingNext: (id: string, body: { generate?: boolean; count?: number; qtype?: "mcq" | "text" }) =>
    data<{ attempt: TrainingAttempt; added: TrainingItem[]; notices: string[] }>(`/training/attempts/${id}/next`, { method: "POST", body }),
  trainingFinish: (id: string) => data<TrainingAttempt>(`/training/attempts/${id}/finish`, { method: "POST" }),
  trainingHistory: (page = 1, size = 10, status?: string) =>
    data<{ page: number; size: number; total: number; items: TrainingAttemptRow[] }>("/training/attempts", { query: { page, size, status } }),
  applyToJob: (jobId: string) => request<JobApplication>(`/recruiters/jobs/${jobId}/apply`, { method: "POST" }),
  myApplications: () => request<MyApplication[]>("/recruiters/applications/mine"),
  jobApplications: (jobId: string) => request<JobApplication[]>(`/recruiters/jobs/${jobId}/applications`),
  updateApplicationStatus: (applicationId: string, status: string) =>
    request<JobApplication>(`/recruiters/applications/${applicationId}`, { method: "PATCH", body: { status } }),

  // Placements
  createCollege: (body: { name: string; domain: string; address?: string }) =>
    request<College>("/placements/colleges", { method: "POST", body }),
  createDrive: (drive: DriveCreate) => request<PlacementDrive>("/placements/drives", { method: "POST", body: drive }),
  collegeDrives: () => request<PlacementDrive[]>("/placements/drives"),
  availableDrives: () => request<PlacementDrive[]>("/placements/drives/available"),
  getDrive: (driveId: string) => request<PlacementDrive>(`/placements/drives/${driveId}`),
  calculateEligibility: (driveId: string) =>
    request<AcceptedResponse>(`/placements/drives/${driveId}/calculate-eligibility`, { method: "POST" }),
  rankStudents: (driveId: string) =>
    request<AcceptedResponse>(`/placements/drives/${driveId}/rank`, { method: "POST" }),
  registerForDrive: (driveId: string) =>
    request<DriveRegistration>(`/placements/drives/${driveId}/register`, { method: "POST" }),
  myRegistrations: () => request<DriveRegistration[]>("/placements/registrations/mine"),
  driveRegistrations: (driveId: string) =>
    request<DriveRegistration[]>(`/placements/drives/${driveId}/registrations`),
  updateRegistrationStatus: (registrationId: string, status: string) =>
    request<DriveRegistration>(`/placements/registrations/${registrationId}`, { method: "PATCH", body: { status } }),
  releaseOffer: (registrationId: string, packageDetails: string) =>
    request<OfferLetter>(`/placements/registrations/${registrationId}/offer`, {
      method: "POST",
      body: { package_details: packageDetails },
    }),

  // Admin
  admin: {
    summary: () => request<AdminDashboardSummary>("/admin/dashboard/summary"),
    health: () => request<SystemHealth>("/admin/health/check"),
    users: () => data<AdminUser[]>("/admin/users"),
    setUserStatus: (userId: string, status: string) =>
      data<{ user_id: string; status: string }>(`/admin/users/${userId}/status`, {
        method: "PUT",
        body: { status },
      }),
    assignRole: (userId: string, roleName: string) =>
      data<{ user_id: string; role: string }>(`/admin/users/${userId}/roles/assign`, {
        method: "POST",
        query: { role_name: roleName },
      }),
    roles: () => data<Role[]>("/admin/roles"),
    permissions: () => data<Permission[]>("/admin/permissions"),
    flags: () => data<FeatureFlag[]>("/admin/flags"),
    createFlag: (flag: { key: string; is_enabled?: boolean; description?: string; rollout_percentage?: number }) =>
      request<FeatureFlag>("/admin/flags", { method: "POST", body: flag }),
    updateFlag: (flagId: string, update: { is_enabled: boolean; rollout_percentage?: number }) =>
      request<FeatureFlag>(`/admin/flags/${flagId}`, { method: "PUT", body: update }),
    settings: () => data<PlatformSetting[]>("/admin/settings"),
    createSetting: (setting: { key: string; value: string; value_type?: string; description?: string }) =>
      request<PlatformSetting>("/admin/settings", { method: "POST", body: setting }),
    updateSetting: (key: string, value: string) =>
      request<PlatformSetting>(`/admin/settings/${encodeURIComponent(key)}`, { method: "PUT", body: { value } }),
    moderationQueue: (statusFilter?: string) =>
      data<ModerationItem[]>("/admin/moderation/queue", { query: { status_filter: statusFilter } }),
    moderationDecision: (itemId: string, decision: string, reason?: string) =>
      data<unknown>(`/admin/moderation/queue/${itemId}/decision`, { method: "POST", body: { decision, reason } }),
    activeAnnouncements: () => data<Announcement[]>("/admin/announcements/active"),
    createAnnouncement: (a: { title: string; content: string; severity?: string; expires_at?: string }) =>
      request<Announcement>("/admin/announcements", { method: "POST", body: a }),
    broadcast: (b: { title: string; content: string; recipient_type: string }) =>
      request<unknown>("/admin/broadcast", { method: "POST", body: b }),
    auditLogs: (limit = 50, offset = 0) => data<AuditLog[]>("/admin/audit/logs", { query: { limit, offset } }),
    healthSnapshots: () => data<unknown>("/admin/health/snapshots"),
    resources: () => data<Record<string, unknown>>("/admin/monitoring/resources"),
    backgroundJobs: (limit = 50) => data<BackgroundJob[]>("/admin/monitoring/jobs", { query: { limit } }),
    maintenanceStatus: () => data<MaintenanceStatus>("/admin/maintenance/status"),
    scheduleMaintenance: (w: { start_time: string; end_time: string; description?: string }) =>
      request<unknown>("/admin/maintenance/schedule", { method: "POST", body: w }),
    providers: () => data<LlmProvider[]>("/admin/ai/providers"),
    createProvider: (p: { name: string; priority?: number; is_active?: boolean }) =>
      request<LlmProvider>("/admin/ai/providers", { method: "POST", body: p }),
    updateProvider: (name: string, update: { is_active?: boolean; priority?: number; provider_status?: string }) =>
      request<LlmProvider>(`/admin/ai/providers/${encodeURIComponent(name)}`, { method: "PUT", body: update }),
    models: () => data<ModelConfig[]>("/admin/ai/models"),
    createModel: (m: { provider_name: string; model_name: string; temperature?: number; max_tokens?: number }) =>
      request<ModelConfig>("/admin/ai/models", { method: "POST", body: m }),
    updateModel: (modelName: string, update: { temperature?: number; max_tokens?: number; is_active?: boolean }) =>
      request<ModelConfig>(`/admin/ai/models/${encodeURIComponent(modelName)}`, { method: "PUT", body: update }),
    createPromptTemplate: (t: { module: string; description?: string }) =>
      request<unknown>("/admin/ai/prompts", { method: "POST", body: t }),
    createPromptVersion: (v: { module: string; version: string; prompt_text: string }) =>
      request<PromptVersion>("/admin/ai/prompts/versions", { method: "POST", body: v }),
    promptVersions: (module: string) =>
      data<PromptVersion[]>(`/admin/ai/prompts/${encodeURIComponent(module)}/versions`),
    rollbackPrompt: (module: string, version: string, targetVersion: string) =>
      data<PromptVersion>("/admin/ai/prompts/rollback", {
        method: "POST",
        query: { module, version, target_version: targetVersion },
      }),
    testProvider: (t: { provider_name: string; model_name: string; prompt_text: string }) =>
      request<AiProviderTestResult>("/admin/ai/testing/test", { method: "POST", body: t }),
    openapi: () => request<Record<string, unknown>>("/openapi.json", { auth: false }),
  },
  openapi: () => request<Record<string, unknown>>("/openapi.json", { auth: false }),
};

// ─── WebSockets (interviews / communication) ─────────────────────────────────

/** ws(s):// URL for a live interview/communication session, authenticated via ?token=. */
export function sessionSocketUrl(kind: "interviews" | "communication", sessionId: string): string {
  const token = getStoredTokens()?.accessToken ?? "";
  const base = API_BASE_URL.replace(/^http/, "ws");
  return `${base}/${kind}/ws/${sessionId}?token=${encodeURIComponent(token)}`;
}
