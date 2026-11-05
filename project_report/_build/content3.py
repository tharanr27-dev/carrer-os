"""Chapters 7-9: database design, API and backend implementation, AI implementation and algorithms."""
import json
import os

from docmodel import bullets, chapter, code, figure, h2, h3, numbered, p, table

HERE = os.path.dirname(os.path.abspath(__file__))
EP = json.load(open(os.path.join(HERE, "data", "endpoints.json"), encoding="utf-8"))["rows"]

# ═════════════════════════ CHAPTER 7 ═════════════════════════
chapter("Database Design")
h2("Database Overview and Selection")
p("Career OS stores all persistent records in a relational database of 103 tables, 78 foreign keys and 54 named indexes, all "
  "defined as SQLAlchemy classes. PostgreSQL was chosen for production because the data is highly connected (a user owns resumes, "
  "resumes have analyses, analyses have suggestions), because transactions and constraints protect consistency, and because JSON "
  "columns hold flexible fields such as rubrics and evaluations. The database is provided by Supabase, a hosted PostgreSQL service. "
  "SQLite is used for local development and automated tests, so that tests never touch a shared database.")
h2("Table Groups and Important Tables")
p("The 103 tables fall into seven groups: identity and access (users, roles, permissions); profile and resume; training (question bank, "
  "attempts, items); interviews and communication; career, learning and mentor; recruiters and placements; and community, analytics and "
  "administration (23 admin tables and the audit log). {tab:keytables} lists the tables that carry the student journey.")
table("keytables", "Important tables, keys and columns",
      ["Table", "Primary key", "Foreign keys", "Important columns"],
      [["users", "id (UUID)", "-", "email (indexed), hashed_password, status, failed_login_attempts, locked_until"],
       ["profiles", "id", "user_id to users (unique)", "first_name, last_name, headline, role_specific_data (JSON), completion_percentage"],
       ["resumes", "id", "user_id to users", "file_name, s3_key (storage key, unique), content_type, status"],
       ["resume_analyses", "id", "resume_id to resumes", "ats_score, grammar_score, quality_score, keyword_analysis (JSON)"],
       ["training_questions", "id", "-", "round, topic, qtype, difficulty, prompt, options, correct_index, rubric (JSON), roles (JSON), source, owner_user_id"],
       ["training_attempts", "id", "user_id to users", "mode, status, config (JSON), summary (JSON), started_at, ended_at"],
       ["training_attempt_items", "id", "attempt_id; question_id", "answer (JSON), evaluation (JSON), score, score_kind, answered_at"],
       ["mentor_messages", "id", "session_id to mentor_sessions", "role (USER or AI), content, token_usage (JSON)"],
       ["recruiter_jobs", "id", "company_id to recruiter_companies", "title, description, status, requirements, pipeline_stages"],
       ["placement_drives", "id", "college_id to placement_colleges", "title, drive_type, status, date_of_drive, requirements"]],
      widths=[3.2, 1.8, 3.6, 5.4], fs=9.5)
h2("Keys, Relationships, Indexes and Integrity")
p("Every table inherits a UUID primary key and the columns created_at, updated_at and deleted_at from a common base class. The "
  "relationships follow {fig:er}: one user has many resumes, mentor sessions and training attempts, and one attempt has many items "
  "that point to a question. Unique constraints protect one-to-one links such as profiles.user_id. Indexes exist on frequently "
  "filtered columns, for example users.email, training_questions (round and topic) and training_attempt_items.user_id. Two columns, "
  "training_attempt_items.user_id and training_questions.owner_user_id, store a user identifier without a foreign key because they "
  "are denormalised for history queries; application code, not the database, enforces them. The deleted_at column is meant for soft "
  "deletion, but only some repositories filter on it, so deletion is not uniformly soft.")
h2("ORM Access and User Data Isolation")
p("Each module has a repository class containing its queries, written with SQLAlchemy `select`, `add` and `commit` on an "
  "asynchronous session, so SQL strings are never built by hand and injection is prevented. As an example, a resume upload inserts a "
  "`resumes` row with status PENDING; a background task later inserts a `resume_analyses` row and several `resume_suggestions` rows "
  "and sets the status to COMPLETED; the analysis endpoint returns the data only if `resumes.user_id` equals the signed-in user.")
p("Isolation is enforced in the service layer: a service loads the requested record and compares its owner with the authenticated "
  "user. Resumes, mentor sessions, interview sessions, training attempts and role sessions all follow this rule, and a foreign "
  "identifier produces a 403 or 404 without revealing the record. Recruiter and officer data is isolated by company or college "
  "identifier. Automated tests verify these rules.")
h2("Database Connection Flow")
p("{fig:dbflow} shows how a connection is created. The settings object reads `DATABASE_URL`, rewrites `postgresql://` to "
  "`postgresql+asyncpg://` where necessary, and the engine and session factory are created once; a new session is opened for each "
  "request by the `get_db` dependency. Safety guards prevent accidental changes to a shared database: tables are created at start-up "
  "only for SQLite, and scripts that write data refuse a non-local database unless a confirmation variable is set.")
figure("dbflow", "fig_7_1_db_flow.png", "Database connection flow and safety guards", 4.8)
h2("Local Test Database and Remote Database")
table("dbstatus", "Database environments and verification status",
      ["Environment", "Used for", "Verification status"],
      [["In-memory SQLite", "Automated tests (483 tests)", "Verified by test execution"],
       ["SQLite file in a temporary folder", "Manual runs, screenshots, live checks", "Verified by manual execution"],
       ["Supabase PostgreSQL", "Intended production database (DATABASE_URL)", "**Not verified**: deliberately not contacted"]],
      widths=[4, 6.2, 3.8], fs=10)
p("The report therefore makes no claim that data persists correctly on the remote database. PostgreSQL compatibility of the table "
  "definitions was checked only by compiling statements for the PostgreSQL dialect. The project has no migration tool; the tables "
  "introduced by the training module are provisioned by an explicit script and a SQL file that must be run with approval.")

# ═════════════════════════ CHAPTER 8 ═════════════════════════
chapter("API and Backend Implementation")
h2("FastAPI Application and Router Structure")
mods = {}
for r in EP:
    mods[r[0]] = mods.get(r[0], 0) + 1
p("The application object is created in `app/main.py`. At start-up it installs three exception handlers, four middleware components "
  "(request identifier, security headers, rate limiter, cross-origin handling) and sixteen routers, each mounted under "
  f"`/api/v1/<module>`. The route counts are: admin {mods['admin']}, training {mods['training']}, placements {mods['placements']}, "
  f"recruiters {mods['recruiters']}, community {mods['community']}, mentor {mods['mentor']}, auth {mods['auth']}, resumes {mods['resumes']}, "
  f"and 1 to 3 each for users, jobs, recommendations, interviews, communication, discovery, learning and analytics, plus "
  f"{mods['system']} health and metrics routes at the root: 124 in total. The start-up function creates tables only for SQLite "
  "databases and otherwise logs a warning, so that merely starting the server cannot change a remote database.")
h2("Request, Response and Validation")
p("Most successful responses use one envelope with the fields `success`, `message`, `data`, `errors`, `request_id` and `timestamp`; "
  "older routes in the authentication, recruiter and placement modules return the model directly, and the frontend client handles "
  "both. Request bodies are Pydantic models. For example, a mentor message must contain 1 to 4000 characters and cannot be blank, a "
  "role session must request 3 to 30 questions and a registration password must have at least eight characters. Invalid input is "
  "rejected with HTTP 422 before any service code runs, and uploaded files are validated for type, size, file signature and name.")
h2("Service Layer and Database Sessions")
p("Routers contain no business rules. They call a service, which uses repositories. The `get_db` dependency yields one asynchronous "
  "session per request, and services commit explicitly after a complete unit of work. A failed language-model call, for example, "
  "raises an error before any message is written, so no partial conversation is stored.")
h2("Authentication Dependencies and Authorization")
table("authdeps", "Authentication and authorization dependencies",
      ["Dependency", "Check performed", "Routes"],
      [["(none)", "Public", "7 (login, register, refresh, health, metrics)"],
       ["get_current_user", "Valid access token and an active user", "69"],
       ["require_permissions", "Login plus a named permission through roles", "34 administrator routes"],
       ["verify_recruiter_access", "Login plus membership of a company", "4"],
       ["verify_placement_officer_access", "Login plus membership of a college", "8"],
       ["Token in query string", "Access token validated inside the WebSocket handler", "2"]],
      widths=[4.8, 6.2, 3.0], fs=10)
h2("Error Handling")
p("A global handler turns unexpected exceptions into a generic 500 response, a second handler formats validation errors and a third "
  "handles database errors. Provider failures are mapped to fixed, user-safe messages: 504 for a timeout, 429 for a rate limit, 502 for "
  "rejected credentials or an unavailable model and 503 for an unconfigured or overloaded provider. Messages never contain the "
  "provider's text, keys or file paths.")
h2("Endpoint Inventory")
p("The inventory was extracted from the running application object, so every path, method and authentication rule is the real one. "
  "{tab:endpoints} lists the endpoints that carry the main features; the complete list of 124 routes is delivered with this report in "
  "the file API_Endpoint_Inventory.md.")
KEY = {
    ("POST", "/api/v1/auth/register"): ("Create account", "Creates an active user from e-mail and password"),
    ("POST", "/api/v1/auth/login"): ("Sign in", "Returns access and refresh tokens; login throttling applies"),
    ("POST", "/api/v1/auth/refresh"): ("Renew tokens", "Exchanges a valid refresh token for a new pair"),
    ("GET", "/api/v1/auth/me"): ("Current identity", "Roles, permissions, company or college link"),
    ("PUT", "/api/v1/users/me/profile"): ("Update profile", "Updates names, headline and role data"),
    ("POST", "/api/v1/resumes/upload"): ("Upload resume", "Validates and stores the file; analysis runs in the background (202)"),
    ("GET", "/api/v1/resumes/{resume_id}/analysis"): ("Read analysis", "Scores, skills and suggestions; owner only"),
    ("GET", "/api/v1/resumes/{resume_id}/download"): ("Download file", "Streams the stored file; owner only"),
    ("GET", "/api/v1/jobs/recommended"): ("Recommended jobs", "Fetches remote jobs and scores them against saved skills"),
    ("GET", "/api/v1/recommendations/feed"): ("Recommendation feed", "Ranked next steps from saved data"),
    ("POST", "/api/v1/mentor/sessions/{session_id}/message"): ("Ask the mentor", "Calls the LLM; saves a successful exchange"),
    ("GET", "/api/v1/mentor/status"): ("Provider status", "Says only whether an AI provider is configured"),
    ("POST", "/api/v1/training/attempts"): ("Start a practice round", "Creates an attempt with selected questions"),
    ("POST", "/api/v1/training/attempts/{attempt_id}/answer"): ("Answer a question", "Grades and saves one answer"),
    ("GET", "/api/v1/training/progress"): ("Progress", "Round and topic progress from saved answers"),
    ("GET", "/api/v1/training/roles"): ("Search roles", "Role catalogue; custom titles allowed"),
    ("POST", "/api/v1/training/roles/resolve"): ("Resolve a title", "Normalises a job title and reports coverage"),
    ("POST", "/api/v1/training/role-sessions"): ("Start role session", "Fresh questions plus a plan"),
    ("POST", "/api/v1/training/role-sessions/{session_id}/answer"): ("Submit answer", "Instant evaluation; no double scoring"),
    ("POST", "/api/v1/training/role-sessions/{session_id}/finish"): ("Finish session", "Totals from saved evaluations"),
    ("GET", "/api/v1/training/role-sessions/{session_id}/review"): ("Review", "Question-by-question review with filters"),
    ("POST", "/api/v1/training/role-sessions/{session_id}/again"): ("Practise again", "New session; mixed or weak-area focus"),
    ("WS", "/api/v1/interviews/ws/{session_id}"): ("Live interview", "Events START, ANSWER_SUBMITTED, FINISH"),
    ("POST", "/api/v1/discovery/assessments/{template_id}/submit"): ("Career questionnaire", "Stores answers; builds a report"),
    ("POST", "/api/v1/learning/roadmaps/generate"): ("Generate roadmap", "Builds a role-based roadmap (202)"),
    ("GET", "/api/v1/analytics/dashboard/student"): ("Dashboard data", "Readiness and score cards"),
    ("POST", "/api/v1/recruiters/company"): ("Create company", "Links the user as company administrator"),
    ("POST", "/api/v1/placements/colleges"): ("Create college", "Links the user as college administrator"),
    ("GET", "/health"): ("Health check", "Reports that the service is running"),
}
byk = {(r[1], r[2]): r for r in EP}
rows = []
for (m, pth), (purpose, desc) in KEY.items():
    r = byk.get((m, pth))
    assert r, (m, pth)
    auth = r[4].replace("Login + permission `", "Login + permission ").replace("`", "")
    rows.append([m, pth.replace("/api/v1", ""), purpose, auth, desc])
table("endpoints", "Key API endpoints (paths are relative to /api/v1)", ["HTTP Method", "Endpoint", "Purpose", "Authentication", "Description"], rows,
      widths=[1.5, 4.8, 2.3, 2.3, 4.8], fs=9)

# ═════════════════════════ CHAPTER 9 ═════════════════════════
chapter("AI Implementation and Algorithms")
h2("Classification of the Intelligent Features")
p("Career OS contains one language-model feature that is central to the product, an optional use of the same model inside the training "
  "module, and several algorithms that are not machine learning. {tab:aiclass} states exactly which is which. No custom model was "
  "trained, no training data set exists in the repository and no fine-tuning is performed.")
table("aiclass", "Classification of intelligent features", ["Feature", "Type", "Engine", "LLM"],
      [["AI Mentor chat", "LLM-powered (needs key)", "mentor/service.py, training/llm.py", "Yes"],
       ["Resume extraction, scoring, skill extraction", "Rule-based formulas", "resumes/, core/text_analysis.py", "No"],
       ["Job matching", "Database and set-overlap matching", "jobs/service.py, skills.py", "No"],
       ["Recommendations and roadmap", "Rule-based", "recommendations/, learning/", "No"],
       ["Multiple-choice grading", "Exact comparison", "training/scoring.py", "No"],
       ["Written-answer grading", "Rubric; LLM optional", "training/scoring.py", "Optional"],
       ["Role question generation", "LLM with validation (needs key)", "training/role_generation.py", "Optional"],
       ["Role question selection", "Weighted selection algorithm", "training/role_training.py", "No"],
       ["Interview and communication feedback", "Rule-based text metrics", "interviews/, communication/", "No"],
       ["Placement ranking, recruiter matching", "Weighted sums, overlap", "placements/, recruiters/", "No"],
       ["Administrator AI-provider test", "Simulated", "ai/providers/echo_gateway.py", "No (stub)"]],
      widths=[4.8, 3.6, 4.2, 1.4], fs=9.5)
h2("AI Mentor and Language-Model Integration")
p("The system prompt is stored in one backend file (`mentor/prompt.py`). It tells the model to act as a supportive career and "
  "learning mentor, to answer in English only, to answer the actual question first, to ask a clarifying question when needed, never to "
  "invent achievements, scores or history, to say when it is unsure and not to reveal instructions or credentials. The facts block "
  "is built from the student's own records (target role, profile completion, latest resume score and missing skills, latest "
  "interview and communication scores, open goals, active roadmap), only values that exist are included, and the block is wrapped in a "
  "`<user_facts>` tag that the prompt declares to be data, not instructions.")
p("The client sends one HTTPS request containing the system prompt, up to ten earlier messages and the new question; the provider "
  "(Groq, xAI or Anthropic) is detected from the key format. The configured Groq model is `openai/gpt-oss-120b` with low reasoning "
  "effort, a reply limit of 1500 tokens and a 25-second timeout. The model has no memory: follow-up questions work because recent messages "
  "are sent again. A successful reply is limited to 6000 characters and saved with the question; any failure becomes a typed reason "
  "(timeout, authentication, rate limit, quota, model unavailable, overload, network or unreadable output) with a safe message, and "
  "nothing is saved.")
code("""function send_message(user, session_id, text):
    session = load(session_id); require session.owner == user        # else 403
    require rate_limit(user) <= 12 per minute                         # else 429
    require llm.is_configured                                         # else 503 setup message
    facts   = ContextAggregator.build(user)                           # only this user's records
    system  = SYSTEM_PROMPT + "<user_facts>" + format(facts) + "</user_facts>"
    history = last 10 messages of session + [text]
    try:    reply = llm.chat(system, history, max_tokens = 1500)
    except ProviderError as e:  raise safe_http_error(e.reason)       # nothing saved
    save(USER text); save(AI reply[:6000]); audit(user, session)
    return reply""", "Pseudocode of the mentor request handler")
p("The mentor was verified by automated tests with a scripted provider (the dedicated mentor test file and 11 interface tests) and by "
  "one manual check on 27 October 2026 in which three questions were answered through the Groq API, including a follow-up that used "
  "the earlier message and a non-English question answered in English. The quality of the answers was not measured.")
h2("Resume Text Extraction and Analysis")
p("{fig:resume} shows the pipeline. PDF text is read page by page with pypdf (first fifteen pages) and DOCX text from the file's "
  "XML. A file with fewer than twenty readable words is flagged as unreadable, which covers scanned images because no OCR is "
  "performed. The scores use the formulas below, documented in `analysis.py`.")
figure("resume", "fig_9_1_resume_pipeline.png", "Resume analysis pipeline", 4.8)
code("""ATS readiness (0-100) = 35 * min(1, words / 150)
                      + 25 * essential_sections_found / 4      # education, experience or projects, skills, contact
                      + 20 * contact_completeness              # e-mail 10, phone 5, profile link 5
                      + 10 * has_skills_section
                      + 10 * (symbol noise below 8% of characters)
Quality (0-100)       = 40 * action_verb_ratio + 30 * min(1, quantified_lines / 5)
                      + 15 * (at least 6 skills found) + 15 * (1 - weak_phrase_penalty)
Writing mechanics     = 100 - 10 * slips   # repeated word, lowercase 'I', lowercase sentence start""",
     "Formulas used for the three resume scores")
p("Skill extraction matches a curated dictionary of skills and role keywords with word-boundary expressions; short names such as C, R "
  "and Go need a supporting context word. Skills expected for the target role but not found are reported as missing. This is keyword "
  "matching, a basic form of term matching (Salton and Buckley, 1988), not an understanding of meaning. The output carries the method "
  "label `rule_based_v1`, and the interface states that the scores are measurements, not language-model judgements and not the "
  "output of any employer's system.")
h2("Job Matching, Recommendations and Assessment Scoring")
p("Each recommended job receives a skill-match estimate: the overlap between the job's skills and the student's saved skills plus those "
  "extracted from the latest completed resume. Recommendations on the dashboard come from explicit rules over saved facts (for "
  "example, a missing resume triggers a prompt to upload one, a low interview or communication score triggers practice and an absent "
  "roadmap triggers roadmap generation); each names the fact that triggered it, and the confidence and impact values are a measurement "
  "directness and a fixed priority, not predictions.")
p("In the practice rounds, multiple-choice answers are graded by comparing the chosen index with the stored key. Written answers "
  "receive a rubric estimate (the share of expected concept groups found) or, when a provider is configured, an LLM estimate against "
  "five criteria that must pass a schema check, otherwise the rule-based estimate is used. Coding answers are self-assessed because "
  "code is never executed on the server. A round is reported as on track at 60 percent and strong at 75 percent once ten scored answers "
  "exist, and a topic is called weak only after three scored answers with an average below 60 percent.")
h2("Role-Based Question Selection and Adaptive Training")
p("The role engine accepts any job title. The title is cleaned and kept exactly as typed for display, while a normalised key is "
  "used for matching: seniority words are removed and synonyms such as developer and engineer are unified. The title is mapped, in "
  "order, to a catalogue role or alias, to a close variant, to topics inferred from keywords in the title, or to nothing. Twenty-two "
  "roles are catalogued, and eight topics (prompt engineering, LLM safety, cybersecurity, cloud, DevOps, UX design, quality assurance and "
  "product management; 48 questions) were added to the reviewed bank so that these roles work without any external service. "
  "A title that maps to no topic is still accepted but can be served only by AI generation. The activity diagram of Figure 4.10 and "
  "the pseudocode below show the selection flow.")
code("""function plan_session(user, title, level, difficulty, topics, count, focus):
    role   = resolve_role(title)                 # preserved title + normalised key + topics
    seen   = seen_questions(user)                # question -> last time seen (any earlier session)
    stats  = topic_accuracy(user, role.key)      # only this role's earlier answers
    target = difficulty or adapt(level, last 8 answers)   # avg >= 0.8 harder, avg <= 0.4 easier
    pool   = questions where topic in role.topics or tagged for this role
    if focus == 'weak': pool = pool restricted to topics with accuracy < 75%
    if unseen(pool) < needed and ai_available:   # one validated call, only for the gap
        pool += validate(llm.generate(role, target, gap))
    weight[t] = 1.5 if never practised; 1 + 3*(1 - acc) if weak; 0.5 if strong; else 1
    while len(chosen) < count:
        t = weighted_random_topic(topics that still have an unseen question first)
        chosen += best(t)  # unseen first, then longest ago; closest difficulty; varied kind
    add up to 20% neutral workplace questions   # never software-specific ones for other professions
    return session(chosen, plan_notes, notices)""", "Pseudocode of the session planner")
p("The planner explains itself: every session stores plan notes such as how many questions are new, why a topic received several "
  "questions, why the difficulty changed and which questions are repeats. Repeats are allowed only when no unseen question exists and "
  "are marked as seen before. A session is never padded with unrelated questions: when too few questions exist, the session is "
  "shorter and the student is told why, and when none exist the request is refused with a clear message.")
p("**Validation of generated questions.** Everything returned by a language model is untrusted. A generated question is accepted only "
  "if it has a known kind, type and difficulty and non-empty skill tags; it does not claim to come from a real company interview; it is "
  "not a near duplicate of an existing question (token-overlap similarity of 0.8 or more is rejected); a multiple-choice question has "
  "four distinct options, no \"all of the above\" option and an answer text that agrees with the answer index; its explanation does not "
  "point to a different option; a written question has at least two expected-concept groups so that it can be graded; and, for a "
  "mapped role, it uses vocabulary related to the role. Accepted questions are stored for that student only and labelled unreviewed. "
  "Passing these checks does not prove that an answer key is correct, and the interface says so.")
table("marks", "Marking rules of role-based training", ["Item", "Rule"],
      [["Marks per question", "Multiple-choice 1 mark; written answer 2 marks (quarter-mark steps)"],
       ["Written-answer status", "Correct at 75 percent or more of the credit, Partially Correct from 34 percent, otherwise Incorrect"],
       ["Rule-based credit", "Share of expected concepts found, multiplied by a length factor between 0.7 and 1"],
       ["LLM credit", "Mean of correctness, relevance and completeness (each 0 to 5), after schema validation"],
       ["Needs Manual Review", "No reliable marking guide: no marks, excluded from the total, model answer shown"],
       ["Unanswered", "0 marks and included in the total"],
       ["Final percentage", "Marks earned over marks available, computed on the server from saved evaluations"]],
      widths=[4.0, 10.0], fs=10)
p("A repeated submission of the same answer returns the saved result and is not scored again. The topic-wise score, strong areas "
  "(75 percent or more), weak areas (below 60 percent) and revision suggestions come from the same saved records. Practise Again "
  "reuses the previous settings, and Improve Weak Areas restricts the next session to topics where marks were lost.")
h2("Interview and Communication Evaluation, and Limits")
p("The interview studio asks questions from the reviewed bank and scores answers with the training rubric. The communication coach "
  "counts filler, hedging, informal and repeated words and mechanical slips in the typed text and turns them into scores. Both are "
  "rule-based, work on text only and do not analyse speech or tone of voice. Not implemented: training or fine-tuning of any model, "
  "resume understanding beyond keywords, optical character recognition, execution of student code and retrieval-augmented "
  "generation (the mentor receives a short fact block, not retrieved documents).")
