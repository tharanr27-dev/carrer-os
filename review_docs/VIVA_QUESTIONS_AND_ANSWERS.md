# Career OS - Review / Viva Questions and Answers

Short, natural answers, consistent with the repository as checked on 2026-10-27. Where something is **not verified**, the answer says so - say the same in the review rather than guessing.

---

## A. Project and use-case questions (10)

**1. What is Career OS in one sentence?**
A web platform where a student prepares for jobs in one place: resume feedback, interview and aptitude practice, a mock interview, a roadmap, job suggestions and an AI mentor.

**2. What problem does it solve?**
Students prepare with scattered tools and do not know how ready they are or what to do next. Career OS gives feedback based on their own data and suggests the next step.

**3. Who are the users?**
Students mainly. Recruiters post jobs and review applications; placement officers run campus drives and rank students; admins manage users, roles and announcements.

**4. Why did you choose this project?**
Because placement preparation in colleges is mostly generic advice. I wanted a system that looks at a student's real results and tells them honestly what to improve.

**5. What is different from a normal chatbot?**
A chatbot only talks. Career OS stores structured records (attempts, reports, roadmaps), computes progress, supports three roles, and the mentor can use the student's verified records in its answers.

**6. What is different from a job portal or a quiz website?**
A job portal lists jobs; a quiz site gives questions. Career OS connects both to preparation: practice results and resume gaps drive recommendations, and jobs are matched to the student's skills.

**7. What are the main modules?**
Auth/profile, Resume Center, Interview Prep (187 questions), Interview Studio, Communication Coach, Career Discovery, Roadmap, Recommendations, Jobs, AI Mentor, Placements, Recruiters, Community, Analytics, Admin.

**8. What is the main innovation?**
Honesty and traceability: every score is computed from real input and labelled by method (objective, rule-based estimate, self-assessed, or LLM). With no data the app says "not started" instead of inventing a number.

**9. What are the current limitations?**
The Mentor needs an external API key and internet; most "AI" is rule-based; the resume analyser reads keywords and structure, not meaning, and cannot read scanned PDFs; code answers are self-assessed; no email verification or password reset; no database migrations; email/S3/Redis/OAuth are stubs; I did not test the remote database in this review.

**10. What is the future scope?**
Alembic migrations, email verification and password reset, HttpOnly-cookie sessions, OCR, sandboxed code execution, speech analysis, streaming mentor answers, shared Redis rate limiting, CI/CD, and a cohort/batch data model for placement analytics.

## B. Frontend, backend and API questions (10)

**11. Why Next.js instead of plain HTML/CSS/JavaScript?**
We have about 30 pages with login, roles, shared layouts and lots of data. Next.js gives file-based routing, layouts, TypeScript, a build/optimisation pipeline and a React component model so screens are reusable and testable. Plain HTML would mean repeating navigation, state and API code on every page.

**12. Why FastAPI instead of Flask or Django?**
FastAPI is async (good for waiting on the database, the LLM and external APIs), validates requests with Pydantic automatically, supports WebSockets, and generates OpenAPI docs. Flask has none of this built in; Django is heavier and its ORM is not async-first. This was my choice for speed and typed validation; I have not benchmarked them.

**13. What is the difference between a REST API and a database query?**
The REST API is the public contract between the browser and server (URL + method + JSON). A database query is the private operation the server runs to read or write data. The browser never talks to the database; the API handler decides what query to run and what the user is allowed to see.

**14. How does the frontend communicate with the backend?**
Through one typed client, `frontend/lib/api.ts`. It builds the URL from `NEXT_PUBLIC_API_BASE_URL`, attaches the JWT, parses the JSON envelope and raises an `ApiError` on failure. Live interview and communication use WebSockets with the token in the query string.

**15. What happens after a student clicks Login?**
The login page validates the form, calls `POST /auth/login`. The backend checks the login throttle, finds the user, verifies the bcrypt hash, and returns an access token (15 min) and a refresh token (7 days). The frontend stores them, calls `GET /auth/me` and the profile endpoint to learn the role, and redirects to the dashboard for that role.

**16. How does JWT authentication work?**
A JWT is a signed token containing the user id (`sub`), an expiry and a type. The server signs it with a secret key (HS256). On every request the server verifies the signature, expiry and that the type is "access", then loads the user and checks they are active. No session is stored on the server, which makes scaling easy, but a token cannot be revoked before it expires.

**17. What is the request lifecycle in the backend?**
Middleware (request id, rate limit, security headers, CORS) -> router -> Pydantic validation -> auth dependency -> service (rules, ownership) -> repository (SQLAlchemy async) -> database -> response envelope. Errors are turned into consistent JSON by exception handlers.

**18. What is the difference between a Pydantic schema and a SQLAlchemy model?**
A schema describes the data crossing the API and validates it. A model describes a database table. Keeping them separate means we never accidentally return a password hash and we can change the database without breaking the API.

**19. How many endpoints are there and how do you know they are connected?**
114 routes (including 2 WebSockets) under `/api/v1`. I extracted them from the running app and compared them with the 109 calls in `lib/api.ts`: every frontend call has a backend route, and only `GET /training/questions` is unused by the frontend. The full table is in `API_ENDPOINT_REFERENCE.md`.

**20. How do you test endpoint correctness?**
448 backend pytest tests run against in-memory SQLite with a fake LLM; they cover auth, RBAC, ownership, validation, rate limits, services and WebSockets. 42 of the 114 routes are referenced directly by a pytest file; the rest were exercised by the live scripts `e2e_live.py` and `verify_all_endpoints.py`, which are manual and were not re-run for this review. So I can say all are implemented, but only some are covered by automated tests.

## C. Database and security questions (8)

**21. Why PostgreSQL?**
Relational data with many links (users -> resumes -> analyses, drives -> registrations), transactions, constraints and JSON columns. Supabase gives hosted PostgreSQL. For local development and tests the same models run on SQLite.

**22. How do you prevent a student from accessing another student's resume?**
Every resume route loads the resume and compares `resume.user_id` with the authenticated user's id; if different the API returns 403. The same ownership check exists for mentor sessions, interview sessions and attempts. The files are not served as static files; downloads go through the authenticated endpoint. Tests verify the 403.

**23. How are passwords stored?**
Never in plain text. The password is SHA-256 pre-hashed (to avoid bcrypt's 72-byte limit) and then hashed with bcrypt with a random salt. Old raw-bcrypt hashes are still accepted so existing users are not locked out. New passwords must be at least 8 characters.

**24. Authentication vs authorization?**
Authentication = proving who you are (login/JWT). Authorization = what you may do (admin permissions through roles; recruiters only see their own company's jobs; officers only their college's drives; students only their own data).

**25. How is role-based access control implemented?**
Tables `roles`, `permissions`, `user_roles`, `role_permissions`. Admin routes use `require_permissions([...])` (34 routes). Recruiter and officer routes use `verify_recruiter_access` / `verify_placement_officer_access`, which require membership of a company/college and then compare ids. A weakness to mention honestly: any registered user can create a company or college and become its admin, because there is no approval step.

**26. What security protections exist?**
Input validation (Pydantic), upload validation (type, size, content sniffing, filename cleaning), login throttling (5 failures per account / 30 per IP per 15 min), global rate limit (100/min/IP), security headers, explicit CORS origins, fail-closed secret-key policy in production, remote-database guards on scripts, errors that never expose stack traces or keys.

**27. What are the risks of storing tokens in localStorage?**
Any JavaScript running on the page (an XSS bug) can read them. HttpOnly cookies are safer. It is a known limitation of the current design, listed as future work.

**28. Which data is real database data and which is not?**
All feature records go to the configured database. In this review everything was verified on in-memory/local SQLite. I did not connect to the remote Supabase database, so I cannot claim remote persistence is verified. There are no migrations; tables are created by `create_all` (automatically only for SQLite).

## D. AI and algorithm questions (8)

**29. Is the AI Mentor a real LLM or a rule-based chatbot?**
A real LLM when a key is configured: it calls a hosted model (Groq `openai/gpt-oss-120b`). Without a key it does not pretend: it shows a setup message. The "suggested next steps" next to it are rule-based.

**30. Did you train your own AI model?**
No. There is no training code or dataset in the project. I use a pretrained model and customise it with a system prompt, the user's verified data and recent conversation history.

**31. What happens if the AI API is unavailable?**
The backend maps the failure to a safe message (timeout 504, rate limit 429, bad key or model 502, overload/quota 503). Nothing is saved, the UI shows the error with a Retry button, and the rest of the app keeps working because it does not depend on the LLM.

**32. How are resume skills extracted?**
The text is extracted with pypdf (or DOCX XML) and matched against a curated skill dictionary with word-boundary regex; skills expected for the target role but not found are listed as missing. It is keyword matching, not understanding.

**33. How do you calculate the job readiness score?**
Honest answer: there is no single "job readiness" number for students. They see per-area results: resume ATS readiness (formula in `analysis.py`), practice accuracy by round/topic, and a status per round (on track at 60%, strong at 75%, after at least 10 scored answers). Placement officers see a weighted rank (CGPA 25%, ATS 20%, interview 15%, communication 10%, learning 10%, and 5% each for certifications, projects, hackathons, recommendations).

**34. How does interview answer evaluation work?**
MCQs are graded exactly. Written answers get a keyword/rubric estimate (coverage of expected points, structure, STAR markers), labelled as an estimate. If an LLM key is configured, an LLM rubric can be used and is validated against a schema, otherwise the rubric is used. Code answers are self-assessed because code is not executed.

**35. How do recommendations work?**
A rule engine checks facts such as profile completeness, resume gaps, low interview or communication scores and whether a roadmap exists. Each recommendation says which fact triggered it. The numbers `confidence` and `impact` describe how directly the fact was measured and a fixed priority, not a prediction.

**36. How do you handle hallucinations?**
Only verified facts are placed in the prompt; the system prompt says not to invent data and to admit uncertainty; the model has no tools or web access; we cap length; the UI warns that answers can be wrong. There is no automatic fact-checking, so critical facts must still be verified by the student.

**37. What does the AI Mentor remember?**
The model itself remembers nothing. Each message is saved in the database, and the last 10 messages are sent again with the new question, which gives follow-up ability (for example "show a tiny example of that").

## E. Testing, limitations and scaling (4+)

**38. What tests did you run?**
Backend pytest: 448 passed. Frontend vitest: 44 passed. `tsc --noEmit` clean. ESLint: 0 errors, 2 warnings. `next build` succeeded. All on local/in-memory data; no remote database, no real AI calls.

**39. What are the main limitations of the current system?**
See answer 9, plus: tokens in localStorage, no migrations, per-process throttling, no CI, only 42 of 114 routes referenced by automated tests, unused dependencies (alembic, passlib, prometheus-client), Docker/Kubernetes files not verified.

**40. How can this application scale to thousands of users?**
The API is stateless (JWT) and async, so it can run as several instances behind a load balancer (Kubernetes manifests exist but I have not deployed them). Needed steps: PostgreSQL connection pooling, indexes on hot queries, move rate limiting and login throttling to Redis, run resume analysis in a worker queue (Celery code exists but is not wired to a running worker), store files in object storage, cache job results, and add monitoring. This is a design plan, not something I load-tested.

**41. What would you do first if you had one more week?**
Add Alembic migrations and CI, move tokens to HttpOnly cookies, add email verification and password reset, and require approval before someone can become a recruiter or placement officer.

## F. Extra likely questions

**42. What is an ORM and why use SQLAlchemy?**
An ORM maps tables to Python classes so we write `select(Resume).where(...)` instead of raw SQL strings; it prevents SQL injection by parameterising and works with both PostgreSQL and SQLite.

**43. What is async and why does it matter here?**
While the server waits for the database or the LLM it can serve other users instead of blocking, which matters because the Mentor call can take several seconds.

**44. How do WebSockets differ from REST in your project?**
REST is one request, one answer. The interview studio keeps a connection open so the server can push the next question and the final report as events (`START`, `ANSWER_SUBMITTED`, `FINISH`).

**45. Where is the API key stored and can users see it?**
Only in the backend environment (`.env`, git-ignored). It is never sent to the browser, never prefixed with `NEXT_PUBLIC_`, and never returned by an API. The `/mentor/status` endpoint only says whether AI is available.

**46. How do you know the resume analysis is "correct"?**
It is deterministic and documented, so correctness means "the formula does what it says". Tests check that a strong resume scores higher than a weak one, that scanned PDFs are flagged, and that missing skills are listed. It is not claimed to match any real company's ATS.

**47. Why are some pages "not available yet" (forgot password, OTP)?**
The backend has no such endpoints, so the pages say so instead of pretending. This was a deliberate honesty fix.
