"use client";

import * as React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  Archive,
  ArrowRight,
  Bell,
  Bookmark,
  Bot,
  Briefcase,
  Building2,
  CalendarClock,
  CheckCircle2,
  ChevronDown,
  Clock,
  FileText,
  Filter,
  GraduationCap,
  Mic,
  MonitorPlay,
  Pause,
  Play,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Star,
  Target,
  Timer,
  Trophy,
  Users,
  Volume2,
  XCircle,
} from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  academyCourses,
  adminSections,
  communicationModules,
  companies,
  communityPosts,
  dailyTasks,
  feedbackCards,
  interviewModes,
  interviewQuestions,
  interviewScores,
  interviewTypes,
  jobCards,
  kanbanColumns,
  learningCardDetails,
  mentorPrompts,
  notificationCategories,
  officerSections,
  progressSeries,
  readinessMetrics,
  recruiterSections,
  reportTypes,
  searchGroups,
} from "./data";

type Metric = { label: string; value: string; icon?: React.ElementType; tone?: string };

function PageHero({
  eyebrow,
  title,
  description,
  icon: Icon = Sparkles,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon?: React.ElementType;
  action?: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-card text-card-foreground dark:bg-slate-950 dark:text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(99,102,241,0.22),transparent_35%),radial-gradient(circle_at_85%_10%,rgba(20,184,166,0.16),transparent_30%)]" />
      <div className="relative flex flex-col gap-5 p-6 md:flex-row md:items-center md:justify-between">
        <div className="max-w-3xl">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-border bg-muted/60 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground dark:border-white/10 dark:bg-white/5 dark:text-indigo-200">
            <Icon className="h-3.5 w-3.5" />
            {eyebrow}
          </div>
          <h1 className="text-2xl font-bold tracking-tight md:text-4xl">{title}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground dark:text-slate-300">{description}</p>
        </div>
        {action ? (
          <Button className="w-full gap-2 bg-primary text-primary-foreground hover:bg-primary/90 md:w-auto">
            {action}
            <ArrowRight className="h-4 w-4" />
          </Button>
        ) : null}
      </div>
    </div>
  );
}

function MetricStrip({ metrics }: { metrics: Metric[] }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => {
        const Icon = metric.icon ?? Target;
        return (
          <Card key={metric.label} hoverEffect>
            <CardContent className="flex items-center justify-between p-5">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{metric.label}</p>
                <p className="mt-1 text-2xl font-bold">{metric.value}</p>
              </div>
              <div className={`rounded-xl p-3 ${metric.tone ?? "bg-primary/10 text-primary"}`}>
                <Icon className="h-5 w-5" />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function StatusPill({ children, tone = "indigo" }: { children: React.ReactNode; tone?: "indigo" | "emerald" | "amber" | "rose" }) {
  const tones = {
    indigo: "border-indigo-500/20 bg-indigo-500/10 text-indigo-300",
    emerald: "border-emerald-500/20 bg-emerald-500/10 text-emerald-300",
    amber: "border-amber-500/20 bg-amber-500/10 text-amber-300",
    rose: "border-rose-500/20 bg-rose-500/10 text-rose-300",
  };
  return <span className={`rounded-full border px-2.5 py-1 text-[10px] font-semibold ${tones[tone]}`}>{children}</span>;
}

function ChartCard({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription className="text-xs">{description}</CardDescription>
      </CardHeader>
      <CardContent className="h-72">{children}</CardContent>
    </Card>
  );
}

function AccordionCards({ cards = feedbackCards }: { cards?: typeof feedbackCards }) {
  const [open, setOpen] = React.useState(cards[0]?.title ?? "");
  return (
    <div className="grid gap-3 lg:grid-cols-2">
      {cards.map((card) => {
        const isOpen = open === card.title;
        return (
          <Card key={card.title} className="overflow-hidden">
            <button
              onClick={() => setOpen(isOpen ? "" : card.title)}
              className="flex w-full items-center justify-between p-5 text-left"
            >
              <div>
                <p className="text-sm font-semibold">{card.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">{card.points[0]}</p>
              </div>
              <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${isOpen ? "rotate-180" : ""}`} />
            </button>
            {isOpen ? (
              <div className="border-t border-border px-5 pb-5 pt-3">
                <div className="space-y-2">
                  {card.points.map((point) => (
                    <div key={point} className="flex items-start gap-2 rounded-lg bg-muted/40 p-3 text-xs text-muted-foreground">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-400" />
                      <span>{point}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </Card>
        );
      })}
    </div>
  );
}

export function InterviewStudio() {
  const [selectedType, setSelectedType] = React.useState("Technical Interview");
  const [company, setCompany] = React.useState("Stripe");
  const [difficulty, setDifficulty] = React.useState("Senior");
  const [paused, setPaused] = React.useState(false);

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="AI Mock Interview Module"
        title="Recruiter-grade interview studio"
        description="Configure company, difficulty, duration, resume context, and job description context, then run a realistic live interview with AI question generation and voice or video placeholders."
        icon={Mic}
        action="Start Interview"
      />

      <MetricStrip
        metrics={[
          { label: "Duration", value: "45 min", icon: Timer },
          { label: "Question Queue", value: "12", icon: Sparkles, tone: "bg-teal-500/10 text-teal-400" },
          { label: "Current Round", value: difficulty, icon: Target, tone: "bg-amber-500/10 text-amber-400" },
          { label: "Company", value: company, icon: Building2, tone: "bg-emerald-500/10 text-emerald-400" },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Interview Setup</CardTitle>
            <CardDescription className="text-xs">Select type, company, difficulty, and context source.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <p className="mb-2 text-xs font-semibold text-muted-foreground">Interview Type</p>
              <div className="grid grid-cols-1 gap-2">
                {interviewTypes.map((type) => (
                  <button
                    key={type}
                    onClick={() => setSelectedType(type)}
                    className={`rounded-lg border px-3 py-2 text-left text-xs transition-all ${
                      selectedType === type ? "border-primary bg-primary/10 text-primary" : "border-border bg-muted/30 hover:bg-muted"
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="space-y-2 text-xs font-semibold text-muted-foreground">
                Company
                <select value={company} onChange={(e) => setCompany(e.target.value)} className="h-10 w-full rounded-lg border border-input bg-background px-3 text-foreground">
                  {companies.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label className="space-y-2 text-xs font-semibold text-muted-foreground">
                Difficulty
                <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="h-10 w-full rounded-lg border border-input bg-background px-3 text-foreground">
                  {["Beginner", "Intermediate", "Senior", "FAANG"].map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="grid gap-2 text-xs">
              <Button variant="outline" className="justify-start gap-2"><FileText className="h-4 w-4" /> Attach resume context</Button>
              <Button variant="outline" className="justify-start gap-2"><Briefcase className="h-4 w-4" /> Paste job description</Button>
            </div>
          </CardContent>
        </Card>

        <Card glowEffect>
          <CardHeader className="border-b border-border">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-base">Live Interview Screen</CardTitle>
                <CardDescription className="text-xs">A realistic recruiter flow with timer, progress, and follow-up controls.</CardDescription>
              </div>
              <div className="flex flex-wrap gap-2">
                <StatusPill tone="emerald">Live</StatusPill>
                <StatusPill>{selectedType}</StatusPill>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5 p-5">
            <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
              <div className="min-h-[360px] rounded-2xl border border-border bg-card text-card-foreground dark:bg-slate-950 dark:text-white p-5">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>Question 4 of 12</span>
                  <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> 31:42 remaining</span>
                </div>
                <Progress value={33} className="mt-4 bg-muted/40" indicatorClassName="bg-teal-400" />
                <div className="mt-8 flex items-center gap-3">
                  <div className="grid h-12 w-12 place-items-center rounded-full bg-indigo-500/20 text-indigo-200">
                    <Bot className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">AI Recruiter is thinking</p>
                    <div className="mt-2 flex gap-1">
                      {[0, 1, 2].map((dot) => (
                        <motion.span
                          key={dot}
                          className="h-2 w-2 rounded-full bg-teal-300"
                          animate={{ opacity: [0.25, 1, 0.25], y: [0, -4, 0] }}
                          transition={{ duration: 1.1, delay: dot * 0.15, repeat: Infinity }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mt-8 rounded-xl border border-border bg-muted/30 dark:border-white/10 dark:bg-white/5 p-5">
                  <p className="text-xs uppercase tracking-wider text-muted-foreground">{`Current Question`}</p>
                  <p className="mt-2 text-lg font-semibold leading-7">{interviewQuestions[3]}</p>
                  <p className="mt-3 text-sm text-muted-foreground">Follow-up likely: bottlenecks, data model, rate limits, observability, and rollout plan.</p>
                </div>
                <div className="mt-5 flex flex-wrap gap-2">
                  <Button size="sm" variant="secondary" onClick={() => setPaused(!paused)} className="gap-2">
                    {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
                    {paused ? "Resume" : "Pause Interview"}
                  </Button>
                  <Button size="sm" variant="outline">Ask Again</Button>
                  <Button size="sm" variant="outline">Skip Question</Button>
                  <Button size="sm" variant="destructive">End Interview</Button>
                </div>
              </div>
              <div className="space-y-4">
                {interviewModes.map((mode) => {
                  const Icon = mode.icon;
                  return (
                    <div key={mode.label} className="rounded-xl border border-border bg-muted/30 p-4">
                      <div className="flex items-center justify-between">
                        <Icon className="h-5 w-5 text-primary" />
                        <StatusPill tone="emerald">{mode.status}</StatusPill>
                      </div>
                      <p className="mt-3 text-sm font-semibold">{mode.label}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <InterviewResult />
    </div>
  );
}

export function InterviewResult() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {readinessMetrics.slice(0, 8).map((metric) => (
          <Card key={metric.label}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-muted-foreground">{metric.label}</p>
                <span className="text-sm font-bold">{metric.value}%</span>
              </div>
              <Progress value={metric.value} className="mt-3" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <ChartCard title="Radar Chart" description="Current interview capability against previous attempts.">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={interviewScores}>
              <PolarGrid stroke="hsl(var(--border))" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
              <Radar dataKey="previous" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.18} />
              <Radar dataKey="current" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.35} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Progress Chart" description="Comparison with previous interviews.">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={interviewScores}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="subject" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="previous" fill="#94a3b8" radius={[6, 6, 0, 0]} />
              <Bar dataKey="current" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">AI Feedback and Coaching Plan</CardTitle>
          <CardDescription className="text-xs">Strengths, weaknesses, root causes, marks deducted, learning modules, career advice, readiness, companies, roles, and daily practice tasks.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <AccordionCards />
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            {dailyTasks.map((task) => (
              <div key={task} className="rounded-xl border border-border bg-muted/30 p-4 text-xs font-medium">
                <CheckCircle2 className="mb-2 h-4 w-4 text-emerald-400" />
                {task}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function CommunicationCoach() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="Communication Coach" title="Daily speaking practice for interviews and workplace confidence" description="Practice introductions, HR conversations, behavioral stories, group discussions, presentations, grammar, vocabulary, pronunciation, and speech analytics." icon={Volume2} action="Start Daily Challenge" />
      <MetricStrip
        metrics={[
          { label: "Confidence Meter", value: "82%", icon: Target },
          { label: "Filler Words", value: "6/min", icon: AlertTriangle, tone: "bg-amber-500/10 text-amber-400" },
          { label: "Speaking Speed", value: "142 wpm", icon: Timer, tone: "bg-teal-500/10 text-teal-400" },
          { label: "Practice Streak", value: "14 days", icon: Trophy, tone: "bg-emerald-500/10 text-emerald-400" },
        ]}
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {communicationModules.map((module, index) => (
          <Card key={module} hoverEffect>
            <CardContent className="p-5">
              <div className="mb-4 flex items-center justify-between">
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary">
                  {index % 3 === 0 ? <Mic className="h-5 w-5" /> : index % 3 === 1 ? <Users className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
                </div>
                <StatusPill tone={index % 2 ? "indigo" : "emerald"}>{index < 8 ? "Practice" : "Analytics"}</StatusPill>
              </div>
              <p className="text-sm font-semibold">{module}</p>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">AI scoring, transcript review, confidence patterns, and guided improvement tasks.</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <ChartCard title="Progress History" description="Communication, fluency, and confidence growth.">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={progressSeries}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="week" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="communication" stroke="#14b8a6" strokeWidth={3} />
            <Line type="monotone" dataKey="interview" stroke="#8b5cf6" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

export function TrainingAcademy() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="AI Training Academy" title="Structured learning paths for career readiness" description="A modular academy covering engineering, AI, cloud, systems, resume, LinkedIn, and HR preparation with progress, lessons, practice, quizzes, assignments, projects, certificates, and bookmarks." icon={GraduationCap} action="Continue Learning" />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {academyCourses.map((course, index) => (
          <Card key={course} hoverEffect>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{course}</CardTitle>
                <Bookmark className="h-4 w-4 text-muted-foreground" />
              </div>
              <CardDescription className="text-xs">AI curated course path with practical milestones.</CardDescription>
            </CardHeader>
            <CardContent>
              <Progress value={35 + ((index * 7) % 55)} />
              <div className="mt-4 flex flex-wrap gap-2">
                {learningCardDetails.slice(0, 6).map((detail) => (
                  <span key={detail} className="rounded-full bg-muted px-2 py-1 text-[10px] text-muted-foreground">{detail}</span>
                ))}
              </div>
              <div className="mt-4 flex items-center justify-between text-xs">
                <span className="text-muted-foreground">{8 + (index % 5)} lessons left</span>
                <Button size="sm" variant="outline">Open</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function JobPortal() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="Job Portal" title="AI matched jobs with preparation intelligence" description="Search, filter, save, apply, track status, inspect companies, view missing skills, readiness, interview difficulty, salary, ratings, benefits, and launch preparation." icon={Briefcase} action="Find Jobs" />
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-[1fr_auto_auto_auto]">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input className="pl-9" placeholder="Search jobs, companies, skills, or locations" />
          </div>
          {["Salary", "Experience", "Remote", "Skill"].map((filter) => (
            <Button key={filter} variant="outline" className="gap-2"><Filter className="h-4 w-4" /> {filter}</Button>
          ))}
        </CardContent>
      </Card>
      <Tabs defaultValue="recommended">
        <TabsList className="flex h-auto flex-wrap justify-start">
          {["recommended", "saved", "applied", "status", "companies"].map((tab) => (
            <TabsTrigger key={tab} value={tab} className="capitalize">{tab}</TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value="recommended">
          <div className="grid gap-4 lg:grid-cols-3">
            {jobCards.map((job) => (
              <Card key={`${job.company}-${job.role}`} hoverEffect>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-base">{job.role}</CardTitle>
                      <CardDescription className="text-xs">{job.company} - {job.location}</CardDescription>
                    </div>
                    <StatusPill tone="emerald">{job.match}% match</StatusPill>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4 text-xs">
                  <Progress value={job.match} />
                  <div className="grid grid-cols-2 gap-3">
                    <Info label="Missing Skills" value={job.missing} />
                    <Info label="Salary" value={job.salary} />
                    <Info label="Difficulty" value={job.difficulty} />
                    <Info label="Rating" value={`${job.rating}/5`} />
                  </div>
                  <div className="rounded-xl border border-border bg-muted/30 p-3">
                    <p className="font-semibold">Preparation Status</p>
                    <p className="mt-1 text-muted-foreground">2 mock interviews, 4 lessons, and 1 project recommended before applying.</p>
                  </div>
                  <Button className="w-full gap-2">Prepare <ArrowRight className="h-4 w-4" /></Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
        {["saved", "applied", "status", "companies"].map((tab) => (
          <TabsContent key={tab} value={tab}>
            <EmptyState title={`${tab.charAt(0).toUpperCase() + tab.slice(1)} Jobs`} description="A production-ready section placeholder connected to the portal navigation and design system." />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-muted/40 p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-1 font-semibold">{value}</p>
    </div>
  );
}

export function ApplicationTracker() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="Application Tracker" title="Kanban pipeline for every job application" description="Track applied roles, shortlists, assessments, interview rounds, offers, rejection learning, timelines, notes, documents, dates, and recruiter contact placeholders." icon={CalendarClock} action="Add Application" />
      <div className="grid gap-4 xl:grid-cols-7">
        {kanbanColumns.map((column) => (
          <Card key={column.title} className="min-h-[320px]">
            <CardHeader className="p-4">
              <CardTitle className="text-sm">{column.title}</CardTitle>
              <CardDescription className="text-xs">{column.items.length} active</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 p-4 pt-0">
              {column.items.map((item) => (
                <div key={item} className="rounded-xl border border-border bg-muted/30 p-3 text-xs">
                  <p className="font-semibold">{item}</p>
                  <p className="mt-1 text-muted-foreground">Timeline, notes, documents, date, and recruiter contact ready.</p>
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function ProgressAnalytics() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="Progress Analytics" title="Career readiness command center" description="Track communication growth, technical growth, interviews, learning, applications, skill improvement, weekly goals, monthly goals, achievements, badges, and streaks." icon={LineChart} action="Download Snapshot" />
      <MetricStrip
        metrics={[
          { label: "Career Readiness", value: "84%", icon: Target },
          { label: "Learning Streak", value: "21 days", icon: Trophy, tone: "bg-emerald-500/10 text-emerald-400" },
          { label: "Weekly Goals", value: "8/10", icon: CheckCircle2, tone: "bg-teal-500/10 text-teal-400" },
          { label: "Badges", value: "12", icon: Star, tone: "bg-amber-500/10 text-amber-400" },
        ]}
      />
      <div className="grid gap-6 xl:grid-cols-2">
        <ChartCard title="Career Readiness Trend" description="Communication, technical, interview, and learning growth.">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={progressSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="week" />
              <YAxis />
              <Tooltip />
              <Area dataKey="career" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.2} />
              <Area dataKey="technical" stroke="#14b8a6" fill="#14b8a6" fillOpacity={0.16} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Applications and Skill Improvement" description="Weekly application velocity and skill momentum.">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={progressSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="week" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="applications" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
              <Bar dataKey="learning" fill="#14b8a6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}

export function CommunityHub() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="Community" title="Professional career community" description="Home feed for interview experiences, company reviews, salary discussions, career tips, questions, answers, likes, comments, bookmarks, trending topics, categories, profiles, and anonymous posting." icon={Users} action="Create Post" />
      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          {communityPosts.map((post) => (
            <Card key={post.title} hoverEffect>
              <CardContent className="p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <StatusPill>{post.topic}</StatusPill>
                    <h3 className="mt-3 text-lg font-semibold">{post.title}</h3>
                    <p className="mt-2 text-sm text-muted-foreground">Anonymous posting toggle enabled. Recruiters and students can bookmark, answer, and follow topics.</p>
                  </div>
                  <Button variant="outline" size="sm">Bookmark</Button>
                </div>
                <div className="mt-4 flex gap-4 text-xs text-muted-foreground">
                  <span>{post.likes} likes</span>
                  <span>{post.comments} comments</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Trending Topics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {["AI interviews", "System design", "Campus salaries", "Resume reviews", "Remote internships"].map((topic) => (
              <div key={topic} className="rounded-lg bg-muted/40 p-3 text-xs font-medium">{topic}</div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function MentorWorkspace() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="AI Career Mentor" title="Full mentor interface with persistent career context" description="Chat history, suggested prompts, advice, skill recommendations, resume advice, learning recommendations, interview coaching, quick actions, voice and attachment placeholders, sidebar, and pinned conversations." icon={Bot} action="New Conversation" />
      <div className="grid gap-6 xl:grid-cols-[300px_1fr]">
        <Card className="h-full">
          <CardHeader>
            <CardTitle className="text-base">Conversation Sidebar</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {["Pinned: Stripe prep", "Resume rewrite", "RAG roadmap", "Weekly plan"].map((chat) => (
              <button key={chat} className="w-full rounded-xl border border-border bg-muted/30 p-3 text-left text-xs hover:bg-muted">{chat}</button>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">AI Coach Summary</CardTitle>
            <CardDescription className="text-xs">Personalized guidance across roles, skills, resume, learning, and interviews.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="rounded-2xl bg-muted/40 p-5 text-sm leading-6 text-muted-foreground">
              You are closest to backend and AI product engineering roles. Focus this week on system design explanation, RAG project polish, and shorter behavioral answers using STAR.
            </div>
            <div className="flex flex-wrap gap-2">
              {mentorPrompts.map((prompt) => (
                <Button key={prompt} variant="outline" size="sm">{prompt}</Button>
              ))}
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-border bg-background p-3">
              <Input placeholder="Ask your mentor about skills, resume, interviews, or jobs..." className="border-0 bg-transparent shadow-none" />
              <Button size="icon" variant="outline"><Mic className="h-4 w-4" /></Button>
              <Button size="icon"><Send className="h-4 w-4" /></Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function PortalDashboard({ type }: { type: "recruiter" | "officer" | "admin" }) {
  const map = {
    recruiter: {
      eyebrow: "Recruiter Dashboard",
      title: "Hiring operations portal",
      description: "Post jobs, manage jobs, search candidates, inspect candidate details, shortlist talent, review interview reports, schedule interviews, view analytics, company profile, and settings.",
      icon: Building2,
      sections: recruiterSections,
    },
    officer: {
      eyebrow: "College Placement Dashboard",
      title: "Placement office control room",
      description: "Manage students, departments, placement statistics, training assignments, mock interview assignments, reports, analytics, company visits, and eligible student cohorts.",
      icon: GraduationCap,
      sections: officerSections,
    },
    admin: {
      eyebrow: "Admin Dashboard",
      title: "System administration workspace",
      description: "Manage users, recruiters, colleges, jobs, learning content, community moderation, reports, analytics, AI models, monitoring, audit logs, and platform settings.",
      icon: ShieldCheck,
      sections: adminSections,
    },
  };
  const config = map[type];
  return (
    <div className="space-y-6">
      <PageHero eyebrow={config.eyebrow} title={config.title} description={config.description} icon={config.icon} action="Open Actions" />
      <MetricStrip
        metrics={[
          { label: "Active Records", value: type === "admin" ? "18.4K" : type === "officer" ? "1.2K" : "342", icon: Users },
          { label: "Reports", value: "48", icon: FileText, tone: "bg-teal-500/10 text-teal-400" },
          { label: "Scheduled", value: "24", icon: CalendarClock, tone: "bg-amber-500/10 text-amber-400" },
          { label: "Health", value: "99.9%", icon: CheckCircle2, tone: "bg-emerald-500/10 text-emerald-400" },
        ]}
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {config.sections.map((section) => (
          <Card key={section} hoverEffect>
            <CardContent className="p-5">
              <div className="mb-4 flex items-center justify-between">
                <div className="grid h-10 w-10 place-items-center rounded-xl bg-primary/10 text-primary">
                  <MonitorPlay className="h-5 w-5" />
                </div>
                <StatusPill tone="emerald">Ready</StatusPill>
              </div>
              <p className="font-semibold">{section}</p>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">Enterprise-grade table, profile, filtering, workflow, analytics, and action states prepared for integration.</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function GlobalSearch() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="Global Search" title="Search jobs, courses, companies, students, community, and commands" description="Unified search UI with recent searches, command palette patterns, categories, keyboard-friendly results, and fast navigation." icon={Search} action="Run Search" />
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-4 top-4 h-5 w-5 text-muted-foreground" />
            <Input className="h-14 pl-12 text-base" placeholder="Search across CareerOS AI..." />
          </div>
        </CardContent>
      </Card>
      <div className="grid gap-4 lg:grid-cols-3">
        {searchGroups.map((group) => {
          const Icon = group.icon;
          return (
            <Card key={group.title}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base"><Icon className="h-4 w-4 text-primary" /> {group.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {group.items.map((item) => (
                  <div key={item} className="rounded-lg bg-muted/40 p-3 text-xs">{item}</div>
                ))}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

export function NotificationCenter() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="Notifications" title="Advanced notification center" description="Category-aware job, interview, learning, application, community, and system notifications with unread, read, and archive states." icon={Bell} action="Mark All Read" />
      <Tabs defaultValue="unread">
        <TabsList>
          {["unread", "read", "archive"].map((tab) => (
            <TabsTrigger key={tab} value={tab} className="capitalize">{tab}</TabsTrigger>
          ))}
        </TabsList>
        {["unread", "read", "archive"].map((tab) => (
          <TabsContent key={tab} value={tab}>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {notificationCategories.map((category, index) => (
                <Card key={`${tab}-${category}`} hoverEffect>
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between">
                      <StatusPill tone={tab === "archive" ? "amber" : index % 2 ? "indigo" : "emerald"}>{category}</StatusPill>
                      {tab === "archive" ? <Archive className="h-4 w-4 text-muted-foreground" /> : <Bell className="h-4 w-4 text-primary" />}
                    </div>
                    <p className="mt-4 text-sm font-semibold">{category} update ready</p>
                    <p className="mt-2 text-xs leading-5 text-muted-foreground">Grouped notification state with source, timestamp, action, and archive handling.</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

export function ReportsCenter() {
  return (
    <div className="space-y-6">
      <PageHero eyebrow="Reports" title="Downloadable professional report center" description="PDF-ready report layouts for interviews, career, learning, applications, and progress with executive summaries, charts, findings, and action plans." icon={FileText} action="Export PDF" />
      <div className="grid gap-4 lg:grid-cols-5">
        {reportTypes.map((report) => (
          <Card key={report} hoverEffect>
            <CardContent className="p-5">
              <FileText className="h-5 w-5 text-primary" />
              <p className="mt-4 font-semibold">{report}</p>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">Downloadable report page with charts, summary, insights, and next steps.</p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="bg-white text-slate-950 dark:bg-slate-100">
        <CardContent className="p-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">PDF Preview</p>
              <h2 className="mt-2 text-2xl font-bold">CareerOS AI Interview Report</h2>
              <p className="mt-2 max-w-2xl text-sm text-slate-600">Executive summary, score distribution, evidence-based deductions, recommended modules, weekly plan, and recruiter-ready readiness statement.</p>
            </div>
            <div className="rounded-xl border border-slate-200 p-4 text-right">
              <p className="text-3xl font-bold">86%</p>
              <p className="text-xs text-slate-500">Overall score</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <Card>
      <CardContent className="grid min-h-[240px] place-items-center p-8 text-center">
        <div>
          <XCircle className="mx-auto h-8 w-8 text-muted-foreground" />
          <h3 className="mt-4 font-semibold">{title}</h3>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">{description}</p>
        </div>
      </CardContent>
    </Card>
  );
}
