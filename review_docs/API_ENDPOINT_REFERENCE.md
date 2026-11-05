# Career OS - API Endpoint Reference (verified inventory)

Generated from the running FastAPI application object (`app.routes`), not from memory: every path, method, request model, response model and authentication dependency below was read from the real route definitions. Frontend callers come from `frontend/lib/api.ts` (the single API client) cross-referenced with the files that call each client method. Nothing here was produced by calling a remote server or the remote Supabase database.

## How to read this file

* **Base URL:** `http://127.0.0.1:8000`; all feature routes are under the prefix `/api/v1` (setting `API_V1_STR`). Health and metrics are at the root.
* **Envelope:** most JSON replies use `{ success, message, data, errors, request_id, timestamp }`. Some older modules (auth, a few admin/recruiter/placement routes) return the model directly.
* **Authentication column:** `Public` = no token; `Login (JWT)` = `Authorization: Bearer <access token>` required (dependency `get_current_user`); `Login + permission X` = JWT plus the named permission through role-based access control (`require_permissions`); `Login + recruiter/placement officer` = JWT plus membership of a company/college (`verify_recruiter_access` / `verify_placement_officer_access`); WebSocket routes authenticate with `?token=<access token>` inside the handler.
* **Test status column is a reference check, not a pass/fail.** It lists the automated pytest files and the manual live scripts (`e2e_live.py`, `verify_all_endpoints.py`) whose source mentions the route. The whole pytest suite was run on 2026-10-27 and **448 passed, 0 failed** (in-memory SQLite, mocked providers). The live scripts are NOT part of pytest; they were not re-run for this document. A route that is only referenced by a script has not been proven by an automated test.

## Summary

| Measure | Count |
|---|---|
| Routes in the app (HTTP + WebSocket) | 114 |
| WebSocket routes | 2 |
| Public routes | 7 |
| Login-only routes | 59 |
| Login + RBAC permission | 34 |
| Login + recruiter membership | 4 |
| Login + placement-officer membership | 8 |
| Routes referenced by at least one pytest file | 42 |
| Frontend client calls parsed from `lib/api.ts` | 109 |

### Frontend vs backend mismatches (verified)

* **Frontend calls with no backend route:** none. The only unmatched string is `GET /openapi.json`, which is FastAPI's built-in docs file (served at `/api/v1/openapi.json`, not an `APIRoute`).
* **Backend routes the frontend never calls:** `GET /api/v1/training/questions` only (the practice screens receive questions inside the attempt response instead). Everything else is called by at least one frontend file.
* **Duplicate/conflicting routes:** none found (each method+path pair is unique).
* **Public routes:** `/auth/login`, `/auth/register`, `/auth/refresh`, `/health`, `/health/live`, `/health/ready`, `/metrics`. Note `/metrics` is public and returns static text (see REVIEW_FINDINGS.md).

## Authentication

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/auth/login` | login | Public | body `UserLogin` | `Token` | useAuthStore.ts | pytest: test_api_contracts.py, test_security_hardening.py; script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/auth/register` | register | Public | body `UserCreate` | `UserResponse` | useAuthStore.ts | pytest: test_security_hardening.py; script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/auth/refresh` | Exchanges a valid refresh token for a fresh access/refresh token pair. | Public | body `RefreshRequest` | `Token` | useAuthStore.ts | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/auth/me` | Returns the authenticated identity with roles, permissions and org linkage. | Login (JWT) | - | `MeResponse` | useAuthStore.ts | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |

## Users and profiles

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| GET | `/api/v1/users/me/profile` | get my profile | Login (JWT) | - | `APIResponse[...][ProfileResponse]` | app/(dashboard)/profile/page.tsx, useAuthStore.ts | script: e2e_live.py, verify_all_endpoints.py |
| PUT | `/api/v1/users/me/profile` | update my profile | Login (JWT) | body `ProfileUpdate` | `APIResponse[...][ProfileResponse]` | app/(dashboard)/profile/page.tsx, useAuthStore.ts | script: e2e_live.py, verify_all_endpoints.py |

## Resumes

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| GET | `/api/v1/resumes` | The current user's uploaded resumes, newest first. | Login (JWT) | - | `APIResponse[...][list[ResumeSummaryResponse]]` | resume-center.tsx | pytest: test_api_contracts.py, test_auth_and_ws_contracts.py, test_real_resume_and_recs.py, test_security_hardening.py; script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/resumes/upload` | upload resume | Login (JWT) | body `UploadFile` | `APIResponse[...][ResumeUploadResponse]` | resume-center.tsx | pytest: test_api_contracts.py, test_real_resume_and_recs.py, test_security_hardening.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/resumes/{resume_id}/analysis` | get resume analysis | Login (JWT) | path: resume_id | `APIResponse[...][ResumeAnalysisResponse]` | resume-center.tsx | pytest: test_real_resume_and_recs.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/resumes/{resume_id}/download` | download resume | Login (JWT) | path: resume_id | - | resume-center.tsx | pytest: test_real_resume_and_recs.py; script: e2e_live.py, verify_all_endpoints.py |

## Jobs (live remote IT jobs)

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| GET | `/api/v1/jobs/recommended` | get recommended jobs | Login (JWT) | query: q, country, page, employment_type, seniority, worldwide, exclude_worldwide | `RecommendedJobsResponse` | recommended-jobs.tsx | pytest: test_pre_deploy_audit.py, test_recommended_jobs.py |

## Recommendations

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/recommendations/refresh` | Triggers an async recommendation generation cycle. | Login (JWT) | - | `APIResponse[...]` | app/(dashboard)/student/page.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/recommendations/feed` | Returns the user's current ranked recommendation feed. | Login (JWT) | - | `APIResponse[...][RecommendationFeedResponse]` | analytics.tsx, app/(dashboard)/student/page.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/recommendations/feedback` | Records the user's interaction with a recommendation (ACCEPTED, REJECTED, COMPLETED, etc.... | Login (JWT) | body `RecommendationFeedbackRequest` | `APIResponse[...]` | app/(dashboard)/student/page.tsx | script: e2e_live.py, verify_all_endpoints.py |

## Interviews (Interview Studio)

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/interviews/sessions` | init session | Login (JWT) | body `SessionCreateRequest` | `APIResponse[...][SessionResponse]` | interview.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/interviews/sessions/{session_id}/report` | Final report for a finished interview. 404 while it is still being generated. | Login (JWT) | path: session_id | `APIResponse[...][InterviewReportResponse]` | interview.tsx | script: e2e_live.py, verify_all_endpoints.py |
| WS | `/api/v1/interviews/ws/{session_id}` | Live session socket (token in query string) | Token in `?token=` | - | `events` | lib/useSessionSocket.ts | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py |

## Assessments and interview-preparation training

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| GET | `/api/v1/training/meta` | meta | Login (JWT) | - | - | index.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |
| GET | `/api/v1/training/profile` | get profile | Login (JWT) | - | - | resume-mock.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |
| PUT | `/api/v1/training/profile` | put profile | Login (JWT) | body `ProfileUpdate` | - | home.tsx, resume-mock.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |
| GET | `/api/v1/training/questions` | Question bank listing. Answers and explanations are never included here. | Login (JWT) | query: round, topic, difficulty, page, size | - | - | pytest: test_pre_deploy_audit.py, test_training_api.py |
| POST | `/api/v1/training/attempts` | create attempt | Login (JWT) | body `AttemptCreate` | - | index.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |
| GET | `/api/v1/training/attempts` | list attempts | Login (JWT) | query: page, size, status | - | home.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |
| GET | `/api/v1/training/attempts/{attempt_id}` | get attempt | Login (JWT) | path: attempt_id | - | runner.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |
| POST | `/api/v1/training/attempts/{attempt_id}/answer` | answer | Login (JWT) | body `AnswerRequest`; path: attempt_id | - | runner.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |
| POST | `/api/v1/training/attempts/{attempt_id}/next` | next questions | Login (JWT) | body `NextRequest`; path: attempt_id | - | runner.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |
| POST | `/api/v1/training/attempts/{attempt_id}/finish` | finish | Login (JWT) | path: attempt_id | - | runner.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |
| GET | `/api/v1/training/progress` | progress | Login (JWT) | - | - | home.tsx | pytest: test_pre_deploy_audit.py, test_training_api.py |

## Communication

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/communication/sessions` | init session | Login (JWT) | body `CommunicationSessionCreate` | `APIResponse[...][CommunicationSessionResponse]` | communication.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/communication/sessions/{session_id}/report` | Final report for a finished session. 404 while it is still being generated. | Login (JWT) | path: session_id | `APIResponse[...][CommunicationReportResponse]` | communication.tsx | script: e2e_live.py, verify_all_endpoints.py |
| WS | `/api/v1/communication/ws/{session_id}` | Live session socket (token in query string) | Token in `?token=` | - | `events` | lib/useSessionSocket.ts | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py |

## Career discovery

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| GET | `/api/v1/discovery/templates` | Assessment templates with their ordered questions, so clients can render the form. | Login (JWT) | - | `APIResponse[...][list[AssessmentTemplateResponse]]` | career-discovery.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/discovery/assessments/{template_id}/submit` | submit assessment | Login (JWT) | body `AssessmentSubmitRequest`; path: template_id | `APIResponse[...]` | career-discovery.tsx | pytest: test_real_coaching_features.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/discovery/reports/{report_id}` | get career report | Login (JWT) | path: report_id | `APIResponse[...][CareerReportResponse]` | career-discovery.tsx | pytest: test_real_coaching_features.py; script: e2e_live.py, verify_all_endpoints.py |

## Mentor

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/mentor/sessions` | create session | Login (JWT) | - | `APIResponse[...][MentorSessionResponse]` | useMentorStore.ts | pytest: test_mentor_ai.py, test_real_coaching_features.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/mentor/sessions/latest` | The user's most recent active conversation with its history (404 if none yet). | Login (JWT) | - | `APIResponse[...][MentorSessionResponse]` | useMentorStore.ts | pytest: test_mentor_ai.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/mentor/status` | Whether a real AI provider is configured (never reveals keys or provider details). | Login (JWT) | - | `APIResponse[...][MentorStatusResponse]` | useMentorStore.ts | pytest: test_mentor_ai.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/mentor/suggestions` | Next steps from the user's own saved activity; separate from chat answers. | Login (JWT) | - | `APIResponse[...][list[MentorSuggestion]]` | useMentorStore.ts | pytest: test_mentor_ai.py, test_real_coaching_features.py; script: e2e_live.py |
| GET | `/api/v1/mentor/goals` | list goals | Login (JWT) | - | `APIResponse[...][list[CareerGoalResponse]]` | career-journey.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/mentor/sessions/{session_id}/message` | send message | Login (JWT) | body `ChatMessageRequest`; path: session_id | `APIResponse[...][MentorMessageResponse]` | useMentorStore.ts | pytest: test_mentor_ai.py, test_real_coaching_features.py; script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/mentor/goals` | create goal | Login (JWT) | body `CareerGoalCreate` | `APIResponse[...][CareerGoalResponse]` | career-journey.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |

## Learning roadmap

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/learning/roadmaps/generate` | Initiates AI-powered personalised learning roadmap generation. | Login (JWT) | body `RoadmapGenerateRequest` | `APIResponse[...]` | learning.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/learning/roadmaps/active` | Fetches the user's current active learning roadmap with all modules and tasks. | Login (JWT) | - | `APIResponse[...][LearningRoadmapResponse]` | analytics.tsx, app/(dashboard)/student/page.tsx, career-journey.tsx, learning.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/learning/tasks/complete` | Marks a learning task as COMPLETED and increments the user's learning streak in Redis. | Login (JWT) | body `TaskCompleteRequest` | `APIResponse[...]` | app/(dashboard)/student/page.tsx, learning.tsx | script: e2e_live.py, verify_all_endpoints.py |

## Placements

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/placements/colleges` | create college | Login (JWT) | body `CollegeCreate` | `CollegeResponse` | officer-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/placements/drives` | create drive | Login + placement officer (college member) | body `PlacementDriveCreate` | `PlacementDriveResponse` | officer-portal.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/placements/drives` | list college drives | Login + placement officer (college member) | - | `List` | officer-portal.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/placements/drives/available` | Student-facing: upcoming/ongoing drives that are open for registration. | Login (JWT) | - | `List` | jobs.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/placements/registrations/mine` | list my registrations | Login (JWT) | - | `List` | jobs.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/placements/drives/{drive_id}` | get drive | Login + placement officer (college member) | path: drive_id | `PlacementDriveResponse` | officer-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/placements/drives/{drive_id}/calculate-eligibility` | trigger eligibility calculation | Login + placement officer (college member) | path: drive_id | - | officer-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/placements/drives/{drive_id}/register` | register for drive | Login (JWT) | path: drive_id | `DriveRegistrationResponse` | jobs.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/placements/drives/{drive_id}/registrations` | list drive registrations | Login + placement officer (college member) | path: drive_id | `List` | officer-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| PATCH | `/api/v1/placements/registrations/{registration_id}` | update registration status | Login + placement officer (college member) | body `DriveRegistrationUpdate`; path: registration_id | `DriveRegistrationResponse` | officer-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/placements/registrations/{registration_id}/offer` | release offer | Login + placement officer (college member) | body `OfferLetterCreate`; path: registration_id | `OfferLetterResponse` | officer-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/placements/drives/{drive_id}/rank` | trigger student ranking | Login + placement officer (college member) | path: drive_id | - | officer-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |

## Recruiters

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/recruiters/company` | create company | Login (JWT) | body `CompanyCreate` | `CompanyResponse` | recruiter-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/recruiters/jobs` | Creates a job posting for the recruiter's company. | Login + recruiter (company member) | body `JobCreate` | `JobResponse` | recruiter-portal.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/recruiters/jobs/open` | Candidate-facing job board: every open posting, with the hiring company's name. | Login (JWT) | - | `List` | app/(dashboard)/student/page.tsx, jobs.tsx, utility-screens.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/recruiters/applications/mine` | The current candidate's own applications with job/company context. | Login (JWT) | - | `List` | jobs.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/recruiters/jobs` | get company jobs | Login + recruiter (company member) | - | `List` | recruiter-portal.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/recruiters/jobs/{job_id}/apply` | apply for job | Login (JWT) | path: job_id | `ApplicationResponse` | jobs.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/recruiters/jobs/{job_id}/applications` | get job applications | Login + recruiter (company member) | path: job_id | `List` | recruiter-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| PATCH | `/api/v1/recruiters/applications/{application_id}` | Updates candidate status in the recruitment pipeline (e.g. 'Shortlisted'). | Login + recruiter (company member) | body `ApplicationUpdate`; path: application_id | `ApplicationResponse` | recruiter-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |

## Community

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/community/posts` | create post | Login (JWT) | body `PostCreate` | `PostResponse` | community-hub.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/community/posts/{post_id}` | get post | Login (JWT) | path: post_id | `PostResponse` | community-hub.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/community/posts/{post_id}/comments` | add comment | Login (JWT) | body `CommentCreate`; path: post_id | `CommentResponse` | community-hub.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/community/posts/{post_id}/comments` | get comments | Login (JWT) | path: post_id | `List` | community-hub.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/community/reactions` | add reaction | Login (JWT) | body `ReactionCreate` | - | community-hub.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/community/feed/trending` | get trending feed | Login (JWT) | query: limit, offset | `List` | community-hub.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/community/feed/latest` | get latest feed | Login (JWT) | query: limit, offset | `List` | community-hub.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/community/search` | search posts | Login (JWT) | query: q, limit, offset | `List` | community-hub.tsx, utility-screens.tsx | script: e2e_live.py, verify_all_endpoints.py |

## Analytics

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/analytics/events` | Log a new domain event. | Login (JWT) | body `AnalyticsEventCreate` | - | analytics.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/analytics/ai-usage` | Log AI pipeline usage (tokens, latency). | Login (JWT) | body `AIUsageAnalyticsCreate` | `AIUsageAnalyticsResponse` | admin-portal.tsx | script: verify_all_endpoints.py |
| GET | `/api/v1/analytics/dashboard/student` | Get aggregated dashboard data for the student. | Login (JWT) | - | `Dict` | analytics.tsx, app/(dashboard)/student/page.tsx, app/(dashboard)/workspace/page.tsx | script: e2e_live.py, verify_all_endpoints.py |

## Admin

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| POST | `/api/v1/admin/settings` | create setting | Login + permission `admin:write` | body `PlatformSettingCreate` | `PlatformSettingResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| PUT | `/api/v1/admin/settings/{key}` | update setting | Login + permission `admin:write` | body `PlatformSettingUpdate`; path: key | `PlatformSettingResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/settings` | get all settings | Login + permission `admin:read` | - | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/flags` | create flag | Login + permission `admin:write` | body `FeatureFlagCreate` | `FeatureFlagResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| PUT | `/api/v1/admin/flags/{flag_id}` | update flag | Login + permission `admin:write` | body `FeatureFlagUpdate`; path: flag_id | `FeatureFlagResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/flags` | get all flags | Login + permission `admin:read` | - | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/ai/providers` | create provider | Login + permission `admin:write` | body `LLMProviderCreate` | `LLMProviderResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| PUT | `/api/v1/admin/ai/providers/{name}` | update provider | Login + permission `admin:write` | body `LLMProviderUpdate`; path: name | `LLMProviderResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/ai/providers` | get providers | Login + permission `admin:read` | - | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/ai/prompts` | create prompt template | Login + permission `admin:write` | body `PromptTemplateCreate` | `PromptTemplateResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/ai/prompts/versions` | create prompt version | Login + permission `admin:write` | body `PromptVersionCreate` | `PromptVersionResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/ai/prompts/rollback` | rollback prompt | Login + permission `admin:write` | query: module, version, target_version | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/moderation/queue` | get moderation queue | Login + permission `admin:moderator` | query: status_filter | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/moderation/queue/{item_id}/decision` | decide moderation | Login + permission `admin:moderator` | body `ModerationDecisionCreate`; path: item_id | - | admin-portal.tsx | script: verify_all_endpoints.py |
| POST | `/api/v1/admin/announcements` | create announcement | Login + permission `admin:write` | body `AnnouncementCreate` | `AnnouncementResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/broadcast` | create broadcast | Login + permission `admin:write` | body `BroadcastNotificationCreate` | `BroadcastNotificationResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/health/check` | system health check | Login + permission `admin:read` | - | `SystemHealthResponse` | admin-portal.tsx | pytest: test_api_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/users` | list users | Login + permission `admin:read` | query: limit, offset | - | admin-portal.tsx | pytest: test_auth_and_ws_contracts.py; script: e2e_live.py, verify_all_endpoints.py |
| PUT | `/api/v1/admin/users/{user_id}/status` | update user status | Login + permission `admin:write` | body `Union`; query: status_str; path: user_id | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/maintenance/schedule` | schedule maintenance | Login + permission `admin:write` | body `MaintenanceWindowCreate` | `MaintenanceWindowResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/dashboard/summary` | get dashboard summary | Login + permission `admin:read` | - | `AdminDashboardSummary` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/ai/testing/test` | test ai provider | Login + permission `admin:write` | body `AIProviderTestRequest` | `AIProviderTestResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/audit/logs` | Cursor-based audit log explorer. | Login + permission `admin:read` | query: limit, offset | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/health/snapshots` | Returns the most recent system health snapshot. | Login + permission `admin:read` | - | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/monitoring/resources` | Live system resource usage: CPU, memory, disk, network. | Login + permission `admin:read` | - | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/monitoring/jobs` | Returns recent background job execution history for Celery task monitoring. | Login + permission `admin:read` | query: limit | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/roles` | Lists all platform roles with their associated permissions. | Login + permission `admin:read` | - | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/permissions` | Lists all platform-level permissions. | Login + permission `admin:read` | - | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/users/{user_id}/roles/assign` | Assign a platform role to a user. Logs the action. | Login + permission `admin:write` | body `Union`; query: role_name; path: user_id | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| POST | `/api/v1/admin/ai/models` | create model config | Login + permission `admin:write` | body `ModelConfigurationCreate` | `ModelConfigurationResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| PUT | `/api/v1/admin/ai/models/{model_name}` | update model config | Login + permission `admin:write` | body `ModelConfigurationUpdate`; path: model_name | `ModelConfigurationResponse` | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/ai/models` | get model configs | Login + permission `admin:read` | - | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/announcements/active` | get active announcements | Login (JWT) | - | - | admin-portal.tsx, top-nav.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/maintenance/status` | Returns any currently active maintenance window. | Login + permission `admin:read` | - | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |
| GET | `/api/v1/admin/ai/prompts/{module}/versions` | Lists all prompt versions for a given module. | Login + permission `admin:read` | path: module | - | admin-portal.tsx | script: e2e_live.py, verify_all_endpoints.py |

## Health and metrics

| HTTP method | Endpoint path | Purpose | Authentication | Request body/parameters | Response | Frontend caller | Test status |
|---|---|---|---|---|---|---|---|
| GET | `/health` | /health | Public |  | - | - | pytest: test_api_contracts.py, test_rbac_and_middleware.py; script: e2e_live.py, verify_all_endpoints.py |
| GET | `/health/live` | /health/live | Public |  | - | - | script: verify_all_endpoints.py |
| GET | `/health/ready` | /health/ready | Public |  | - | - | script: verify_all_endpoints.py |
| GET | `/metrics` | /metrics | Public |  | - | - | script: verify_all_endpoints.py |

## Worked examples (what really happens)

1. **Login** - `POST /api/v1/auth/login` with `{ "email": ..., "password": ... }`. The frontend `api.login()` is called by `useAuthStore.login`. The backend checks the login throttle, verifies the bcrypt hash and returns `{ access_token, refresh_token }`.
2. **Upload a resume** - `POST /api/v1/resumes/upload` (multipart `file`). Returns HTTP 202 with the resume id; analysis runs as a background task. The page then polls `GET /api/v1/resumes/{resume_id}/analysis` until it returns 200.
3. **Ask the AI Mentor** - `POST /api/v1/mentor/sessions` once, then `POST /api/v1/mentor/sessions/{session_id}/message` with `{ "content": "..." }`. Returns the assistant message, or 503 with a setup message when no AI key is configured, or 429/502/504 for provider problems.
4. **Live interview** - create `POST /api/v1/interviews/sessions`, then open the WebSocket `/api/v1/interviews/ws/{session_id}?token=...` and send `START`, `ANSWER_SUBMITTED`, `FINISH` events. The report is read afterwards from `GET /api/v1/interviews/sessions/{session_id}/report`.
5. **Recommended jobs** - `GET /api/v1/jobs/recommended?query=...&page=1`. The backend calls the public Himalayas API over the internet and scores each job against the student's saved skills.

## Method notes

* Paths, methods, request models, response models and authentication dependencies come from FastAPI's own route objects, so they cannot drift from the code.
* Request bodies are shown as the Pydantic model name. Field-level schemas are in the backend `schemas.py` of each module and in the live OpenAPI document at `/api/v1/openapi.json` while the server runs.
* Where the 'Purpose' text is only the function name, the route has no docstring.
