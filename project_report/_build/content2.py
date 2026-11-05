"""Chapters 4-6: architecture and design, technology stack, module description."""
from docmodel import bullets, chapter, figure, h2, h3, numbered, p, table

# ═════════════════════════ CHAPTER 4 ═════════════════════════
chapter("System Architecture and Design")
h2("Overall System Architecture")
p("Career OS follows a three-tier client-server architecture ({fig:arch}). The client tier is a Next.js application running in "
  "the browser. The application tier is a FastAPI server that validates requests, enforces authentication and authorization, applies "
  "business rules and talks to the data tier: a relational database accessed through SQLAlchemy, local file storage for resumes and "
  "two optional external services, a language-model provider and a public remote-jobs interface. The browser never talks to the "
  "database, and the provider key is held only by the server.")
figure("arch", "fig_4_1_architecture.png", "Overall architecture of Career OS", 4.6)
h2("Frontend and Backend Architecture")
p("The frontend ({fig:frontend}) is organised in layers. Pages under the Next.js App Router are thin: the login and registration "
  "pages live in the `(auth)` group and all signed-in pages in the `(dashboard)` group. Each page imports a feature module, such as the "
  "resume centre or the AI Mentor. Feature modules use shared interface components and two kinds of state: React Query caches server "
  "data, and three Zustand stores keep the session, the mentor conversation and notifications. All network access goes through one "
  "typed client, `lib/api.ts`, which attaches the access token, refreshes it once when the server answers 401 and converts every "
  "failure into an `ApiError` with a readable message.")
figure("frontend", "fig_4_2_frontend.png", "Layers of the frontend", 4.4)
p("The backend ({fig:backend}) processes each request through middleware (request identifier, security headers, rate limiter and "
  "cross-origin handling), a router that validates the body with Pydantic and resolves authentication dependencies, a service that "
  "applies business rules and ownership checks, and a repository that runs SQLAlchemy queries through an asynchronous session. "
  "Shared components such as configuration, password hashing, login throttling, text analysis and the language-model client sit "
  "beside this pipeline.")
figure("backend", "fig_4_3_backend.png", "Layered architecture of the backend", 4.6)
h2("Client-Server Communication and API Flow")
p("The frontend and backend exchange JSON over HTTPS using REST conventions (Fielding, 2000). Live interview and communication "
  "sessions use WebSocket connections (Fette and Melnikov, 2011) that carry the access token in the query string, because browsers "
  "cannot add headers to a WebSocket handshake. {fig:apiflow} traces one ordinary request from a user action to the interface update.")
figure("apiflow", "fig_4_4_api_flow.png", "Request flow between the browser, the API and the database", 4.7)
h2("Authentication and Authorization Flow")
p("Authentication and authorization are separate steps ({fig:auth}). During login the server checks the login throttle (five "
  "failures per account and thirty per address in fifteen minutes), verifies the password hash with bcrypt (Provos and Mazières, 1999) "
  "and issues a short-lived access token and a longer-lived refresh token, both JSON Web Tokens (Jones et al., 2015). On every later "
  "request the server checks the signature, expiry and type of the token and that the user is active. Authorization then depends on the "
  "route: personal data is protected by an ownership check, administrator routes need named permissions, and recruiter and officer "
  "routes need membership of a company or a college.")
figure("auth", "fig_4_5_auth_flow.png", "Authentication and authorization flow", 5.0)
h2("AI Processing Flow")
p("{fig:mentorflow} shows how a message to the AI Mentor is processed. The server verifies the user and the ownership of the "
  "conversation, applies a limit of twelve messages per minute and refuses to continue when no provider key is configured, so that it "
  "never produces a pretend answer. Otherwise a context aggregator reads the student's own saved records, the last ten messages are added "
  "as history and one request is sent to the provider. Only a successful reply is saved; every failure is converted to a safe message.")
figure("mentorflow", "fig_4_6_mentor_flow.png", "Processing flow of an AI Mentor message", 5.0)
h2("Data Flow Diagrams")
p("The context diagram ({fig:dfd0}) treats the platform as one process: the four user groups send data in and receive scores, "
  "feedback, reports and rankings, while the language-model provider and the jobs interface are external systems that the platform "
  "queries. {fig:dfd1} expands the system into seven processes and seven data stores; each process reads and writes only its own tables.")
figure("dfd0", "fig_4_7_dfd0.png", "Data flow diagram, level 0 (context diagram)", 4.5)
figure("dfd1", "fig_4_8_dfd1.png", "Data flow diagram, level 1", 4.9)
h2("Use Case and Activity Diagrams")
p("{fig:usecase} lists the main use cases of each actor; the student has the largest set because the platform is centred on "
  "preparation. The activity diagram ({fig:activity}) follows one role-based training session from the choice of a job role to the "
  "final review. Its branches show the honest handling of limited question banks: unseen stored questions are used first, a validated "
  "AI call fills only the gap, and repeats are marked when no alternative exists.")
figure("usecase", "fig_4_9_usecases.png", "Use case diagram of Career OS", 4.9)
figure("activity", "fig_4_10_activity.png", "Activity diagram of a role-based training session", 5.2, tall=True)
h2("Sequence and Entity Relationship Diagrams")
p("{fig:seq} shows how one submitted answer is evaluated. The service loads the session of the signed-in student only, grades a "
  "multiple-choice answer by exact comparison or scores a written answer against the expected concepts. If a provider key is "
  "configured, a language model may grade the answer; its JSON output is validated and replaced by the rule-based result if invalid. "
  "The database holds 103 tables; {fig:er} shows the entities central to the student journey, and Chapter 7 explains the design.")
figure("seq", "fig_4_11_answer_sequence.png", "Sequence diagram of answer evaluation", 4.7)
figure("er", "fig_4_12_er.png", "Entity relationship diagram of the core tables", 5.4, tall=True)

# ═════════════════════════ CHAPTER 5 ═════════════════════════
chapter("Technology Stack")
p("Technologies were selected for strong documentation, support for asynchronous input and output, and a type system that catches "
  "interface mismatches early. Only technologies that the project imports or executes are described as used; packages that are "
  "declared but dormant are listed at the end of this chapter.")
h2("Frontend Technologies")
table("stack_fe", "Frontend technologies and their roles",
      ["Technology", "What it is", "Why selected", "Where used in Career OS"],
      [["Next.js 15.5 and React 19.1", "React framework with file-based routing; UI library", "Routing, layouts, production build; reusable components", "All pages in app/(auth) and app/(dashboard)"],
       ["TypeScript 5", "JavaScript with static types", "Compile-time checks of API shapes", "All source files; type check passes with zero errors"],
       ["Tailwind CSS 4", "Utility-first styling", "Fast, consistent styling with dark mode", "All components"],
       ["React Query 5", "Server-state library", "Caching, loading and error states", "More than 25 files (dashboard, resume, jobs, role training)"],
       ["Zustand 5", "Small client-state store", "Global state without boilerplate", "Authentication, mentor chat, notifications"],
       ["react-hook-form, zod", "Form handling and validation", "Typed form validation", "Login and registration forms"],
       ["Vitest, Testing Library", "Test runner and component testing", "Fast tests in a simulated browser", "54 frontend tests"]],
      widths=[3.0, 3.4, 3.8, 3.8], fs=10)
h2("Backend Technologies")
table("stack_be", "Backend technologies and their roles",
      ["Technology", "What it is", "Why selected", "Where used in Career OS"],
      [["Python", "General-purpose language", "Rich libraries for text and data work", "All backend code (about 18,400 lines)"],
       ["FastAPI and Uvicorn", "Asynchronous web framework and server", "Automatic validation, OpenAPI docs, WebSockets", "app/main.py and 16 routers"],
       ["Pydantic 2", "Data validation and typed settings", "Rejects bad input before handlers run", "Schemas of every module; core/config.py"],
       ["SQLAlchemy 2 (async)", "Object-relational mapper", "Portable queries for PostgreSQL and SQLite", "models.py and repository.py of each module"],
       ["asyncpg, aiosqlite", "Database drivers", "Asynchronous access to PostgreSQL and SQLite", "Production and local or test databases"],
       ["python-jose, bcrypt", "JWT library; password hashing", "Stateless sessions; slow salted hashes", "core/security.py"],
       ["httpx, pypdf", "Async HTTP client; PDF text reader", "Provider and jobs calls; offline resume parsing", "training/llm.py, jobs/service.py, resumes/text_extraction.py"],
       ["pytest, pytest-asyncio, ruff", "Test framework and linter", "Asynchronous tests; consistent style", "483 backend tests"]],
      widths=[3.0, 3.4, 3.8, 3.8], fs=10)
h2("Database, AI and Data Processing Technologies")
p("PostgreSQL, provided by Supabase, is the intended production database. The application reads the connection string from the "
  "`DATABASE_URL` environment variable, rewrites it for the asyncpg driver and disables the prepared-statement cache so that it works "
  "behind a connection pooler. For development and tests the same models run on SQLite. Tables are defined with SQLAlchemy models; "
  "there is no migration tool (see Chapter 12).")
bullets([
    "**Language-model access:** a provider-neutral client sends chat-completion requests over HTTPS to Groq (model `openai/gpt-oss-120b`), xAI or Anthropic; the key is read only from the server environment.",
    "**Text processing:** pypdf and a zip-and-XML reader extract PDF and DOCX text locally; a shared module matches a skills dictionary and counts verbs, sections, contact details and slips.",
    "**External job data:** the public Himalayas remote-jobs interface supplies live listings that are scored against the student's skills.",
])
h2("Tools, Deployment and Dormant Technologies")
p("Source code is managed with Git and hosted on GitHub; packages are installed with npm and pip; configuration is read from "
  "environment variables and the real `.env` file is excluded from version control. Dockerfiles, compose files and Kubernetes "
  "manifests exist, but they were not built or run during this work, and no continuous-integration workflow is configured. "
  "{tab:unused} lists packages that are declared but are not part of the verified system.")
table("unused", "Declared but unused or dormant technologies",
      ["Technology", "Status in the repository"],
      [["Alembic", "Listed in requirements; no migration directory exists"],
       ["passlib, prometheus-client, gunicorn", "Listed; not used (bcrypt is called directly; /metrics returns fixed text)"],
       ["Celery and Redis", "Task and cache code exists but no worker or Redis server was run; dormant"],
       ["S3 storage, e-mail, OAuth", "Interfaces or stubs only; resumes are stored on local disk"]],
      widths=[5, 9], fs=10.5)

# ═════════════════════════ CHAPTER 6 ═════════════════════════
chapter("Module Description")
p("Each module is described by its purpose, input, processing, output, frontend and backend implementation, database interaction "
  "and current limitations. File names refer to the project repository.")


def module(key, title, purpose, inp, proc, out, fe, be, db, lim):
    h2(title)
    table(key, f"Module description: {title}",
          ["Aspect", "Description"],
          [["Purpose", purpose], ["Input", inp], ["Processing", proc], ["Output", out], ["Frontend", fe], ["Backend", be],
           ["Database", db], ["Limitations", lim]],
          widths=[2.2, 11.8], fs=10)


module("m_auth", "User Authentication",
       "Create accounts and control who can use which feature.",
       "E-mail and password (at least eight characters for new accounts); refresh token.",
       "Throttle check, bcrypt verification, token issue and refresh, identity and permission lookup.",
       "Access and refresh tokens; the current user with roles, permissions and company or college link.",
       "(auth) pages, store/useAuthStore.ts, lib/api.ts token handling.",
       "auth/router.py, service.py, core/security.py, dependencies.py, login_throttle.py.",
       "users, roles, permissions, user_roles, role_permissions.",
       "No e-mail verification or password reset; tokens in browser storage cannot be revoked; the throttle is in memory per process.")
module("m_dash", "Student Dashboard and Profile",
       "Show readiness at a glance and keep the student's profile.",
       "Profile fields and saved results from other modules.",
       "Aggregates the latest resume score, interview score and roadmap progress; readiness is the mean of the components that have data.",
       "Readiness ring, score cards, quick actions and tasks.",
       "app/(dashboard)/student and profile pages (React Query).",
       "users and analytics routers; ContextAggregator.",
       "profiles, educations, projects, profile_skills, analytics_events.",
       "Readiness is a transparent average, not a prediction; some analytics screens are basic.")
module("m_resume", "Resume Management and Analysis",
       "Tell the student how complete, readable and well worded the resume is.",
       "A PDF or DOCX file of at most 5 MB and the target role.",
       "Validate type, size and file signature; store; extract text; compute the scores of Section 9.3 in a background task.",
       "ATS readiness, quality and writing scores, found and missing skills, suggestions; the stored file on request.",
       "features/student/resume-center.tsx.",
       "resumes/upload_validation.py, text_extraction.py, analysis.py, service.py.",
       "resumes, resume_analyses, resume_suggestions; file in local storage.",
       "Rule-based, not an LLM judgement; scanned PDFs are flagged, not read; scores do not match any employer system.")
module("m_jobs", "Job Recommendations",
       "Show current remote IT jobs matched to the student's skills.",
       "Keyword, role, experience and location filters.",
       "Calls the public Himalayas interface, cleans descriptions and scores skill overlap with saved and extracted skills.",
       "Paged job cards with a skill-match estimate and a link to the listing.",
       "features/student/recommended-jobs.tsx.",
       "jobs/service.py, skills.py, router.py.",
       "Reads profile skills; listings are not stored.",
       "Needs internet; remote roles only; data belongs to a third party.")
module("m_prep", "Interview Preparation, Aptitude and Technical Assessments",
       "Practise by round and topic with immediate scoring and progress tracking.",
       "Round, topic, difficulty, number of questions, mode (practice, exam, mock).",
       "Selects questions with a seen map and topic weights; grades multiple-choice answers exactly; scores written answers with a rubric or optional LLM; computes progress from saved answers.",
       "Question sets, feedback, summaries and a roadmap of next steps.",
       "features/student/interview-prep (home, round practice, runner, mock).",
       "training/service.py, scoring.py, progress.py, bank/ (235 questions).",
       "training_questions, training_attempts, training_attempt_items, training_profiles.",
       "Coding answers are self-assessed because code is never executed; written scores are estimates.")
module("m_role", "Role-Based Training",
       "Let a student prepare for any job title with fresh questions, instant marks and a full review.",
       "A chosen or typed job title, level, difficulty, topics, question count and focus.",
       "Normalises the title, maps it to topics, selects unseen questions, optionally generates validated questions, evaluates each answer and computes totals from saved evaluations.",
       "A session with a plan, per-answer status and marks, and a final review with a practise-again option.",
       "interview-prep/role-training.tsx.",
       "training/roles.py, role_training.py, role_generation.py; nine routes.",
       "training_attempts (mode role), training_attempt_items, training_questions.",
       "Reviewed questions exist for 22 catalogued roles; other titles need an LLM key; generated answer keys are validated, not guaranteed correct.")
module("m_mentor", "AI Mentor",
       "Answer free-form career and learning questions in English.",
       "A message of 1 to 4000 characters.",
       "Checks ownership and rate limit, reads verified facts, builds the system prompt and history, calls the provider and saves a successful reply.",
       "An answer plus separate rule-based suggested next steps.",
       "features/mentor, features/student/mentor.tsx, store/useMentorStore.ts.",
       "mentor/service.py, prompt.py, router.py; training/llm.py.",
       "mentor_sessions, mentor_messages.",
       "Needs a provider key and internet; answers can be wrong; replies are shown as plain text.")
module("m_comm", "Communication Practice and Interview Studio",
       "Practise written communication and live mock interviews.",
       "Typed messages or answers sent over a WebSocket.",
       "Counts filler, hedging and informal words and slips; scores interview answers with the training rubric.",
       "Live feedback and a report.",
       "student/communication.tsx, interview.tsx, lib/useSessionSocket.ts.",
       "communication and interviews modules (WebSocket routes).",
       "communication_* and interview_* tables.",
       "Text only; no speech or video analysis.")
module("m_disc", "Career Discovery, Roadmap and Recommendations",
       "Suggest suitable careers, a learning path and the next actions.",
       "Questionnaire answers, target role and saved results.",
       "Tallies answers against role keywords; builds role-based roadmap modules; applies explicit rules to the student's records.",
       "Career matches, a roadmap with tasks and ranked recommendations that name their trigger.",
       "career-discovery.tsx, learning.tsx, dashboard.",
       "career_discovery, learning, recommendations modules.",
       "career_reports, career_matches, learning_roadmaps, recommendations.",
       "Rule-based; confidence and impact are fixed priorities, not predictions.")
module("m_place", "Placement, Recruiter and Admin Management",
       "Support recruiters, placement officers and administrators.",
       "Company, college, job, drive and user data.",
       "Recruiters manage jobs of their own company; officers manage drives of their own college and rank students with weighted scores; administrators manage users, roles and announcements.",
       "Job and application lists, eligibility and ranking results, audit logs.",
       "features/recruiter, officer and admin.",
       "recruiters, placements and admin modules (8, 12 and 35 routes).",
       "recruiter_*, placement_* and admin_* tables.",
       "Any registered user can create a company or college and become its administrator; the administrator AI-provider test is a simulated echo gateway.")
h2("Feature Status Summary")
table("status", "Classification of the implemented features",
      ["Feature", "Classification"],
      [["Authentication, profile, access control", "Fully implemented and verified by tests"],
       ["Resume analysis; recommendations, roadmap, career discovery", "Rule-based; verified by tests"],
       ["Interview preparation and role-based training", "Rule-based with optional LLM generation and grading; verified by tests (LLM mocked)"],
       ["AI Mentor", "LLM-powered when a key is configured; mocked tests plus one manual live check"],
       ["Interview Studio and Communication Coach", "Rule-based, text only; verified by tests"],
       ["Recommended jobs", "Partially implemented: depends on a third-party service"],
       ["Placements, recruiters, community, analytics", "Implemented; some screens basic"],
       ["Administrator AI-provider test, community AI moderation", "Demo or simulated"],
       ["E-mail, S3 storage, Redis, OAuth, password reset", "Planned or not implemented"],
       ["Persistence on the remote Supabase database", "Not verified"]],
      widths=[6.4, 7.6], fs=10)
