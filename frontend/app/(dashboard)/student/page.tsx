"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/useAuthStore";
import { useNotificationStore } from "@/store/useNotificationStore";
import {
  Sparkles,
  Trophy,
  Calendar,
  Briefcase,
  AlertCircle,
  TrendingUp,
  CheckCircle2,
  FileCheck,
  Zap,
  Mic,
  Compass,
  BookOpen,
  MessageSquareText,
  FileText,
  GraduationCap,
  Bot,
  Bell,
  Plus,
  Play,
  ArrowRight,
  Target,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { motion } from "framer-motion";

// Mock Charts Data
const weeklyActivityData = [
  { day: "Mon", score: 40 },
  { day: "Tue", score: 45 },
  { day: "Wed", score: 65 },
  { day: "Thu", score: 55 },
  { day: "Fri", score: 85 },
  { day: "Sat", score: 70 },
  { day: "Sun", score: 95 },
];

export default function StudentDashboard() {
  const [isMounted, setIsMounted] = React.useState(false);
  const { user } = useAuthStore();
  const { notifications } = useNotificationStore();
  const [tasks, setTasks] = React.useState([
    { id: 1, label: "Complete advanced Next.js 15 routing mock tests", checked: false },
    { id: 2, label: "Add Missing Keywords 'Tailwind CSS v4' to resume", checked: true },
    { id: 3, label: "Run AI simulated screen test for Stripe interview", checked: false },
    { id: 4, label: "Submit application to Vercel Front-End Engineer opening", checked: false },
  ]);

  // Mount guard for Recharts
  React.useEffect(() => {
    setIsMounted(true);
  }, []);

  const toggleTask = (id: number) => {
    setTasks(tasks.map((t) => (t.id === id ? { ...t, checked: !t.checked } : t)));
  };

  const readinessScore = 78;
  const firstName = user?.name.trim().split(/\s+/)[0] || "Student";

  // Navigation cards setup
  const navCards = [
    { label: "Career Journey", desc: "View timelines & milestones", href: "/workspace?tab=careers", icon: GraduationCap, color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20" },
    { label: "AI Interview", desc: "Simulate live mock screenings", href: "/workspace?tab=interviews", icon: Mic, color: "text-violet-400 bg-violet-500/10 border-violet-500/20" },
    { label: "Learning Center", desc: "Start structured video lessons", href: "/workspace?tab=academy", icon: BookOpen, color: "text-teal-400 bg-teal-500/10 border-teal-500/20" },
    { label: "Jobs", desc: "Search matching openings", href: "/jobs", icon: Briefcase, color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
    { label: "Resume Center", desc: "Scan and optimize CV scores", href: "/workspace?tab=resume", icon: FileText, color: "text-sky-400 bg-sky-500/10 border-sky-500/20" },
    { label: "AI Mentor", desc: "Access persistent conversation", href: "/workspace?tab=mentor", icon: Bot, color: "text-pink-400 bg-pink-500/10 border-pink-500/20" },
    { label: "Communication Coach", desc: "Analyze grammar & filler speed", href: "/workspace?tab=communication", icon: MessageSquareText, color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
    { label: "Progress", desc: "View learning benchmarks", href: "/analytics", icon: Target, color: "text-rose-400 bg-rose-500/10 border-rose-500/20" },
    { label: "Recent Activity", desc: "Track weekly event checklists", href: "/analytics", icon: TrendingUp, color: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
  ];

  return (
    <div className="space-y-8 text-left">
      {/* Welcome Banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-8 border border-indigo-500/20 text-white shadow-xl"
      >
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded-full text-xs text-indigo-300 font-semibold">
              <Sparkles className="h-3.5 w-3.5 animate-pulse" /> AI Steering Active
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">Welcome back, {firstName}!</h1>
            <p className="text-sm text-indigo-200/80 max-w-xl leading-relaxed">
              Your overall Career Readiness is up **4.2%** this week. Let&apos;s tackle today&apos;s skill gap exercises.
            </p>
          </div>
          <Link href="/workspace?tab=discovery">
            <Button className="bg-background/90 text-foreground hover:bg-background font-semibold cursor-pointer shrink-0 border border-border shadow-sm">
              Launch Career Planner
            </Button>
          </Link>
        </div>
        {/* Background glow */}
        <div className="absolute right-0 top-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />
      </motion.div>

      {/* Grid layout: Gauges & metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Circular Gauge: Career Readiness Score */}
        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider">Career Readiness</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center pt-2">
            <div className="relative flex items-center justify-center">
              <svg className="w-24 h-24 transform -rotate-90">
                <circle cx="48" cy="48" r="40" stroke="currentColor" className="text-muted/20" strokeWidth="6" fill="transparent" />
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke="currentColor"
                  className="text-primary"
                  strokeWidth="6"
                  fill="transparent"
                  strokeDasharray={`${2 * Math.PI * 40}`}
                  strokeDashoffset={`${2 * Math.PI * 40 * (1 - readinessScore / 100)}`}
                />
              </svg>
              <span className="absolute text-xl font-bold">{readinessScore}%</span>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-3 font-medium">Ready for Junior Roles</p>
          </CardContent>
        </Card>

        {/* ATS Resume Score */}
        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider">ATS Resume Score</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">87/100</span>
              <FileCheck className="h-5 w-5 text-indigo-400" />
            </div>
            <div className="space-y-1">
              <Progress value={87} indicatorClassName="bg-indigo-500" />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>ATS Optimized</span>
                <span className="text-emerald-500 font-semibold">+12% vs last week</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Learning Progress */}
        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider">Learning Progress</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">76%</span>
              <BookOpen className="h-5 w-5 text-teal-400" />
            </div>
            <div className="space-y-1">
              <Progress value={76} indicatorClassName="bg-teal-500" />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>Advanced Next.js v15</span>
                <span>8 lessons left</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Weekly Progress Gauge */}
        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider">Weekly Progress Goal</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">8 / 10</span>
              <Trophy className="h-5 w-5 text-amber-400" />
            </div>
            <div className="space-y-1">
              <Progress value={80} indicatorClassName="bg-amber-500" />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>Activity Streak</span>
                <span className="text-emerald-500 font-semibold">14 Days Active</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: beautiful gateway cards */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">Workspace Gateways</CardTitle>
              <CardDescription className="text-xs">Quick links directly into specific learning & optimization tabs.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              {navCards.map((card) => {
                const Icon = card.icon;
                return (
                  <Link key={card.label} href={card.href} className="w-full">
                    <div className="flex flex-col items-start p-4 border border-border bg-card/40 hover:bg-primary/5 hover:border-primary/30 transition-all rounded-xl text-left cursor-pointer group h-full justify-between">
                      <div className={`p-2.5 rounded-lg border ${card.color} shrink-0 mb-3`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="space-y-1">
                        <p className="font-semibold text-xs text-slate-200 group-hover:text-primary transition-colors">{card.label}</p>
                        <p className="text-[10px] text-muted-foreground leading-normal">{card.desc}</p>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </CardContent>
          </Card>

          {/* Weekly Progress Line Chart */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold">Weekly Performance Trend</CardTitle>
                  <CardDescription className="text-xs">Aggregated career readiness points earned day-by-day</CardDescription>
                </div>
                <TrendingUp className="h-4 w-4 text-primary" />
              </div>
            </CardHeader>
            <CardContent className="h-64">
              {isMounted ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={weeklyActivityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="dashboardGlow" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="day" stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "hsl(var(--card))",
                        borderColor: "hsl(var(--border))",
                        borderRadius: "8px",
                        fontSize: "12px",
                      }}
                    />
                    <Area type="monotone" dataKey="score" stroke="hsl(var(--primary))" strokeWidth={2} fillOpacity={1} fill="url(#dashboardGlow)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full w-full bg-muted/20 animate-pulse rounded-lg" />
              )}
            </CardContent>
          </Card>

          {/* Recommended Jobs */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold">Recommended Jobs</CardTitle>
                  <CardDescription className="text-xs">Top job recommendations matching your target skill profile.</CardDescription>
                </div>
                <Link href="/jobs" className="text-xs text-primary hover:underline font-semibold flex items-center gap-1">
                  View All <ArrowRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { company: "Stripe", role: "Software Engineer (Frontend)", match: 94, salary: "$130k - $160k" },
                { company: "Vercel", role: "Front-End Architect", match: 91, salary: "$140k - $170k" },
              ].map((job) => (
                <div key={job.company} className="p-4 border border-border bg-card/30 rounded-xl flex items-center justify-between">
                  <div className="space-y-0.5">
                    <p className="font-semibold text-xs text-slate-200">{job.role}</p>
                    <p className="text-[10px] text-muted-foreground">{job.company} • {job.salary}</p>
                  </div>
                  <span className="rounded-full bg-primary/20 text-primary border border-primary/20 px-2 py-0.5 text-[10px] font-bold">
                    {job.match}% match
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Planner, Notifications, Quick Actions */}
        <div className="space-y-6">
          {/* Quick Actions Panel */}
          <Card className="border-indigo-500/10 bg-gradient-to-b from-indigo-500/5 to-transparent">
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Sparkles className="h-4.5 w-4.5 text-indigo-400" /> Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2.5 text-xs">
              <Button onClick={() => (window.location.href = "/workspace?tab=resume")} className="w-full text-xs shrink-0 cursor-pointer justify-start gap-2" variant="outline">
                <FileCheck className="h-4 w-4 text-sky-400" /> Optimize ATS Score
              </Button>
              <Button onClick={() => (window.location.href = "/workspace?tab=interviews")} className="w-full text-xs shrink-0 cursor-pointer justify-start gap-2" variant="outline">
                <Zap className="h-4 w-4 text-violet-400 animate-pulse" /> Launch Interview Room
              </Button>
              <Button onClick={() => (window.location.href = "/workspace?tab=mentor")} className="w-full text-xs shrink-0 cursor-pointer justify-start gap-2" variant="outline">
                <Bot className="h-4 w-4 text-pink-400" /> Consult AI Mentor
              </Button>
            </CardContent>
          </Card>

          {/* Today's Tasks Checklist */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">Today&apos;s Tasks</CardTitle>
              <CardDescription className="text-xs">Action plan generated by AI Mentor</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => toggleTask(task.id)}
                  className={`flex items-start gap-3 p-3 border rounded-xl cursor-pointer transition-all ${
                    task.checked
                      ? "bg-emerald-500/5 border-emerald-500/20 text-muted-foreground opacity-60 line-through"
                      : "bg-muted/40 border-muted hover:border-muted-foreground/20 text-foreground"
                  }`}
                >
                  <CheckCircle2 className={`h-4.5 w-4.5 shrink-0 mt-0.5 ${task.checked ? "text-emerald-500" : "text-muted-foreground"}`} />
                  <span className="text-[11px] leading-normal font-semibold">{task.label}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Upcoming Interviews Calendar */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">Upcoming Interviews</CardTitle>
              <CardDescription className="text-xs">Mock screens and schedules</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-muted/40 border border-muted rounded-xl">
                <div className="flex items-center gap-3">
                  <Calendar className="h-4 w-4 text-violet-400 shrink-0" />
                  <div className="text-left">
                    <p className="text-xs font-semibold text-slate-200">React 19 Tech Screen</p>
                    <p className="text-[10px] text-muted-foreground">July 10, 10:00 AM • AI Simulator</p>
                  </div>
                </div>
                <Button size="sm" variant="outline" className="text-[10px] h-7 px-2 cursor-pointer" onClick={() => (window.location.href = "/workspace?tab=interviews")}>
                  Prep
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Recent Notifications */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-bold">Recent Notifications</CardTitle>
                <Link href="/notification-center" className="text-xs text-primary hover:underline">
                  View All
                </Link>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {notifications.length === 0 ? (
                <p className="text-xs text-muted-foreground py-2 text-center">No notifications yet.</p>
              ) : (
                notifications.slice(0, 3).map((notif) => (
                  <div key={notif.id} className="p-3 border border-border bg-card/20 rounded-xl space-y-1">
                    <div className="flex justify-between text-[9px] text-muted-foreground font-semibold">
                      <span className="capitalize">{notif.category}</span>
                      <span>{notif.time}</span>
                    </div>
                    <p className="font-bold text-xs text-slate-200 truncate">{notif.title}</p>
                    <p className="text-[10px] text-muted-foreground line-clamp-1">{notif.description}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

// Client Routing Link Helper
function Link({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) {
  return (
    <a href={href} {...props}>
      {children}
    </a>
  );
}
