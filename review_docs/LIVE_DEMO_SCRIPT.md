# Career OS - 5-Minute Live Demo Script and Backup Plan

Designed so that **nothing depends on the remote Supabase database or on an unverified service**. The only optional dependency is the AI Mentor (needs the configured Groq key and internet); a backup is provided.

---

## 0. Before the review (do this 15 minutes earlier)

**Start the backend on a throw-away local SQLite database** (this overrides the remote `DATABASE_URL` in `.env`, so Supabase is never touched; the Groq key in `.env` is still read for the Mentor). PowerShell, from the repository root:

```powershell
cd careeros_backend
$env:DATABASE_URL = "sqlite+aiosqlite:///$env:TEMP/careeros_demo.db"
$env:ENVIRONMENT = "development"
$env:UPLOAD_DIR = "$env:TEMP/careeros_demo_uploads"
$env:SECRET_KEY = [guid]::NewGuid().ToString() + [guid]::NewGuid().ToString()
python -m uvicorn app.main:app --port 8000
```

In a second terminal:

```powershell
cd frontend
npm run dev
```

Checklist (2 minutes):
1. Open http://127.0.0.1:8000/docs - the API docs load (backend OK).
2. Open http://localhost:3000/login - the page loads (frontend OK).
3. Register a demo student now: `demo.student@example.com` / a password of 8+ characters. Do **not** use a real email.
4. Open the floating AI Mentor once and send "hello". Outcomes: a real answer (key + internet OK) or the yellow "AI Mentor is not set up" notice (use the backup in section 3).
5. Keep `review_docs/demo_assets/sample_resume_fictional.pdf` (fictional person "Priya Raman") ready to upload.
6. Open the browser DevTools -> Network tab (for step 4 of the demo). Keep the API docs tab open.

Do **not** run `seed_dev.py`, `create_supabase_schema.py`, `verify_all_endpoints.py` or any script against the remote database during the review.

---

## 1. The 5-minute demo

| Time | Page / action | What to say |
|---|---|---|
| 0:00-0:30 | Slide or landing page `http://localhost:3000` | "Students prepare with scattered tools and never know how ready they are. Career OS gives feedback computed from their own data, and tells them honestly what to do next." |
| 0:30-1:00 | `/login` -> sign in as the demo student -> lands on `/student` (dashboard) | "Login sends my email and password to FastAPI. The server verifies a bcrypt hash and returns a short-lived JWT, which the app attaches to every request." Point at the sidebar: "Navigation depends on my role: student." |
| 1:00-2:30 | **Core workflow: Resume Center.** Go to `/resume` -> click **Upload New Resume** -> choose `sample_resume_fictional.pdf` | "The file goes to `POST /api/v1/resumes/upload`. The backend checks type and size, stores it, extracts the text locally, and scores it." |
| 2:30-3:00 | In DevTools Network: show `upload` (status 202) then `analysis` (status 200) and click the JSON | **How the request reaches the backend.** "The page calls my API client, which adds `Authorization: Bearer ...`. The response is a JSON envelope with the scores." |
| 3:00-3:30 | Back on the page: read the three scores, found/missing skills and suggestions | "These are **rule-based measurements** with documented formulas - the page labels them 'not AI judgements'. Where it is stored: tables `resumes`, `resume_analyses`, `resume_suggestions`; only the owner can read or download them (another student gets 403)." Show the data label (`rule_based_v1`). |
| 3:30-4:15 | `/interview-prep`: set a target role (e.g. Backend Developer) -> start an Aptitude practice round, answer a few questions, then finish (rehearse this once beforehand so you know the exact buttons and the number of questions offered). Back at `/student` click **Refresh** on recommendations | "MCQs are graded exactly; progress comes only from my saved answers. Recommendations are rules over my saved data and each one says which fact triggered it." |
| 4:15-4:45 | **AI feature.** Open the floating **CareerOS AI Mentor** -> ask: "Explain a Python decorator in two sentences." then "Show a tiny example." | "This is the one real LLM feature: a hosted model (Groq `openai/gpt-oss-120b`) called from the backend, so the key never reaches the browser. The second question works because the last messages are sent again as context. We did not train this model." |
| 4:45-5:00 | Closing | "Limitations: the mentor needs a key and internet, most scoring is rule-based, no email verification yet, and I verified persistence on local SQLite, not on the remote database. Future: migrations, OCR, speech analysis, cohort analytics." |

Accurate talking points about the output:
* Resume scores measure completeness and wording, not meaning; scanned PDFs are not read.
* Recommendations are rule-based, not predictions.
* Mentor answers can be wrong; they are not fact-checked.

---

## 2. Where the data lives (answer if asked mid-demo)

* Demo run: local SQLite file in your temp folder (`careeros_demo.db`) and uploaded files in `careeros_demo_uploads`.
* Normal configuration: the database named by `DATABASE_URL` (Supabase PostgreSQL in the owner's `.env`) - **not verified in this review**.
* Optional proof: while the backend runs, open `http://127.0.0.1:8000/docs`, authorise with the token, and call `GET /api/v1/resumes` to show the saved record.

## 3. Backup plans

| If this fails | Do this |
|---|---|
| **AI Mentor shows "not set up" / key missing / no internet** | Say: "This is the intended behaviour: the app refuses to fake an AI reply." Show the notice and the **Suggested next steps from your saved activity** panel (rule-based, works offline). Then spend the time on Resume Center and Interview Prep. Mention that automated tests (35 backend + 11 frontend) cover the Mentor with a mocked provider. |
| **Mentor error with a Retry button** (timeout / rate limit) | Click **Retry** once; explain that failed requests are never saved, so there is no duplicate or fake reply. |
| **Frontend does not start** | Show the backend through `http://127.0.0.1:8000/docs`: run `POST /auth/register`, `POST /auth/login`, authorise, and call `POST /resumes/upload` with the sample PDF - the same flow without the UI. |
| **Backend does not start** | Show the evidence instead: terminal outputs of `pytest` (448 passed), `vitest` (44 passed), `tsc --noEmit` and `npm run build`; then walk through `API_ENDPOINT_REFERENCE.md` and `TECHNICAL_ARCHITECTURE.md` diagrams. |
| **Resume analysis stays pending** | Wait a few seconds and refresh the page; the analysis runs in a background task. If it still fails, upload again. |
| **Jobs tab (`/jobs` -> Recommended IT Jobs)** | Only demo with internet (it calls the public Himalayas API). Skip it if the connection is poor; it is not required. |
| **Any question about the remote database** | "I deliberately did not connect to it during the review; persistence is verified on SQLite. Enabling it needs the schema script to be run with explicit approval." |

## 4. Things not to do during the review

* Do not use real personal data or real emails.
* Do not run live probe scripts against the remote database.
* Do not claim the mentor is trained by you, or that scores predict hiring results.
* Do not open `.env` on screen (it contains the database URL and the API key).
