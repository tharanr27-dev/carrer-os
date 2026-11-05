"""Front matter data and Chapters 1-3."""
from docmodel import bullets, chapter, figure, h2, h3, numbered, p, table

FRONT = dict(
    abstract=(
        "Students preparing for jobs usually depend on separate tools for resume writing, aptitude practice, interview rehearsal "
        "and job search, and none of these tools tells a student how ready they are or what to do next. Career OS is a web-based "
        "platform that brings these activities together and gives feedback computed from the student's own saved data. The system "
        "uses a Next.js and TypeScript frontend, a FastAPI backend and a relational database accessed through SQLAlchemy. A student "
        "can upload a resume that is analysed by documented rule-based formulas, practise from a reviewed bank of 235 questions, "
        "train for any job role by choosing or typing a title, receive immediate marks and explanations, and read a complete scored "
        "review of every session. A role engine maps any job title to practice topics, prefers questions the student has not seen, "
        "adapts difficulty to earlier results and, when a language-model key is configured, generates validated questions to fill "
        "gaps. An AI Mentor answers free-form questions through a hosted language model using only verified facts from the student's "
        "own records. Recruiters, placement officers and administrators have separate portals. The backend exposes 124 routes and has "
        "483 automated tests, of which 481 passed in the final run; the frontend has 54 passing tests. No model was trained, and "
        "persistence on the remote database was not verified."
    ),
    keywords="job preparation, resume analysis, adaptive assessment, role-based training, large language model, FastAPI, Next.js",
    abbreviations=[
        ("AI", "Artificial Intelligence"), ("API", "Application Programming Interface"), ("ATS", "Applicant Tracking System"),
        ("CORS", "Cross-Origin Resource Sharing"), ("CSS", "Cascading Style Sheets"), ("DFD", "Data Flow Diagram"),
        ("ER", "Entity Relationship"), ("HTTP(S)", "Hypertext Transfer Protocol (Secure)"), ("JSON", "JavaScript Object Notation"),
        ("JWT", "JSON Web Token"), ("LLM", "Large Language Model"), ("MCQ", "Multiple-Choice Question"), ("ORM", "Object-Relational Mapping"),
        ("PDF", "Portable Document Format"), ("RBAC", "Role-Based Access Control"), ("REST", "Representational State Transfer"),
        ("SQL", "Structured Query Language"), ("STAR", "Situation, Task, Action, Result"), ("UI / UX", "User Interface / User Experience"),
        ("UUID", "Universally Unique Identifier"), ("WS", "WebSocket"),
    ],
)

# ═════════════════════════ CHAPTER 1 ═════════════════════════
chapter("Introduction")
h2("General and Background")
p("Preparing for a first job is a multi-step task. A student has to write a resume that a screening system can read, practise "
  "aptitude and technical questions, learn to speak about projects, rehearse interviews and find openings that match their skills. "
  "Most students handle each step with a different website, and the results are never connected: a poor quiz score does not "
  "change what the student practises next, and a resume score does not influence the interview preparation. Practice material is "
  "plentiful but generic; a student applying for a backend developer position and one applying for a cloud engineer position are "
  "usually shown the same question lists. Large studies of hiring practices also report that automated screening can filter out "
  "qualified applicants because of rigid rules (Fuller et al., 2021), so students need to understand how machines read their documents.")
p("Career OS is a web-based job-preparation and career-readiness platform developed to close this gap. It keeps the student's "
  "profile, resume analysis, practice results, interview reports and goals in one database and uses them to produce feedback and "
  "recommendations for four kinds of users: students, recruiters, placement officers and administrators. This report describes the "
  "design (Chapters 3 and 4), technology and modules (Chapters 5 and 6), database and backend interface (Chapters 7 and 8), algorithms "
  "(Chapter 9), screens (Chapter 10), testing (Chapter 11), results and limitations (Chapter 12) of the system as it exists in the "
  "project repository.")
h2("Problem Statement")
p("Students lack a single place that (i) measures how complete and readable their resume is, (ii) lets them practise questions that "
  "match the job role they want, however unusual the title, (iii) gives immediate and explained feedback on every answer, (iv) remembers "
  "what they have already practised so that new sessions contain fresh questions, and (v) answers their free-form questions without "
  "inventing facts about them. The problem addressed by Career OS is the design and implementation of such a platform with honest, "
  "traceable scoring.")
h2("Existing System and Its Limitations")
p("The usual approach is a collection of independent tools: a word-processor template for the resume, free online quizzes for "
  "aptitude, video tutorials for interviews, a job portal for searching and a general chatbot for questions. Each has its own login, "
  "its own data and its own idea of progress. {tab:limits} summarises the limitations and the response of Career OS.")
table("limits", "Limitations of the existing approach and the response of Career OS",
      ["Limitation", "Response in Career OS"],
      [["Tools are disconnected, so there is no overall view of readiness", "One database; recommendations read resume, practice and goals together"],
       ["Practice is not role-specific and questions repeat", "Role engine maps any job title to topics; a seen-question history prefers unseen questions"],
       ["Feedback is delayed, vague or unexplained", "Immediate result, correct answer, explanation and suggestion, labelled by scoring method"],
       ["General chatbots may invent facts about the user", "The mentor receives only verified records and refuses to chat without a configured provider"]],
      widths=[6.5, 7.5], fs=10.5)
h2("Proposed System")
p("Career OS is proposed as an integrated platform with a web frontend, an application server and a relational database. After "
  "registration a student maintains a profile, uploads a resume, practises by round or by job role, rehearses interviews, chats with "
  "an AI Mentor and follows a learning roadmap ({fig:modules}). Recruiters publish jobs and review applications, placement "
  "officers organise campus drives and rank students, and administrators manage users, roles and announcements.")
figure("modules", "fig_1_1_modules.png", "Main modules of the Career OS student workspace", 4.7)
p("The system is deliberately honest about its intelligence. Resume analysis, interview and communication feedback, "
  "recommendations, the roadmap and placement ranking are rule-based algorithms with documented formulas. A large language model is "
  "used in one place only, the AI Mentor, and optionally to generate and grade role-specific questions when a provider key is "
  "configured. No machine-learning model is trained in this project.")
h2("Objectives and Scope")
numbered([
    "Provide secure registration and login with role-based access for four user groups.",
    "Analyse an uploaded resume and report completeness, readability and wording with transparent formulas.",
    "Let a student practise for any job role, prefer unseen questions, adapt difficulty and explain the choice.",
    "Evaluate every answer immediately and compute final scores on the server from saved records.",
    "Provide an AI Mentor that uses only verified facts from the student's account, and portals for recruiters, officers and administrators.",
    "Verify the implementation with automated tests and report its limitations honestly.",
])
p("The scope covers the web application, the backend services, the database design and the automated tests. It excludes a mobile "
  "application, payments, e-mail delivery, social sign-in, speech or video analysis and execution of student-written code. "
  "Question content is a reviewed bank of 235 questions extended by optional AI generation. The target users are students "
  "(preparation, resume feedback, mentor), recruiters (jobs and applications), placement officers (drives and ranking) and "
  "administrators (users, roles, audit). Scores are practice feedback, not predictions of hiring decisions.")
h2("Applications and Expected Outcomes")
p("A college placement cell can prepare students before campus drives and rank registered students; a training institute can use "
  "the role-based engine for roles that standard question sets do not cover; an individual job seeker can use the resume analysis and "
  "the mentor to find missing skills for a target role. The expected outcome is a working, tested platform in which a student can "
  "complete the full cycle of analysing a resume, practising for a role, seeing immediate feedback, reading a scored review and "
  "following suggested next steps, with every figure traceable to saved data.")

# ═════════════════════════ CHAPTER 2 ═════════════════════════
chapter("Literature Survey and Existing System")
p("This chapter reviews the approaches that students and institutions use today and the ideas on which Career OS builds. Product "
  "categories are described in general terms and no vendor statistics are quoted; scholarly sources are cited only where their "
  "content was checked, and all are listed in the References.")
h2("Job Preparation and Interview Platforms")
p("Preparation material is delivered through job portals that list vacancies, assessment sites that offer timed quizzes and coding "
  "problems, interview-practice services that connect candidates with peers or mentors, and learning platforms that offer courses. "
  "Job portals concentrate on search and applications, and assessment sites on a limited set of skills. Interview services "
  "typically offer question lists by company or topic, recorded mock interviews or live sessions with people. Question lists are "
  "usually static, so a student who practises regularly sees the same questions again. In general, none of these channels combines "
  "resume feedback, role-specific practice and a conversational assistant under one account.")
h2("Resume Screening Systems")
p("Employers use applicant tracking systems to store and filter applications. Fuller et al. (2021) studied hiring practices in "
  "several countries and concluded that automated systems that rely on rigid exclusion rules can screen out candidates who could do "
  "the job. For students this means that a resume must be machine-readable and must state skills clearly. Keyword matching is the "
  "basic technique behind many such checks; it is related to term weighting in information retrieval (Salton and Buckley, 1988) and "
  "to set-overlap measures such as the Jaccard index (Jaccard, 1912). Career OS uses transparent keyword and structure measurements and "
  "states clearly that its scores are not those of any employer's system.")
h2("Online Assessment Systems")
p("Educational research supports frequent, low-stakes testing with feedback. Roediger and Karpicke (2006) showed that taking a "
  "memory test improved long-term retention compared with repeated study, and Black and Wiliam (1998) reviewed evidence that "
  "formative assessment raises learning achievement. These findings motivate the design of Career OS, where every answer is graded "
  "immediately and explained and weak topics are revisited in later sessions. Multiple-choice questions can be graded exactly, "
  "whereas free-text answers need a rubric; Career OS uses an expected-concept rubric and, when available, a language model to judge "
  "semantic equivalence.")
h2("AI-Based Career Assistance")
p("Large language models are based on the Transformer architecture (Vaswani et al., 2017). Brown et al. (2020) showed that a large "
  "model can perform new tasks from a few examples placed in the prompt, which makes it possible to adapt behaviour by prompt design "
  "instead of training. Wei et al. (2022) described chain-of-thought prompting for reasoning tasks, and Lewis et al. (2020) "
  "introduced retrieval-augmented generation, in which a model is grounded in retrieved text. These ideas explain why Career OS "
  "supplies verified facts from the student's own records to the mentor instead of relying on the model's memory. Such models can "
  "produce fluent but wrong statements, so the platform restricts the context, caps the output and warns the student.")
h2("Limitations of Existing Approaches and Comparison")
p("Separate tools do not share data, question sets are static or role-agnostic, general chatbots may state invented details with "
  "equal confidence, and scores are often unexplained. {tab:compare} compares typical approaches qualitatively with Career OS.")
table("compare", "Qualitative comparison of typical approaches with Career OS",
      ["Capability", "Job portals", "Quiz sites", "General chatbot", "Career OS"],
      [["Resume feedback", "Limited", "Rare", "Possible, unverified", "Rule-based analysis of the file"],
       ["Practice for any job title", "No", "Fixed categories", "Possible, unvalidated", "Role engine, validated questions"],
       ["Fresh-question history", "Not applicable", "Rarely", "No memory of practice", "Per-student seen map"],
       ["Explained instant feedback", "No", "Often", "Yes, may be wrong", "Yes, labelled by method"],
       ["Uses the student's own records", "Profile only", "Scores only", "Only if pasted", "Verified facts in the mentor"]],
      widths=[3.0, 2.2, 2.4, 2.8, 3.6], fs=10)

# ═════════════════════════ CHAPTER 3 ═════════════════════════
chapter("System Requirements and Feasibility Study")
h2("Functional Requirements")
table("fr", "Functional requirements of Career OS",
      ["ID", "Requirement", "Status"],
      [["FR1", "Register, log in, refresh a session; maintain a profile and target role", "Implemented, tested"],
       ["FR2", "Upload a PDF or DOCX resume, analyse it and download the stored file", "Implemented, rule-based"],
       ["FR3", "Practise aptitude, technical, coding, communication, HR and managerial rounds", "Implemented, tested"],
       ["FR4", "Practise for any job role with fresh questions and a scored review", "Implemented, tested"],
       ["FR5", "Run live interview and communication sessions over WebSocket", "Implemented, rule-based"],
       ["FR6", "Chat with an AI Mentor and keep the conversation history", "Implemented; needs an LLM key"],
       ["FR7", "Suggest next steps and a learning roadmap; list recommended remote jobs", "Implemented; jobs need internet"],
       ["FR8", "Recruiters: companies, jobs, applications. Officers: colleges, drives, eligibility, ranking", "Implemented"],
       ["FR9", "Administration, community, dashboards and notifications", "Implemented (partly basic)"]],
      widths=[1.2, 9.4, 3.4], fs=10.5)
h2("Non-Functional Requirements")
table("nfr", "Non-functional requirements and how they are met",
      ["Quality", "How it is met"],
      [["Security and privacy", "bcrypt hashes, JWT, role and ownership checks, login throttling, upload validation; every personal resource is filtered by the authenticated user"],
       ["Reliability", "Typed provider errors; nothing is saved when an external service fails"],
       ["Performance", "Asynchronous server, React Query caching, bounded conversation history"],
       ["Maintainability", "Router, service, repository and model layers; 124 documented routes"],
       ["Honesty and portability", "Scores labelled by method; runs on SQLite locally and on PostgreSQL"]],
      widths=[3.4, 10.6], fs=10.5)
h2("Hardware and Software Requirements")
table("hwsw", "Hardware and software requirements",
      ["Item", "Requirement"],
      [["Hardware (development)", "Dual-core 2 GHz processor, 8 GB RAM, 5 GB free storage, internet access for the LLM and jobs services"],
       ["Hardware (small deployment, estimated)", "2 virtual CPUs, 4 GB RAM, 20 GB storage, public HTTPS endpoint"],
       ["Operating system", "Windows 11 (development); Linux container (deployment)"],
       ["Languages and runtimes", "Python 3.12 in the Dockerfile (3.14 on the development machine); Node.js 24; TypeScript 5"],
       ["Frameworks", "FastAPI with Uvicorn; Next.js 15.5 with React 19.1"],
       ["Database", "PostgreSQL (Supabase) or SQLite"],
       ["Tools and browser", "Git, npm, pip, pytest, Vitest, ESLint, ruff; any current Chromium-based browser or Firefox"]],
      widths=[4.4, 9.6], fs=10.5)
h2("Technology and User Requirements")
p("The project requires an HTTPS-capable application server, a PostgreSQL-compatible database for production, an optional LLM account "
  "(Groq, xAI or Anthropic) for the mentor and generation features, and outbound access to the public Himalayas jobs interface. Secrets "
  "such as the signing key, database URL and provider key are supplied only through environment variables and never sent to the browser. "
  "Students need clear feedback, fresh practice and a mentor that does not invent facts; recruiters need to publish jobs and move "
  "applicants through stages; placement officers need eligibility and ranking tools limited to their own college; administrators need "
  "role management and an audit trail.")
h2("Feasibility Study")
p("**Technical feasibility.** Every component uses mature open-source technology. The backend and frontend were built, tested and run "
  "locally, the production build of the frontend succeeds, and a real language-model request through the configured provider was "
  "verified. The only external dependencies are the optional provider and the public jobs interface, both with defined failure behaviour.")
p("**Operational feasibility.** Students and staff use the system through a web browser with no installation, and the four user "
  "groups have separate portals. Limitations, such as the absence of e-mail verification, are stated in the interface where relevant.")
p("**Economic feasibility.** All frameworks are free software. The recurring costs are hosting and, optionally, LLM usage billed by "
  "the provider. The platform keeps these costs low by using stored questions first and calling the LLM only to fill gaps, with "
  "per-user limits on messages and generated questions. A cost estimate for a particular deployment was not measured.")
