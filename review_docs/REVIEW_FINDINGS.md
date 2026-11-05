# Career OS - Review Findings, Verification Results and Readiness

Audit date: 2026-10-27. Branch `feature/interview-training` (HEAD `1ed510f`). No commit, push, deploy or remote-database access was made by this audit. Remote Supabase was **not** contacted. No secrets are reproduced here.

Labels: **PASSED / FAILED / BLOCKED / NOT RUN** for tests; **CONFIRMED** for findings verified in code or by running something.

---

## 1. Verification results (commands actually run)

All runs used in-memory SQLite and mocked providers (the autouse fixture `_never_use_a_real_llm` blocks real LLM calls during tests). Run from `careeros_backend/` and `frontend/`.

| Check | Command | Result | What it proves | What it does NOT prove |
|---|---|---|---|---|
| Backend full suite | `python -m pytest -q --no-cov` | **PASSED** - 448 passed, 0 failed (~109 s) | Services, repositories, API contracts, auth/RBAC, ownership, validation, rate limits, WebSocket contracts, resume/interview/communication/training/mentor logic behave as coded | Behaviour against PostgreSQL/Supabase; real LLM or Himalayas responses |
| by area | `pytest tests/<dir>` | **PASSED** - api 48, unit 103, services 5, repositories 5, websocket 4, smoke 31, training 225, ai 7, integration 5, load 1, performance 4, security 10 (sum 448) | Distribution of tests across layers | - |
| Frontend tests | `npx vitest run` | **PASSED** - 7 files, 44 tests | Components render, API calls hit the expected paths (mocked), loading/error/retry states, role sidebar, auth pages, Mentor chat | Real browser/network behaviour |
| TypeScript | `npx tsc --noEmit` | **PASSED** - exit 0 | Frontend types are consistent with `lib/api.ts` | That the types match the live backend at runtime |
| Lint | `npm run lint` | **PASSED** - 0 errors, 2 warnings (`<img>` instead of `next/image`) | Code style rules | - |
| Production build | `npm run build` | **PASSED** - compiled, 32 static pages generated | The app builds for production | Deployment |
| Ruff (backend, touched modules) | `python -m ruff check app ...` | **PASSED** on all of `app/` ("All checks passed"); **17 style findings remain in `scripts/` and test helpers** (unused imports, f-strings without placeholders, deliberate E402 import order) - none affect behaviour | - | Whole-repo lint cleanliness |
| API integration (live script) | `scripts/e2e_live.py` | **NOT RUN today.** Run earlier in the project against an isolated local SQLite backend | - | Today's state |
| Security/feature live probes | scratch probes (40 + 25 checks) | **NOT RUN today** (run earlier on isolated SQLite and passed at that time) | - | - |
| Browser (e2e) tests | `e2e/*.e2e.mjs` | **NOT RUN** | - | - |
| Remote database | any | **BLOCKED by design** (rule: never contact Supabase) | - | Remote persistence is **unverified** |
| Docker / Kubernetes | compose / manifests | **NOT RUN** | - | Deployability |
| Real LLM call | manual | A 3-message manual check through the local API succeeded on 2026-10-27 (Groq `openai/gpt-oss-120b`); not repeated in this audit and not an automated test | The key and model work | Answer quality |

Endpoint coverage evidence: of 114 routes, **42** are referenced by at least one pytest file; the remaining 72 are referenced only by the manual live scripts (`e2e_live.py`, `verify_all_endpoints.py`) or by the frontend client. See `API_ENDPOINT_REFERENCE.md` ("Test status" column). Do not claim "all endpoints have automated tests".

## 2. Confirmed findings

### 2.1 Security and correctness findings (CONFIRMED)

| # | Severity | Finding | Evidence | Status |
|---|---|---|---|---|
| S1 | Medium | **Anyone can become a recruiter admin or a college officer.** `POST /recruiters/company` and `POST /placements/colleges` require only a login; the caller is linked as the admin of the new company/college. Isolation between companies/colleges still holds (id checks), but there is no approval/verification. | `recruiters/services/company_service.py: create_company`, endpoint inventory (`Login (JWT)`) | Unresolved (design) |
| S2 | Medium | **JWTs are kept in `localStorage`**, readable by any script on the page if an XSS bug exists. | `frontend/lib/api.ts` token helpers | Unresolved (known limitation) |
| S3 | Low | `/metrics` and `/health*` are public; `/metrics` returns fixed text (not real Prometheus data). | `app/main.py` | Unresolved |
| S4 | Medium | **Stateless tokens cannot be revoked**; `refresh_tokens` table exists but is unused. Logout only clears the browser. | `core/security.py`, `auth/service.py` | Unresolved |
| S5 | Low | Login throttle and global rate limiter are **in-memory per process**; they reset on restart and are not shared across workers. | `core/login_throttle.py`, `middleware/rate_limit.py` | Unresolved |
| S6 | Medium | No email verification and no password reset (pages say so honestly); accounts are ACTIVE immediately. | `auth/service.py: register`, auth pages | Unresolved |
| S7 | Info | Old fallback admin credentials from an earlier version remain in **Git history**; they should be rotated if they were ever used. | Earlier audit | Unresolved (needs the owner) |
| S8 | Info | The Groq API key was pasted into a chat during development; regenerate it. | - | Owner action |
| S9 | Low | `soft delete` column `deleted_at` is only honoured by some repositories (mostly admin). | `grep deleted_at` | Unresolved |
| S10 | Low | Placeholder `SECRET_KEY` in the local `.env` is the public example value (fine for local development; production start-up refuses it). | `config.py` secret policy | Local only |

Verified protections (CONFIRMED by code and tests): bcrypt password hashing; JWT type/expiry checks; per-user ownership checks on resumes, mentor sessions, interview/communication sessions and training attempts; RBAC on 34 admin routes; recruiter/officer tenant isolation by company/college id; upload validation (type, 5 MB, content sniffing, safe file name); login throttling (429); explicit CORS origins; security headers; remote-database guards on scripts and no table creation at start-up for non-SQLite databases; safe, non-leaking provider errors.

### 2.2 Engineering and documentation findings (CONFIRMED)

| # | Finding | Evidence | Status |
|---|---|---|---|
| E1 | `requirements.txt` did not list **`aiosqlite`**, which local SQLite mode and the tests need | grep + imports | **FIXED** in this audit (one line added; the 448-test suite already passed with it installed) |
| E2 | `docker-compose.prod.yml` references `Dockerfile`, but only `Dockerfile.dev` exists - the production compose build would fail | file listing | Unresolved |
| E3 | **No migrations**: `alembic` is listed but there is no Alembic folder; schema is created with `create_all` / a SQL file (`deployment/training_tables.postgres.sql`) | file search | Unresolved |
| E4 | **No CI workflow** in the repository (no `.github/`) | file listing | Unresolved |
| E5 | Declared but unused/dormant packages: `passlib`, `prometheus-client`, `gunicorn`; `celery`/`redis` code exists but nothing in the verified setup runs a worker or Redis | grep | Unresolved (do not present as active) |
| E6 | Only 42 of 114 routes referenced by pytest files | endpoint inventory | Unresolved (coverage gap) |
| E7 | Admin "AI provider test" uses an **echo stub** that returns fake latency/token numbers | `modules/ai/providers/echo_gateway.py`, registered as `mock`/`test` | Unresolved (labelled in docs; consider removing from the UI) |
| E8 | Community "AI moderation", email, S3 and Redis are stubs | file docstrings | Documented |
| E9 | `/reports` simply redirects to `/analytics`; notification toggles in Settings are stored only on the device | page source | Documented |
| E10 | `verify_all_endpoints.py` creates a throwaway admin user and is intended for a local backend; do not point it at the shared database | script source | Documented |
| E11 | Training questions endpoint `GET /training/questions` is not called by the frontend | cross-check | Info |

### 2.3 Frontend-backend mismatch check

* Frontend calls without a backend route: **none** (the only unmatched string, `/openapi.json`, is FastAPI's docs file).
* Backend routes without a frontend caller: **1** (`GET /api/v1/training/questions`).
* No duplicate or conflicting routes. WebSocket events used by the frontend (`START`, `ANSWER_SUBMITTED`, `MESSAGE_SUBMITTED`, `FINISH`) match the backend handlers (contract tests exist).
* Not verified: every UI state in a real browser during this audit (previous manual browser checks covered resume upload, download, login/register, jobs and the mentor).

## 3. Honest feature status (for the review)

| Area | Status |
|---|---|
| Authentication, profile, RBAC, ownership | Implemented and tested |
| Resume Center | Implemented; **rule-based**, local extraction, tested |
| Interview Prep (187 questions), Interview Studio, Communication, Discovery, Roadmap, Recommendations | Implemented; **rule-based/deterministic**, tested |
| Jobs | Works with internet via third-party API; tested with mocks |
| AI Mentor | Implemented with a **real LLM when a key is set**; mocked tests pass; one manual live check passed; no key -> clear setup notice |
| Placements, Recruiters, Community, Analytics, Admin | Implemented (admin/analytics partly basic); several admin items are stubs |
| Email, S3, Redis, OAuth, password reset, OTP | Not implemented (stubs/labelled) |
| Remote Supabase persistence | **Not verified** |
| Deployment (Docker/K8s/CI) | Files exist; **not verified**; prod Dockerfile missing |

## 4. Readiness for tomorrow

**Ready to present:** the local demo (SQLite) of login, resume analysis, interview prep progress, recommendations and the Mentor; the architecture, API inventory and test results above.

**Be careful about:**
1. Do not say "fully AI-powered": say "one real LLM feature (Mentor) plus transparent rule-based scoring".
2. Do not say "trained our own model".
3. Do not say "all endpoints are tested": say "448 automated tests pass; 42 routes are directly covered by pytest and the rest by manual live scripts".
4. Do not claim cloud/database deployment works; say it was verified locally.
5. Rehearse the demo once (section 0 of `LIVE_DEMO_SCRIPT.md`) and have the backup ready if the internet or the Groq key fails.

**Top fixes after the review (priority order):** (1) rotate the Groq key and old admin credentials; (2) approval step for recruiter/officer creation (S1); (3) Alembic migrations (E3); (4) HttpOnly-cookie sessions and token revocation (S2/S4); (5) CI pipeline and a production Dockerfile (E4/E2); (6) email verification and password reset (S6).

## 5. Changes made by this audit

* Created `review_docs/` with 7 Markdown files and `review_docs/demo_assets/sample_resume_fictional.pdf` (fictional data).
* Added one line `aiosqlite>=0.19.0` to `careeros_backend/requirements.txt` (E1).
* No application source code was changed, nothing was committed or pushed, and `.env`/`.env.local` were not modified.
