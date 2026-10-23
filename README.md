# CareerOS AI

Next.js 15 frontend (`frontend/`) + FastAPI backend (`careeros_backend/`).
Every screen talks to the real API: `UI → lib/api.ts → /api/v1/... → service → database → response → UI`.

## Run locally

```bash
# 1. Backend (SQLite by default in development, see careeros_backend/.env)
cd careeros_backend
pip install -r requirements.txt
# set SEED_ADMIN_PASSWORD first (see below); seeding only runs against SQLite unless ALLOW_REMOTE_DB_SCRIPTS=yes
python -m scripts.seed_dev          # RBAC roles, admin user, one career assessment (idempotent)
python -m uvicorn app.main:app --port 8000

# 2. Frontend
cd frontend
cp .env.example .env.local          # NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
npm install
npm run dev                         # http://localhost:3000
```

Seeding requires an admin password you choose: set `SEED_ADMIN_PASSWORD` (12+ characters) and optionally
`SEED_ADMIN_EMAIL` (default `admin@careeros.ai`) in your shell first; there is no default password. Everyone else registers through the UI.

### Roles
The backend decides the role, the UI never lets you pick one at sign-in:

| Role | How a user gets it |
|------|--------------------|
| Admin | RBAC permission `admin:*` (seed script, or `POST /admin/users/{id}/roles/assign`) |
| Recruiter | Creates a company (`POST /recruiters/company`) - the recruiter portal shows this setup step first |
| Placement officer | Registers a college (`POST /placements/colleges`) - the officer portal shows this setup step first |
| Student | Default |

`GET /auth/me` returns roles, permissions, `company_id` and `college_id`; the frontend derives the portal from it.

### Environment
| Variable | Where | Purpose |
|----------|-------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | frontend | API base URL including `/api/v1` |
| `BACKEND_CORS_ORIGINS` | backend | Comma-separated allowed origins (`*` falls back to local dev origins) |
| `RATE_LIMIT_PER_MINUTE` | backend | Per-IP request limit (default 100) |
| `DATABASE_URL` | backend | SQLAlchemy URL; SQLite in dev, PostgreSQL in production |

## Tests

```bash
# Backend unit/contract tests (no external services needed)
cd careeros_backend && python -m pytest

# Live API contract test: exercises every endpoint the frontend calls, all four roles,
# positive + negative paths, WebSockets included. Run against a freshly seeded backend:
export SEED_ADMIN_PASSWORD="<choose-12+-chars>" E2E_ADMIN_EMAIL=admin@careeros.ai E2E_ADMIN_PASSWORD="$SEED_ADMIN_PASSWORD"
DATABASE_URL=sqlite+aiosqlite:///./careeros_e2e.db RATE_LIMIT_PER_MINUTE=100000 python -m scripts.seed_dev
DATABASE_URL=sqlite+aiosqlite:///./careeros_e2e.db RATE_LIMIT_PER_MINUTE=100000 python -m uvicorn app.main:app --port 8000
python -m scripts.e2e_live

# Frontend
cd frontend && npx tsc --noEmit && npm run lint && npm run build

# Real-browser end-to-end (needs backend on :8000 and `npm run build && npm start` on :3000)
cd e2e && npm install
npm run student && npm run roles    # set BROWSER_PATH to a Chrome/Edge executable if not on the default path
```

## Known limits
- **AI output is placeholder.** The AI gateway is an echo/mock provider, so mentor replies, resume/interview/communication
  scores, roadmaps and recommendations are canned. The wiring is real; configure a real provider to get real content.
- **Redis/Celery are optional in development.** Redis is an in-memory stub and Celery tasks are enqueued best-effort
  (never blocking a request). Without a worker, eligibility calculation and ranking are accepted but not executed.
- **No password reset / email verification / OTP endpoints yet.** Those screens say so instead of pretending.
- Settings that have no backend (notification/privacy/language preferences, password change, device sessions) are shown disabled.
- Candidate/student names are not exposed by the API, so recruiter and officer lists show short IDs.
