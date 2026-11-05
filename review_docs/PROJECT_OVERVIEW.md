# Career OS - Project Overview (evidence-based)

> Everything in this file was checked against the real repository on 2026-10-27. Where a feature is rule-based, simulated or needs a key, it says so.
> Honest one-line summary: **Career OS is a full-stack career-preparation platform whose scoring and feedback are mostly deterministic, rule-based algorithms that run locally, plus one real LLM feature (the AI Mentor) that needs an API key.**

---

## 1. What is Career OS?

Career OS is a web platform that helps students prepare for jobs in one place. A student can build a profile, upload a resume and get measurable feedback, practise aptitude / technical / HR / communication questions, run a live mock interview, get a learning roadmap and recommended next steps, see live remote IT jobs matched to their skills, and chat with an AI mentor. Recruiters and placement officers have their own portals (job posting, applications, placement drives and ranking), and an admin area manages users, roles, announcements and platform settings.

## 2. The problem it solves

Students usually prepare with scattered tools: a resume template here, a quiz site there, YouTube for interview tips, and a job portal elsewhere. Nothing tells them *where they stand* or *what to do next*.

| Student problem | What Career OS does (as implemented) |
|---|---|
| "Is my resume any good?" | Extracts the text of an uploaded PDF/DOCX and scores completeness, readability and wording with documented formulas (`rule_based_v1`), listing missing skills for the target role. |
| "What should I practise?" | Interview-prep module with 187 reviewed questions (aptitude 74, technical 64, HR 20, coding 13, communication 9, managerial 7) and per-round/topic progress built only from the student's saved answers. |
| "How do I practise talking?" | Live Interview Studio and Communication Coach over WebSockets with text-based feedback. |
| "What next?" | Recommendations and a roadmap built from the student's own saved data (profile, resume analysis, practice results). |
| "Which jobs fit me?" | Live remote IT jobs from the public Himalayas API, matched against saved/extracted skills. |
| "I have a question" | AI Mentor chat backed by a real LLM (Groq, model `openai/gpt-oss-120b`) when a key is configured. |

## 3. Target users

Students (primary), recruiters (post jobs, review applications), placement officers (colleges: create drives, check eligibility, rank students), and platform admins.

## 4. Why this project / what is different

* **Why I chose it (simple English):** "Many students, including me and my classmates, do not know how ready they are for placements. Advice is generic. I wanted one place that looks at *your own* data and tells you honestly what to improve next."
* **Main innovation (realistic):** the platform is *evidence-based and honest*. Every score is computed from the student's real inputs and labelled with how it was computed (objective, rule-based estimate, self-assessed, or LLM). It never shows invented numbers: with no data it says "not started". The cross-module context (resume + practice + interviews + goals) also feeds the AI Mentor so its answers can refer to *verified* facts.
* **Versus a chatbot:** a chatbot only answers questions. Career OS keeps structured records (attempts, reports, roadmaps), computes progress, and supports three roles.
* **Versus a job portal:** it prepares you for jobs, and also lists live jobs, but its core is readiness feedback.
* **Versus a quiz site:** quizzes are one of ~12 modules, and results drive recommendations.

## 5. Modules and honest status

Status key: **A** = implemented and covered by automated tests; **B** = partial; **C** = simulated/demo only; **D** = needs an external key/service not present. Test evidence: full backend pytest 448 passed; frontend vitest 44 passed (run 2026-10-27).

| Module | What it really does | Status |
|---|---|---|
| Auth (register/login/refresh/me) | bcrypt password hashing, JWT access (15 min) + refresh (7 days), login throttle | A |
| Profile | Profile, education, skills, projects stored per user | A |
| Resume Center | Upload (type/size checks), PDF/DOCX text extraction, rule-based ATS-readiness / quality / mechanics scores, skill extraction, download of own file | A (rule-based, not an LLM) |
| Interview Prep (training) | Question bank, practice/mock attempts, objective MCQ grading, keyword rubric for written answers, progress by round/topic | A (LLM scoring only if a key is set - then labelled `ai_estimate`) |
| Interview Studio | WebSocket interview; questions from the reviewed bank; answers scored with the same rubric | A (rule-based) |
| Communication Coach | WebSocket practice; text metrics (fillers, hedges, informal words, length) | A (rule-based, text only - no speech analysis) |
| Career Discovery | Questionnaire; matches by tallying answers against role keywords | A (rule-based) |
| Learning Roadmap | Role-based module list + progress; marks tasks complete | A (rule-based) |
| Recommendations | Rule engine over saved facts; ranked by a ranking engine | A (rule-based) |
| Jobs (recommended) | Calls the public Himalayas API; skill-overlap match score | B (needs internet; third-party data) |
| AI Mentor | LLM chat with saved history, per-user context, rate limit | A with a key (mocked tests only; one manual live check on 2026-10-27); D without a key |
| Mentor goals | Create/list career goals with milestones | A |
| Placements | Colleges, drives, eligibility, ranking by weighted scores, registrations | A (deterministic); batch readiness returns "not available" by design |
| Recruiters | Company, jobs, applications, notes, candidate matching | A (deterministic skill overlap) |
| Community | Posts, comments, reactions, search | A basic; "AI moderation" is a stub (labelled) |
| Analytics | Student dashboard, event logging, AI-usage log | B |
| Admin | Users, roles/permissions, announcements, audit logs, monitoring | B: screens read real tables (users, roles, audit logs, announcements); the admin "AI provider test" goes through an **echo stub** (`modules/ai/providers/echo_gateway.py`, fake latency/tokens) and the public `/metrics` endpoint returns fixed text |
| Email, S3, Redis, OAuth | Interfaces exist but no real provider | D |
| Password reset / OTP | Pages say "not available yet" | D (honestly labelled) |

## 6. Actual user journey (corrected to the code)

1. **Open the site.** `frontend/app/page.tsx` is the landing page; Login/Register are under `app/(auth)/`.
2. **Register.** `register/page.tsx` calls `useAuthStore.register`, which calls `api.register` -> `POST /api/v1/auth/register` (email + password, min 8 characters). The backend creates a `users` row with status `ACTIVE` immediately - **there is no email verification**. The chosen role (student / recruiter / officer) is stored client-side in the profile (`role_specific_data.selected_role`) via `PUT /users/me/profile`; the server does not grant a role at sign-up.
3. **Login.** `POST /api/v1/auth/login` -> the login throttle is checked, the bcrypt hash is verified, and an access token (15 min) and refresh token (7 days) are returned. The frontend stores them in `localStorage` and the API client attaches `Authorization: Bearer ...` to every request, refreshing once automatically on a 401.
4. **Who am I.** `GET /auth/me` returns roles/permissions/company/college. The frontend derives the dashboard role: admin if any permission starts with `admin:`, recruiter if linked to a company, officer if linked to a college, otherwise student.
5. **Student dashboard** (`app/(dashboard)/student/page.tsx`) loads the active roadmap, recommendations and open jobs through React Query.
6. **Feature use.** For example Resume Center: upload -> backend validates, stores the file locally, extracts text, computes scores in a background task, saves a `resume_analyses` row -> the page polls and shows the result.
7. **Feedback loop.** Practice results, resume analysis and reports are saved; `ContextAggregator` reads them to build recommendations, the roadmap and the Mentor's context; the student follows the suggested next steps.

## 7. Tech stack (verified from package files and imports)

### 7.1 Frontend (`frontend/`)

| Technology | Where used | Why | How it works in Career OS |
|---|---|---|---|
| Next.js 15.5 (App Router, Turbopack) | whole `frontend/app/` | File-based routing, build, dev server | Each folder with `page.tsx` is a URL; `(auth)` and `(dashboard)` are route groups with their own layouts |
| React 19 + TypeScript 5 | all components | UI components, type safety | Types in `lib/api.ts` mirror backend response shapes; `tsc --noEmit` passes |
| Tailwind CSS 4 (+ tailwind-merge, tailwindcss-animate) | all styling | Fast utility styling and dark mode | `cn()` helper in `lib/utils.ts` merges classes |
| @tanstack/react-query | 27 files (dashboard, jobs, resume, admin...) | Fetching, caching, loading/error states | `useQuery`/`useMutation` wrap `api.*` calls |
| zustand | `store/useAuthStore.ts`, `useMentorStore.ts`, `useNotificationStore.ts` | Small global state | Auth session/role, mentor chat state, notifications |
| Centralised API client | `lib/api.ts` (about 1300 lines) | One place for URL, auth header, errors, token refresh | `request()` / `data()` / `download()`; typed method per endpoint; `ApiError` carries status and message |
| react-hook-form + zod | 2 files | Form validation | Used in the auth forms |
| framer-motion, lucide-react, recharts | animation, icons, charts | UI polish; charts on analytics | recharts is used in 1 file |
| vitest + Testing Library + jsdom | `**/__tests__` | Component tests | 44 tests passing |

### 7.2 Backend (`careeros_backend/`)

| Technology | Where used | Why | How it works |
|---|---|---|---|
| Python 3.12 (Docker) / 3.14 (this machine) | everywhere | Language | - |
| FastAPI + Uvicorn | `app/main.py` | Async web framework with automatic validation and OpenAPI docs | `app.include_router(...)` registers 16 routers under `/api/v1/<module>` |
| Pydantic v2 + pydantic-settings | `schemas.py` per module, `core/config.py` | Request/response validation, typed configuration | Bad input becomes HTTP 422 before the handler runs; settings read from env/.env |
| SQLAlchemy 2 (async) | `app/db`, `models.py`, `repository.py` | ORM: Python classes <-> tables | `AsyncSession` per request via `Depends(get_db)` |
| asyncpg | `config.py`, `db/session.py` | PostgreSQL driver (Supabase) | URL is rewritten to `postgresql+asyncpg://`; statement cache disabled for PgBouncer |
| aiosqlite | tests and local dev | In-memory/local SQLite | **Not listed in `requirements.txt`** although tests/local mode need it (finding) |
| JWT (python-jose) + bcrypt | `core/security.py`, `core/dependencies.py` | Stateless login and password hashing | Password is SHA-256 pre-hashed then bcrypt (avoids the 72-byte limit); tokens HS256 signed with `SECRET_KEY` |
| RBAC | `require_permissions`, roles/permissions tables | Admin screens need named permissions | Roles -> permissions are many-to-many; checked per route |
| httpx | `training/llm.py`, `jobs/service.py` | Outbound HTTP | Calls Groq/xAI/Anthropic and the Himalayas jobs API |
| pypdf, zipfile | `resumes/text_extraction.py` | Local PDF/DOCX text extraction | No external service |
| pytest + pytest-asyncio + httpx | `tests/` | Automated tests | In-memory SQLite, fake LLM |
| ruff | lint | Style/lint | clean on the code I touched |

**Declared but not actively used (do not present as working):** `alembic` (no migration folder exists), `passlib` (security.py uses `bcrypt` directly), `prometheus-client` (not imported; `/metrics` returns fixed text), `gunicorn` (only mentioned in config), `celery`/`redis` (Celery apps and a Redis cache class exist in `admin/analytics/community/placements/recruiters/tasks.py` and `infrastructure/cache/redis.py`, but no worker or Redis is run in the verified setup; the code is dormant/stub), boto3/S3 (stub; resumes are stored on local disk). Docker/Kubernetes/Grafana files exist under `careeros_backend/docker`, `deployment/k8s` and compose files but were **not built or run** in this audit, and there is **no CI workflow** in the repository.

### 7.3 Database

* Configured by `DATABASE_URL`. In the owner's `.env` this points at a remote PostgreSQL (Supabase). **This audit never connected to it.**
* 103 tables, 78 foreign keys, 54 named indexes (extracted from the SQLAlchemy models). All primary keys are UUIDs; a shared `AuditableBase` adds `created_at`, `updated_at`, `deleted_at`.
* There are **no migrations** (no Alembic). Tables are created by `Base.metadata.create_all` (automatically only for SQLite; for other databases only when `AUTO_CREATE_TABLES=true` or via `scripts/create_supabase_schema.py` with explicit confirmation).

### 7.4 AI and data processing - see `AI_FEATURES_EXPLAINED.md`.

### 7.5 Tools

Git/GitHub (branch `feature/interview-training`), npm and pip, environment variables via `.env` (git-ignored), pytest/vitest. Docker/K8s files present but unverified.

## 8. Beginner-friendly definitions with Career OS examples

| Term | Meaning | Career OS example |
|---|---|---|
| Frontend | What runs in the browser | The Next.js Resume Center page with the upload button |
| Backend | The server logic | FastAPI code that validates the PDF and computes scores |
| API | The agreed set of URLs/messages between them | `POST /api/v1/resumes/upload` |
| Database | Permanent storage | The `resumes` and `resume_analyses` tables |
| ORM | Lets you use Python classes instead of SQL | `class Resume(AuditableBase)` maps to table `resumes` |
| Authentication | Proving who you are | Login returns a JWT |
| Authorization | What you are allowed to do | A student cannot download another student's resume (403) |
| AI model | A trained program that generates/predicts | The Groq-hosted `openai/gpt-oss-120b` used by the Mentor - **not trained by this project** |

## 9. Presentation scripts

**30-second introduction**
"Career OS is a web platform that helps students get job-ready. A student uploads a resume, practises aptitude and interview questions, joins a mock interview, and gets a roadmap and job suggestions - and every score is computed from their own data and clearly labelled. There is also an AI mentor, powered by an external language model, that answers questions. Recruiters and placement officers have their own portals."

**1-minute explanation**
"Students prepare using scattered tools and never know how ready they are. Career OS puts the journey in one place. It is built with a Next.js frontend and a FastAPI backend with a PostgreSQL database. After login, the student gets a dashboard. The Resume Center reads the uploaded PDF locally, extracts skills and scores completeness and wording with transparent formulas. Interview Prep has 187 reviewed questions and tracks progress by round and topic. The Interview Studio runs a live mock interview over WebSockets. Recommendations and the learning roadmap are generated from the student's saved results. For free-form questions there is an AI Mentor that calls a hosted language model. I was careful that nothing is faked: if data is missing the app says so."

**2-minute technical presentation**
"The frontend is Next.js 15 with TypeScript and Tailwind. All network calls go through one typed API client, `lib/api.ts`, which attaches the JWT and refreshes it once on a 401. Server data is cached with React Query; small global state such as the session lives in zustand. The backend is FastAPI with 16 routers under `/api/v1`. Each module follows router -> service -> repository -> SQLAlchemy models, with Pydantic schemas validating every request. Authentication uses bcrypt-hashed passwords and HS256 JWTs; authorization uses role-based permissions for admin routes, company and college membership for recruiters and officers, and per-user ownership checks for personal data such as resumes and mentor conversations. There are 114 routes and 103 tables.
Intelligence is split honestly. Resume analysis, interview and communication feedback, recommendations, the roadmap, career matching and placement ranking are deterministic algorithms with documented formulas, tested by 448 backend tests. Only the AI Mentor and optional answer evaluation use a large language model, through a provider-neutral client that supports Groq, xAI and Anthropic. We did not train any model; behaviour is shaped by a system prompt, a bounded conversation history and verified facts from the user's own records. Limitations: no email verification, tokens in localStorage, no database migrations yet, and the remote database persistence was not verified in this review."

**Why did you choose this project?** "I saw that students in my college prepare without feedback. I wanted something that tells you honestly where you stand and what to do next, using your own data."

**Main innovation?** "Not a bigger chatbot, but trustworthy feedback: every score is computed from the student's real data, labelled by method, and the system refuses to invent results when there is no data."

## 10. Limitations and future scope

**Current limitations (verified):** AI Mentor needs an external API key and internet; most "AI" scoring is rule-based and is an estimate, not a recruiter's judgement; resume analysis does not understand meaning (keyword and structure only; scanned PDFs are not OCR'd); code answers are self-assessed (code is never executed); jobs depend on a third-party API; no email verification or password reset; no migrations; tokens in localStorage; throttling is per-process; email/S3/Redis/OAuth are stubs; remote Supabase persistence was not tested in this audit.

**Future scope:** Alembic migrations; email verification and password reset; HttpOnly-cookie sessions; OCR for scanned resumes; sandboxed code execution; speech analysis for the communication coach; LLM-based answer evaluation with validation; shared (Redis) rate limiting; CI pipeline; streaming Mentor replies; batch/cohort data model for placement readiness.
