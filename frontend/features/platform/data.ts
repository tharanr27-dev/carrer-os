import {
  Activity,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  Briefcase,
  Building2,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  Command,
  FileText,
  GraduationCap,
  LineChart,
  MessageSquareText,
  Mic,
  MonitorPlay,
  Network,
  PieChart,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  Video,
} from "lucide-react";

export const interviewTypes = [
  "Resume Based Interview",
  "Job Description Based Interview",
  "Technical Interview",
  "HR Interview",
  "Behavioral Interview",
  "Coding Interview",
  "System Design Interview",
  "Voice Interview",
  "Video Interview",
];

export const companies = ["Google", "Microsoft", "Amazon", "Stripe", "Atlassian", "Infosys", "TCS", "Deloitte"];

export const interviewQuestions = [
  "Walk me through the architecture of your most complex project.",
  "How would you reduce latency in a high-traffic recommendation API?",
  "Describe a conflict you handled during a team delivery.",
  "Design a notification system for 20 million users.",
  "What tradeoffs did you make in your resume project?",
];

export const interviewScores = [
  { subject: "Technical", current: 84, previous: 72 },
  { subject: "Communication", current: 78, previous: 68 },
  { subject: "Confidence", current: 82, previous: 71 },
  { subject: "Problem Solving", current: 88, previous: 76 },
  { subject: "Behavioral", current: 74, previous: 66 },
  { subject: "Time", current: 80, previous: 70 },
];

export const progressSeries = [
  { week: "W1", career: 62, communication: 55, technical: 58, interview: 48, learning: 44, applications: 3 },
  { week: "W2", career: 66, communication: 60, technical: 64, interview: 55, learning: 52, applications: 6 },
  { week: "W3", career: 72, communication: 67, technical: 70, interview: 63, learning: 61, applications: 10 },
  { week: "W4", career: 79, communication: 73, technical: 76, interview: 71, learning: 69, applications: 14 },
  { week: "W5", career: 84, communication: 80, technical: 82, interview: 78, learning: 76, applications: 18 },
];

export const feedbackCards = [
  {
    title: "Strengths",
    points: ["Clear project ownership", "Strong API fundamentals", "Good recruiter-style examples"],
  },
  {
    title: "Weaknesses",
    points: ["Answers run long", "STAR method is incomplete", "System design metrics need sharper numbers"],
  },
  {
    title: "Root Cause Analysis",
    points: ["You start with implementation before clarifying constraints", "Resume bullets do not quantify business impact"],
  },
  {
    title: "Why Marks Were Deducted",
    points: ["Missed failure-mode discussion", "Limited vocabulary variation", "Speaking speed spiked during follow-ups"],
  },
  {
    title: "Recommended Improvements",
    points: ["Use a 20-second answer frame", "Add scale, latency, and cost numbers", "Practice two follow-up branches per question"],
  },
  {
    title: "Weekly Improvement Plan",
    points: ["Mon: STAR drills", "Wed: system design whiteboard", "Fri: company-specific mock", "Sun: report review"],
  },
];

export const communicationModules = [
  "Self Introduction",
  "HR Conversation",
  "Behavioral Answers",
  "Group Discussion Practice",
  "Presentation Practice",
  "Daily Speaking Challenge",
  "Grammar Practice",
  "Vocabulary Builder",
  "Pronunciation Page",
  "Speech Analytics",
  "Confidence Meter",
  "Filler Word Counter",
  "Speaking Speed",
  "Eye Contact Placeholder",
  "Body Language Placeholder",
  "Progress History",
];

export const academyCourses = [
  "Python",
  "SQL",
  "Java",
  "C++",
  "Machine Learning",
  "Deep Learning",
  "Generative AI",
  "LLM",
  "RAG",
  "FastAPI",
  "Docker",
  "Kubernetes",
  "AWS",
  "Azure",
  "System Design",
  "Data Structures",
  "Algorithms",
  "Operating Systems",
  "DBMS",
  "Computer Networks",
  "Behavioral Skills",
  "Communication Skills",
  "Resume Writing",
  "LinkedIn Optimization",
  "HR Preparation",
];

export const jobCards = [
  {
    role: "Software Engineer - Backend",
    company: "Stripe",
    location: "Remote - India",
    match: 94,
    missing: "Kafka, PCI compliance",
    salary: "24-32 LPA",
    difficulty: "High",
    rating: 4.6,
  },
  {
    role: "AI Product Engineer",
    company: "Microsoft",
    location: "Bengaluru",
    match: 89,
    missing: "Azure OpenAI",
    salary: "22-30 LPA",
    difficulty: "Medium",
    rating: 4.5,
  },
  {
    role: "Data Platform Intern",
    company: "Atlassian",
    location: "Hybrid",
    match: 86,
    missing: "Airflow",
    salary: "80K/month",
    difficulty: "Medium",
    rating: 4.7,
  },
];

export const kanbanColumns = [
  { title: "Applied", items: ["Stripe Backend", "Google STEP"] },
  { title: "Shortlisted", items: ["Microsoft AI Engineer"] },
  { title: "Assessment", items: ["Atlassian Data"] },
  { title: "Technical Interview", items: ["Amazon SDE"] },
  { title: "HR Interview", items: ["Deloitte Analyst"] },
  { title: "Offer", items: ["Vercel Intern"] },
  { title: "Rejected", items: ["Meta SWE"] },
];

export const communityPosts = [
  { topic: "Interview Experience", title: "Stripe backend round focused on API idempotency", likes: 128, comments: 34 },
  { topic: "Company Review", title: "Microsoft intern loop had practical system design", likes: 92, comments: 18 },
  { topic: "Salary Discussion", title: "2026 campus offers for AI product roles", likes: 211, comments: 57 },
  { topic: "Career Tips", title: "How I turned a weak resume into a 90 percent match", likes: 76, comments: 12 },
];

export const mentorPrompts = [
  "Build my weekly interview plan",
  "Improve this resume bullet",
  "Which roles match my skills?",
  "Create a learning path for RAG",
  "Prepare me for Stripe",
];

export const reportTypes = [
  "Interview Reports",
  "Career Reports",
  "Learning Reports",
  "Application Reports",
  "Progress Reports",
];

export const searchGroups = [
  { title: "Jobs", icon: Briefcase, items: ["Backend Engineer", "AI Product Engineer", "Data Platform Intern"] },
  { title: "Courses", icon: BookOpen, items: ["System Design", "RAG", "Communication Skills"] },
  { title: "Companies", icon: Building2, items: ["Stripe", "Microsoft", "Atlassian"] },
  { title: "Students", icon: Users, items: ["Alex Morgan", "Jessica Smith", "Ryan Thompson"] },
  { title: "Community", icon: MessageSquareText, items: ["Interview Experiences", "Salary Discussions", "Career Tips"] },
  { title: "Commands", icon: Command, items: ["Start Mock Interview", "Download Career Report", "Open Mentor"] },
];

export const notificationCategories = ["Jobs", "Interviews", "Learning", "Applications", "Community", "System"];

export const navCatalog = [
  { href: "/interviews", label: "AI Interviews", icon: Mic },
  { href: "/communication", label: "Communication Coach", icon: MessageSquareText },
  { href: "/academy", label: "Training Academy", icon: BookOpen },
  { href: "/job-portal", label: "Job Portal", icon: Briefcase },
  { href: "/applications", label: "Application Tracker", icon: ClipboardList },
  { href: "/analytics", label: "Progress Analytics", icon: BarChart3 },
  { href: "/community", label: "Community", icon: Users },
  { href: "/mentor", label: "AI Mentor", icon: Bot },
  { href: "/global-search", label: "Global Search", icon: Search },
  { href: "/notification-center", label: "Notifications", icon: Bell },
  { href: "/reports", label: "Reports", icon: FileText },
];

export const rolePortalLinks = {
  recruiter: [
    { href: "/recruiter", label: "Dashboard", icon: Building2 },
    { href: "/recruiter/post-job", label: "Post Job", icon: Briefcase },
    { href: "/recruiter/manage-jobs", label: "Manage Jobs", icon: ClipboardList },
    { href: "/recruiter/candidates", label: "Candidate Search", icon: Users },
    { href: "/recruiter/reports", label: "Interview Reports", icon: PieChart },
    { href: "/recruiter/scheduling", label: "Scheduling", icon: CalendarClock },
    { href: "/recruiter/analytics", label: "Analytics", icon: LineChart },
  ],
  officer: [
    { href: "/officer", label: "Dashboard", icon: GraduationCap },
    { href: "/officer/students", label: "Students", icon: Users },
    { href: "/officer/departments", label: "Departments", icon: Network },
    { href: "/officer/statistics", label: "Placement Stats", icon: BarChart3 },
    { href: "/officer/training", label: "Training Assignment", icon: BookOpen },
    { href: "/officer/mock-interviews", label: "Mock Interviews", icon: Mic },
    { href: "/officer/reports", label: "Reports", icon: FileText },
    { href: "/officer/company-visits", label: "Company Visits", icon: Building2 },
  ],
  admin: [
    { href: "/admin", label: "Dashboard", icon: ShieldCheck },
    { href: "/admin/users", label: "Users", icon: Users },
    { href: "/admin/recruiters", label: "Recruiters", icon: Building2 },
    { href: "/admin/colleges", label: "Colleges", icon: GraduationCap },
    { href: "/admin/jobs", label: "Jobs", icon: Briefcase },
    { href: "/admin/content", label: "Learning Content", icon: BookOpen },
    { href: "/admin/community", label: "Moderation", icon: MessageSquareText },
    { href: "/admin/models", label: "AI Models", icon: Sparkles },
    { href: "/admin/monitoring", label: "Monitoring", icon: Activity },
  ],
};

export const interviewModes = [
  { label: "Voice", icon: Mic, status: "Frontend ready" },
  { label: "Video", icon: Video, status: "Camera placeholder" },
  { label: "Live Screen", icon: MonitorPlay, status: "Recruiter simulation" },
  { label: "AI Questions", icon: Sparkles, status: "Generated queue" },
  { label: "Company Specific", icon: Building2, status: "Role tuned" },
  { label: "Result Report", icon: CheckCircle2, status: "Charts included" },
];

export const learningCardDetails = ["Overview", "Learning Progress", "Lessons", "Practice", "Quiz", "Assignments", "Projects", "Completion Status", "Certificates", "Bookmarks"];

export const recruiterSections = ["Post Job", "Manage Jobs", "Candidate Search", "Candidate Details", "Shortlisted Candidates", "Interview Reports", "Interview Scheduling", "Analytics", "Company Profile", "Settings"];
export const officerSections = ["Students", "Departments", "Placement Statistics", "Training Assignment", "Mock Interview Assignment", "Reports", "Analytics", "Company Visits", "Eligible Students"];
export const adminSections = ["Users", "Recruiters", "Colleges", "Jobs", "Learning Content", "Community Moderation", "Reports", "Analytics", "AI Models Placeholder", "System Monitoring", "Audit Logs", "Settings"];

export const readinessMetrics = [
  { label: "Overall Score", value: 86 },
  { label: "Technical Score", value: 84 },
  { label: "Communication Score", value: 78 },
  { label: "Confidence Score", value: 82 },
  { label: "Problem Solving", value: 88 },
  { label: "Behavioral Score", value: 74 },
  { label: "Time Management", value: 80 },
  { label: "Resume Relevance", value: 91 },
  { label: "STAR Method Usage", value: 68 },
  { label: "Grammar", value: 87 },
  { label: "Vocabulary", value: 76 },
  { label: "Fluency", value: 81 },
  { label: "Speaking Speed", value: 73 },
];

export const dailyTasks = ["2 mock HR answers", "1 coding explanation out loud", "15 vocabulary cards", "1 resume relevance rewrite", "5-minute speaking speed drill"];
