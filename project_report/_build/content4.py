"""Chapters 10-13, appendix and references."""
import json
import os

from docmodel import appendix, bullets, chapter, code, figure, h2, h3, numbered, p, references, table

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = json.load(open(os.path.join(HERE, "data", "samples.json"), encoding="utf-8"))
COUNTS = json.load(open(os.path.join(HERE, "data", "test_counts.json"), encoding="utf-8"))
SHOTS = "screenshots"

# ═════════════════════════ CHAPTER 10 ═════════════════════════
chapter("Implementation and User Interface")
h2("Development and Run Environment")
p("The system was implemented with a Next.js frontend in the `frontend` directory and a FastAPI backend in the `careeros_backend` "
  "directory of one Git repository: about 18,400 lines of Python in 183 files and about 13,300 lines of TypeScript in 84 files, excluding "
  "tests. For the screens in this chapter the backend ran with Uvicorn on a temporary SQLite database and the frontend with the "
  "Next.js development server. The data belongs to fictional users (for example \"Priya Raman\") created through the application's own "
  "interface and API; no real personal data and no remote database were used. All figures in this chapter are real screenshots of the "
  "running application, captured with a headless browser.")
h2("Login and Registration")
p("The login page (left of {fig:loginreg}) accepts an e-mail address and password, shows server messages such as a throttling notice and "
  "links to the pages for password reset and e-mail verification, which state honestly that these functions are not available yet. "
  "The registration page (right) asks for a name, e-mail address, password and the intended role; the role is stored in the profile, "
  "but permissions come from the server, not from this choice.")
figure("loginreg", "c1_login_register.png", "Login page (left) and registration page (right)", 5.4, SHOTS)
h2("Student Dashboard and Resume Center")
p("The dashboard ({fig:dash}) shows career readiness, the latest ATS resume score, learning progress and the latest interview "
  "score, with quick actions, workspace links and the tasks of the active roadmap. In the resume centre ({fig:resume_ui}) the student "
  "uploads a PDF or DOCX file and sees the analysis: ATS readiness, writing mechanics and overall quality, found and missing skills "
  "and suggestions with their impact. A note states that the scores are rule-based measurements, not judgements by a language model "
  "or by any company's screening system.")
figure("dash", "04_student_dashboard.png", "Student dashboard", 5.8, SHOTS)
figure("resume_ui", "05_resume_center.png", "Resume Center with the rule-based analysis", 5.8, SHOTS)
h2("Interview Preparation and Role-Based Training")
p("The interview-preparation page ({fig:prep}) is organised in tabs for the roadmap, role training, aptitude, technical, coding, "
  "communication, HR, resume questions, mock interviews and performance, and shows the target role, the overall preparation "
  "percentage computed from saved answers and a score for each round. In the role-training tab ({fig:rolesetup}) the student has typed "
  "\"Cloud Security Specialist\", which is not in the catalogue. The system accepts the title, matches it to the closest known role "
  "(Cloud Engineer), shows the related topics, reports that 24 reviewed questions match and offers level, difficulty, number of "
  "questions and optional AI generation.")
figure("prep", "06_interview_prep_home.png", "Interview Preparation home with progress by round", 5.8, SHOTS)
figure("rolesetup", "08_role_training_setup.png", "Role selection with a custom job title", 5.8, SHOTS)
p("During a session ({fig:rolefb}) one question is shown with its topic, difficulty, kind and marks, a progress bar and an "
  "expandable explanation of why the questions were chosen. After the answer is submitted the result appears immediately: the status, "
  "the marks earned, the correct answer, the explanation, what the student got right or missed, and a suggestion. At the end the review "
  "({fig:review1}) shows the percentage and marks computed on the server, counts by result, topic-wise bars, strong and weak areas, "
  "suggested revision topics and the scoring rules; below it every question is listed with filters for all, correct, partially "
  "correct, incorrect and unanswered questions, and the buttons Practise Again and Improve Weak Areas start the next session.")
figure("rolefb", "09_role_question_feedback.png", "Immediate feedback after submitting an answer", 5.8, SHOTS)
figure("review1", "10_role_review_summary.png", "Assessment review: score, counts and topic-wise performance", 5.8, SHOTS)
h2("AI Mentor and Job Recommendations")
p("The mentor page ({fig:mentorui}) shows the conversation, a multi-line input (Enter sends, Shift+Enter inserts a new line) and a "
  "separate panel of suggested next steps from the student's saved activity. When no provider key is configured the page shows a "
  "setup notice instead of pretending to answer. The reply in the figure was produced by a real request to the configured language "
  "model; the interface shows it as plain text, so Markdown symbols appear literally, which is a possible improvement. The "
  "recommended-jobs tab ({fig:jobsui}) searches live remote listings, explains that the source covers remote roles only and shows each "
  "job with a skill-match estimate and a link to the original listing.")
figure("mentorui", "12_ai_mentor.png", "AI Mentor conversation with suggested next steps", 5.8, SHOTS)
figure("jobsui", "13_recommended_jobs.png", "Recommended IT jobs from a live remote-jobs source", 5.8, SHOTS)
h2("Recruiter, Placement Officer and Administrator Interfaces")
p("The recruiter portal (left of {fig:portals}) lists the company's jobs and offers tabs for posting a job and reviewing applicants; "
  "the placement-office portal (right) offers drives and a form for a new drive. The administrator console ({fig:admin}) shows user "
  "counts, system status, AI usage and a system-health panel; in the local run the panel reports the task worker as down because no "
  "worker process was started. Screens that were not captured, such as the live interview studio and the mobile layout, are listed in "
  "the file Screenshots_Required.md delivered with this report.")
figure("portals", "c2_recruiter_officer.png", "Recruiter portal (left) and placement officer portal (right)", 5.8, SHOTS)
figure("admin", "19_admin_portal.png", "Administrator console", 5.0, SHOTS)

# ═════════════════════════ CHAPTER 11 ═════════════════════════
chapter("Testing and Results")
h2("Testing Strategy and Environment")
p("Testing was automated wherever possible and designed to be safe: tests use an in-memory SQLite database and scripted "
  "language-model responses, never the remote database and never a real provider. A fixture that applies to every training test replaces "
  "the provider client, so a key stored in the developer's environment cannot be used by accident. Backend tests run with "
  "`python -m pytest` (pytest 9, pytest-asyncio, Python 3.14), frontend tests with `npx vitest run`, types with `npx tsc --noEmit`, "
  "lint with `npm run lint` and `ruff`, and the production build with `npm run build`; the final run was made on 31 October 2026. "
  "Result labels have exactly four values: PASSED, FAILED, BLOCKED and NOT RUN.")
h2("Unit, Integration and API Testing")
layers = [
    ("Unit tests (functions and classes)", ["tests/unit/", "tests/training/test_engine_units.py", "tests/training/test_bank_integrity.py", "tests/services/"]),
    ("Repository and provisioning tests", ["tests/repositories/", "tests/training/test_provisioning.py"]),
    ("API contract and smoke tests", ["tests/api/", "tests/smoke/"]),
    ("Security, guards and pre-deployment audit", ["tests/security/", "tests/training/test_security_hardening.py", "tests/training/test_pre_deploy_audit.py"]),
    ("Feature tests (training, resume, coaching, placement, mentor, role training)", ["tests/training/test_training_api.py", "tests/training/test_real_resume_and_recs.py",
        "tests/training/test_real_coaching_features.py", "tests/training/test_real_placement_recruiter_and_guards.py", "tests/training/test_mentor_ai.py", "tests/training/test_role_training.py"]),
    ("WebSocket, integration, performance, load, AI contracts", ["tests/websocket/", "tests/integration/", "tests/performance/", "tests/load/", "tests/ai/"]),
]
rows, total = [], 0
for name, prefixes in layers:
    n = sum(v for k, v in COUNTS.items() if any(k.startswith(x) for x in prefixes))
    total += n
    rows.append([name, str(n)])
assert total == 483, total
rows.append(["Total backend tests", "483"])
table("layers", "Backend automated tests by layer", ["Layer", "Number of tests"], rows, widths=[10.6, 3.4], fs=10)
p("API tests call the real application through an HTTP test client with dependency overrides for the database session and the "
  "signed-in user, and contract tests also check the shape of responses on which the frontend relies.")
h2("Frontend, Database and Security Testing")
p("Eight frontend test files contain 54 tests, all of which passed. They render the real components with the network layer replaced "
  "and cover the authentication pages, role-based navigation, the resume centre, recommended jobs, interview preparation, the AI Mentor "
  "(11 tests) and role training (10 tests); one test replaces only the network call and checks that every client method sends the "
  "method, path and body that the backend route expects. Repository contract tests and the API tests run against SQLite and verify "
  "that records are inserted, read back and isolated by user; training tables were also checked for PostgreSQL compatibility by "
  "compiling their definitions for that dialect, but no test connected to the remote database, so remote persistence is **NOT RUN**. "
  "Security tests verify that unauthenticated requests receive 401, that wrongly typed tokens are refused, that a login becomes "
  "throttled after repeated failures, that another student's resume, mentor conversation or role session cannot be read (403 or 404), "
  "that administrator routes need permissions, and that recruiter and officer routes are limited to their own company or college.")
h2("Browser Testing")
p("The repository contains two Node-based browser scripts (`e2e/roles.e2e.mjs`, `e2e/student.e2e.mjs`); they were **NOT RUN** for this "
  "report. Instead, a scripted headless browser was driven through the running application on 31 October 2026: it opened 19 pages "
  "with the sessions of four different users, typed a custom job title, started a role session, answered a question, opened a "
  "completed review and read a mentor conversation, saving a screenshot of each page. All steps completed (manual scripted run, "
  "**PASSED**), but they were not recorded as automated assertions.")
h2("Selected Test Cases")
tc = [
    ["TC1", "Register with a password shorter than 8 characters", "Rejected with 422", "Rejected", "PASSED"],
    ["TC2", "Log in with six wrong passwords", "Sixth attempt blocked (429)", "Blocked", "PASSED"],
    ["TC3", "Student B downloads Student A's resume", "403, no file returned", "403", "PASSED"],
    ["TC4", "Analyse a complete and a poor resume", "Complete resume scores higher; poor gets no canned skills", "As expected", "PASSED"],
    ["TC5", "Mentor request when the provider fails", "Safe error; no message saved", "As expected", "PASSED"],
    ["TC6", "Mentor follow-up question", "Earlier turns are sent to the provider", "As expected", "PASSED"],
    ["TC7", "Role training for \"Cloud Security Specialist\"", "Title kept; matched to Cloud Engineer; cybersecurity and cloud questions", "As expected", "PASSED"],
    ["TC8", "Unmapped title without an LLM key", "Refused with a clear message; no session created", "As expected", "PASSED"],
    ["TC9", "Two roles in turn (Prompt Engineer, Data Analyst)", "Different, role-relevant questions", "As expected", "PASSED"],
    ["TC10", "Second session for the same role", "Prefers unseen questions", "As expected", "PASSED"],
    ["TC11", "Request more questions than the bank holds", "Repeats marked and explained; no duplicates in a session", "As expected", "PASSED"],
    ["TC12", "Wrong multiple-choice answer", "Incorrect; correct answer and explanation shown", "As expected", "PASSED"],
    ["TC13", "Written answer with half of the concepts", "Partially Correct with partial marks", "As expected", "PASSED"],
    ["TC14", "Submit the same answer twice", "Saved result returned; not scored twice", "As expected", "PASSED"],
    ["TC15", "Finish with unanswered questions", "Percentage equals saved marks over total; unanswered count as zero", "As expected", "PASSED"],
    ["TC16", "Open another student's role session", "404 for every endpoint", "404", "PASSED"],
    ["TC17", "Improve Weak Areas after a session", "Questions only from topics where marks were lost", "As expected", "PASSED"],
    ["TC18", "Malformed generated questions (11 kinds)", "All rejected before storage", "Rejected", "PASSED"],
]
table("cases", "Selected test cases, expected and actual results", ["ID", "Test case", "Expected result", "Actual result", "Status"], tc, widths=[1.1, 4.7, 5.0, 2.1, 1.7], fs=9)
h2("Test Summary and Results")
table("results", "Summary of verification results (final run, 31 October 2026)",
      ["Check", "Command", "Result", "Status"],
      [["Backend tests", "python -m pytest", "483 tests: 481 passed, 2 failed", "FAILED (2 tests)"],
       ["Frontend tests", "npx vitest run", "8 files, 54 tests passed", "PASSED"],
       ["TypeScript", "npx tsc --noEmit", "0 errors", "PASSED"],
       ["Lint (frontend)", "npm run lint", "0 errors, 2 warnings", "PASSED"],
       ["Production build", "npm run build", "Compiled; 32 static pages", "PASSED"],
       ["Lint (backend)", "ruff check app", "6 import-order findings (E402)", "FAILED (style)"],
       ["Automated browser tests", "e2e scripts", "Not executed", "NOT RUN"],
       ["Remote database; Docker and Kubernetes", "-", "Not executed by design", "NOT RUN"]],
      widths=[3.8, 3.4, 4.6, 2.2], fs=9.5)
p("Two backend tests failed in the final run. `test_password_verify_performance` is a timing benchmark that failed while the whole "
  "suite was running and passed in three separate reruns of its folder, so it is sensitive to machine load. "
  "`test_resume_repository_save_analysis_persists_suggestions_after_analysis` fails because of an uncommitted modification of "
  "`ResumeRepository.save_analysis` in the working tree: the modified method re-reads the latest analysis through a call that the "
  "test's simulated session does not support. Either the test or the modification must be updated before submission; this is an open "
  "item. A full run on 27 October 2026, which then contained 481 tests, had passed completely. The six lint findings come from a logger "
  "defined before imports in the same uncommitted edit.")
p("The language-model features cannot be proved by tests that use scripted providers, so they were also checked manually against "
  "the configured provider on 27 October 2026. The mentor answered three questions, including a follow-up and a non-English question "
  "answered in English. For a custom role (\"Sound Engineer\") the platform generated five questions that all passed validation; in a "
  "second session two generated questions were discarded by the validator. A written answer was graded by the model and the "
  "validated result stored. These checks show that the integration works; they do not measure the accuracy of generated answer keys.")

# ═════════════════════════ CHAPTER 12 ═════════════════════════
chapter("Results, Limitations and Future Enhancement")
h2("Results and Working Features")
p("The project delivered a working full-stack platform with 124 backend routes, 103 database tables, a reviewed bank of 235 questions, "
  "sixteen backend modules and role-specific portals. The tests and live checks of Chapter 11 show that the main student journey works "
  "from registration to a scored review. The working features are:")
bullets([
    "Registration, login, token refresh, role-based and ownership-based access control, login throttling.",
    "Resume upload, validation, local text extraction, rule-based analysis and authenticated download.",
    "Practice by round and topic with immediate grading and progress computed from saved answers.",
    "Role-based training for any job title with fresh-question preference, adaptive difficulty, instant marks and a complete review.",
    "AI Mentor with saved conversations, bounded history and safe error handling (needs a provider key).",
    "Recruiter, placement officer and administrator portals with company and college isolation.",
])
p("Partially working: recommended jobs depend on a public third-party interface and internet access; analytics, community and "
  "administrator screens are functional but basic; question generation and LLM grading were verified with a real provider only by a "
  "small manual check.")
h2("Known Limitations")
table("limits12", "Known limitations", ["Area", "Limitation"],
      [["AI", "The mentor needs an API key and internet; answers can be wrong and are not fact-checked; generated answer keys are validated for consistency, not for truth."],
       ["Assessment", "Written-answer scores are estimates; coding answers are self-assessed; the reviewed bank has 8 to 22 questions for each catalogued role."],
       ["Resume", "Keyword and structure analysis only; no optical character recognition; scores do not match any employer system."],
       ["Database", "Remote persistence not verified; no migration tool; soft deletion is not uniform; two denormalised user identifiers have no foreign key."],
       ["Security", "Tokens in browser storage cannot be revoked; throttling and rate limits are per process; no e-mail verification or password reset; any user can create a company or college and become its administrator."],
       ["Operations", "No continuous-integration pipeline; Docker and Kubernetes files are unverified, and the production compose file refers to a Dockerfile that does not exist."],
       ["Quality", "Two automated tests fail in the current working tree (Section 11.6)."]],
      widths=[2.6, 11.4], fs=10)
h2("External Dependencies and Security Considerations")
p("The platform depends on an optional language-model provider (Groq, xAI or Anthropic) and on the public Himalayas jobs interface; "
  "both are third-party services whose availability, prices and terms can change. When they fail, the affected feature reports the "
  "problem and the rest of the platform continues. Passwords are stored as salted bcrypt hashes, tokens are signed and typed, personal "
  "data is protected by ownership checks, uploads are validated, provider keys are read only on the server, and error messages never "
  "include internal details. These measures address several risk categories of the OWASP Top 10 (OWASP Foundation, 2021), such as broken "
  "access control and injection. Remaining risks include token storage in the browser, the absence of token revocation and the "
  "unrestricted creation of companies and colleges. An earlier version of the repository contained default administrator credentials in "
  "its history; they should be rotated.")
h2("Future Enhancement, Scalability and Deployment")
bullets([
    "Add database migrations, e-mail verification, password reset and HttpOnly-cookie sessions with token revocation.",
    "Render Markdown in the mentor, stream replies and extend the reviewed bank to more roles.",
    "Add optical character recognition for scanned resumes, sandboxed code execution and speech analysis.",
    "Require approval before a user becomes a recruiter or placement officer; add a continuous-integration pipeline.",
])
p("The API is stateless and asynchronous, so several instances can run behind a load balancer. For thousands of users the following "
  "steps are needed: connection pooling for PostgreSQL, indexes for the heaviest queries, shared rate limiting and login throttling in "
  "a store such as Redis, a worker queue for resume analysis, object storage for resumes, cached job results and monitoring. This is a "
  "design plan; no load test was performed. A realistic deployment would use a managed PostgreSQL instance, a container platform and "
  "HTTPS, with all secrets supplied through the environment.")

# ═════════════════════════ CHAPTER 13 ═════════════════════════
chapter("Conclusion")
p("Career OS was designed to give students one place to prepare for jobs and to receive feedback they can trust. It combines a "
  "Next.js and TypeScript frontend, a FastAPI backend and a SQLAlchemy data layer. A student can upload a resume that is analysed by "
  "documented formulas, practise from a reviewed bank, prepare for any job title through the role engine, receive immediate marks and "
  "explanations and read a complete review built from saved records. A hosted language model powers the AI Mentor and can supply extra "
  "role-specific questions, but every model output is bounded, validated and labelled.")
p("The technical achievements are a layered backend with 124 routes, ownership and permission checks, a role-to-topic engine that works "
  "for unseen job titles, a selection algorithm that avoids repetition and explains itself, server-side scoring, a validated generation "
  "pipeline and a test suite of 483 backend and 54 frontend tests. The project also records its limits openly: no model was trained, the "
  "remote database was not verified, two tests need attention, and production features such as e-mail verification and migrations "
  "remain to be added. With migrations, stronger session security and a managed "
  "database, the verified prototype can become a service that a placement cell operates for a whole batch of students.")

# ═════════════════════════ APPENDIX ═════════════════════════
appendix("Sample API Requests and Responses")
p("Real exchanges captured on 31 October 2026 from a temporary database with a fictional user; long values and lists are trimmed. "
  "The complete route list is in the file API_Endpoint_Inventory.md.")
KEEP = ("Submit an answer (instant evaluation)", "Send a message to the AI Mentor")
for s in [x for x in SAMPLES if x["title"] in KEEP]:
    req = json.dumps(s["request"], indent=1, ensure_ascii=False) if s["request"] is not None else "(no body)"
    resp = json.dumps(s["response"], indent=1, ensure_ascii=False)
    lines = resp.split("\n")
    if len(lines) > 12:
        lines = lines[:12] + ["  ... (trimmed)"]
    code(f"{s['method']} {s['path']}\nRequest: {req}\nResponse {s['status']}:\n" + "\n".join(lines), s["title"])

# ═════════════════════════ REFERENCES ═════════════════════════
REF = [
    "Black, P. and Wiliam, D. (1998) ‘Assessment and Classroom Learning’, Assessment in Education: Principles, Policy & Practice, Vol. 5, No. 1, pp. 7–74.",
    "Brown, T.B. et al. (2020) ‘Language Models are Few-Shot Learners’, Advances in Neural Information Processing Systems, Vol. 33, pp. 1877–1901.",
    "FastAPI (n.d.) ‘FastAPI documentation’. Available at: https://fastapi.tiangolo.com",
    "Fette, I. and Melnikov, A. (2011) ‘The WebSocket Protocol’, RFC 6455, Internet Engineering Task Force.",
    "Fielding, R.T. (2000) ‘Architectural Styles and the Design of Network-based Software Architectures’, Doctoral dissertation, University of California, Irvine.",
    "Fuller, J., Raman, M., Sage-Gavin, E. and Hines, K. (2021) ‘Hidden Workers: Untapped Talent’, Harvard Business School Project on Managing the Future of Work and Accenture, September 2021.",
    "Groq (n.d.) ‘GroqCloud documentation’. Available at: https://console.groq.com/docs",
    "Himalayas (n.d.) ‘Remote Jobs API documentation’. Available at: https://himalayas.app/docs/remote-jobs-api",
    "Jaccard, P. (1912) ‘The Distribution of the Flora in the Alpine Zone’, New Phytologist, Vol. 11, No. 2, pp. 37–50.",
    "Jones, M., Bradley, J. and Sakimura, N. (2015) ‘JSON Web Token (JWT)’, RFC 7519, Internet Engineering Task Force.",
    "Lewis, P. et al. (2020) ‘Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks’, Advances in Neural Information Processing Systems, Vol. 33, pp. 9459–9474.",
    "Meta Platforms (n.d.) ‘React documentation’. Available at: https://react.dev",
    "OWASP Foundation (2021) ‘OWASP Top 10:2021’. Available at: https://owasp.org/Top10/",
    "Provos, N. and Mazières, D. (1999) ‘A Future-Adaptable Password Scheme’, Proceedings of the USENIX Annual Technical Conference, pp. 81–92.",
    "Pydantic (n.d.) ‘Pydantic documentation’. Available at: https://docs.pydantic.dev",
    "Roediger, H.L. and Karpicke, J.D. (2006) ‘Test-Enhanced Learning: Taking Memory Tests Improves Long-Term Retention’, Psychological Science, Vol. 17, No. 3, pp. 249–255.",
    "Salton, G. and Buckley, C. (1988) ‘Term-weighting Approaches in Automatic Text Retrieval’, Information Processing & Management, Vol. 24, No. 5, pp. 513–523.",
    "SQLAlchemy (n.d.) ‘SQLAlchemy documentation’. Available at: https://docs.sqlalchemy.org",
    "Supabase (n.d.) ‘Supabase documentation’. Available at: https://supabase.com/docs",
    "Tailwind Labs (n.d.) ‘Tailwind CSS documentation’. Available at: https://tailwindcss.com/docs",
    "TanStack (n.d.) ‘TanStack Query documentation’. Available at: https://tanstack.com/query",
    "The PostgreSQL Global Development Group (n.d.) ‘PostgreSQL documentation’. Available at: https://www.postgresql.org/docs/",
    "Vaswani, A. et al. (2017) ‘Attention Is All You Need’, Advances in Neural Information Processing Systems, Vol. 30, pp. 5998–6008.",
    "Vercel (n.d.) ‘Next.js documentation’. Available at: https://nextjs.org/docs",
    "Wei, J. et al. (2022) ‘Chain-of-Thought Prompting Elicits Reasoning in Large Language Models’, Advances in Neural Information Processing Systems, Vol. 35.",
]
references(REF)
