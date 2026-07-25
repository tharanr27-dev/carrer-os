"use client";

import React, { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  TrendingUp,
  Target,
  Trophy,
  Star,
  Download,
  Mic,
  Volume2,
  BookOpen,
  FileText,
  Calendar,
  Sparkles,
  Award,
  ChevronRight,
  ShieldCheck,
  CheckCircle,
} from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { motion } from "framer-motion";

// Mock Data
const progressSeries = [
  { week: "Wk 1", career: 60, technical: 55, applications: 1, learning: 2, communication: 70, interview: 65 },
  { week: "Wk 2", career: 65, technical: 60, applications: 3, learning: 4, communication: 73, interview: 68 },
  { week: "Wk 3", career: 72, technical: 65, applications: 2, learning: 5, communication: 75, interview: 72 },
  { week: "Wk 4", career: 78, technical: 70, applications: 4, learning: 8, communication: 82, interview: 82 },
];

const skillGapData = [
  { subject: "React/Next.js", current: 80, target: 90 },
  { subject: "TypeScript", current: 75, target: 85 },
  { subject: "System Design", current: 40, target: 80 },
  { subject: "Data Structures", current: 65, target: 85 },
  { subject: "CI/CD & DevOps", current: 30, target: 70 },
  { subject: "Communication", current: 85, target: 90 },
];

const timelineMilestones = [
  { step: "01", role: "Junior Front-End Developer", timeline: "Years 0–1 (Current)", status: "Completed", desc: "Focus on UI fidelity, responsive web layouts, and state management logic." },
  { step: "02", role: "Full-Stack Software Engineer", timeline: "Years 1–3 (Target)", status: "Active Prep", desc: "Take ownership of full-stack data routes, backend optimization, and caching." },
  { step: "03", role: "Lead Frontend Architect", timeline: "Years 3–5 (Long-Term)", status: "Future Goal", desc: "Lead engineering projects, define structural layouts, and manage core platforms." },
];

function AnalyticsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [isMounted, setIsMounted] = React.useState(false);

  React.useEffect(() => {
    setIsMounted(true);
  }, []);

  const tabParam = searchParams.get("tab") || "overview";

  const handleTabChange = (value: string) => {
    const params = new URLSearchParams(window.location.search);
    params.set("tab", value);
    router.push(`/analytics?${params.toString()}`);
  };

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-primary">
            <TrendingUp className="h-3.5 w-3.5" />
            Career Insights Center
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Analytics</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Monitor Career Readiness scores, interview diagnostics, communication speeds, achievements, and download summaries.
          </p>
        </div>
        <Button className="cursor-pointer gap-2 shrink-0">
          <Download className="h-4 w-4" /> Download Snapshot
        </Button>
      </div>

      <Tabs defaultValue="overview" value={tabParam} onValueChange={handleTabChange} className="w-full">
        <TabsList className="mb-6 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30 dark:bg-slate-950/40">
          <TabsTrigger value="overview" className="text-xs">Career Readiness & Progress</TabsTrigger>
          <TabsTrigger value="charts" className="text-xs">Performance Charts</TabsTrigger>
          <TabsTrigger value="interview" className="text-xs">Interview & Communication</TabsTrigger>
          <TabsTrigger value="timeline" className="text-xs">Learning & Timeline</TabsTrigger>
          <TabsTrigger value="reports" className="text-xs">Reports Center</TabsTrigger>
        </TabsList>

        {/* Tab 1: Career Progress & Readiness */}
        <TabsContent value="overview" className="space-y-6">
          {/* Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { label: "Career Readiness", value: "84%", desc: "Ready for Junior Roles", icon: Target, progress: 84 },
              { label: "ATS Resume Match", value: "87 pts", desc: "ATS Optimized version", icon: FileText, progress: 87 },
              { label: "Speech Confidence", value: "82%", desc: "Daily practice active", icon: Volume2, progress: 82 },
              { label: "Learning Streak", value: "21 Days", desc: "14 lesson milestones", icon: Trophy, progress: 70 },
            ].map((metric) => {
              const Icon = metric.icon;
              return (
                <Card key={metric.label}>
                  <CardContent className="p-5 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-semibold text-muted-foreground uppercase">{metric.label}</span>
                      <div className="p-2 bg-primary/10 text-primary rounded-lg">
                        <Icon className="h-4 w-4" />
                      </div>
                    </div>
                    <div>
                      <p className="text-2xl font-bold">{metric.value}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">{metric.desc}</p>
                    </div>
                    <Progress value={metric.progress} indicatorClassName="bg-primary" />
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold">Career Progress Overview</CardTitle>
                <CardDescription className="text-xs">Track your aggregate progress score milestones across components.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="space-y-2">
                  <div className="flex justify-between font-semibold">
                    <span>Technical Knowledge Gap</span>
                    <span className="text-emerald-500">Close to Target</span>
                  </div>
                  <Progress value={80} indicatorClassName="bg-primary" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between font-semibold">
                    <span>Mock Interview Pass Rate</span>
                    <span className="text-amber-500">Needs Practice</span>
                  </div>
                  <Progress value={65} indicatorClassName="bg-amber-500" />
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between font-semibold">
                    <span>Resume Optimization Index</span>
                    <span className="text-emerald-500">Fully Optimized</span>
                  </div>
                  <Progress value={90} indicatorClassName="bg-emerald-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold">Career Readiness Checklist</CardTitle>
                <CardDescription className="text-xs">Complete items to increase recruiter placement matchmaking compatibility.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                {[
                  { label: "Upload ATS optimized resume draft (v2.0)", done: true },
                  { label: "Pass Next.js advanced structures test", done: true },
                  { label: "Achieve speech rate between 130-150 wpm", done: false },
                  { label: "Complete CDN system design mock interview", done: false },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-2 bg-muted/20 border border-border rounded-xl">
                    <CheckCircle className={`h-4.5 w-4.5 shrink-0 ${item.done ? "text-emerald-500" : "text-muted-foreground opacity-50"}`} />
                    <span className={`font-semibold ${item.done ? "text-slate-300" : "text-muted-foreground"}`}>{item.label}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 2: Performance Charts */}
        <TabsContent value="charts" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold">Weekly Performance Trend</CardTitle>
                <CardDescription className="text-xs">Aggregated career readiness points earned day-by-day</CardDescription>
              </CardHeader>
              <CardContent className="h-72">
                {isMounted ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={progressSeries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="analyticsGlow" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="week" stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                      <YAxis stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                      <Tooltip
                        contentStyle={{
                          background: "hsl(var(--card))",
                          borderColor: "hsl(var(--border))",
                          borderRadius: "8px",
                          fontSize: "12px",
                        }}
                      />
                      <Area type="monotone" dataKey="career" stroke="hsl(var(--primary))" strokeWidth={2} fillOpacity={1} fill="url(#analyticsGlow)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full w-full bg-muted/20 animate-pulse rounded-lg" />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold">Applications & Learning Momentum</CardTitle>
                <CardDescription className="text-xs">Weekly job application velocity against lessons completed.</CardDescription>
              </CardHeader>
              <CardContent className="h-72">
                {isMounted ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={progressSeries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                      <XAxis dataKey="week" stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                      <YAxis stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                      <Tooltip
                        contentStyle={{
                          background: "hsl(var(--card))",
                          borderColor: "hsl(var(--border))",
                          borderRadius: "8px",
                          fontSize: "12px",
                        }}
                      />
                      <Bar dataKey="applications" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Applications" />
                      <Bar dataKey="learning" fill="#14b8a6" radius={[4, 4, 0, 0]} name="Lessons Completed" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full w-full bg-muted/20 animate-pulse rounded-lg" />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 3: Interview & Communication */}
        <TabsContent value="interview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold">Interview Diagnostics</CardTitle>
                <CardDescription className="text-xs">Current capability indexes compared with peer demands.</CardDescription>
              </CardHeader>
              <CardContent className="h-72 flex items-center justify-center">
                {isMounted ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={skillGapData}>
                      <PolarGrid stroke="rgba(255,255,255,0.05)" />
                      <PolarAngleAxis dataKey="subject" stroke="#888888" fontSize={9} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#888888" fontSize={8} />
                      <Radar name="Your level" dataKey="current" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.2} />
                      <Radar name="Target Demand" dataKey="target" stroke="rgba(255,255,255,0.3)" fill="none" />
                      <Tooltip />
                    </RadarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full w-full bg-muted/20 animate-pulse rounded-lg" />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold">Speech & Voice Diagnostics</CardTitle>
                <CardDescription className="text-xs">Fluent patterns compiled from Communication Coach simulations.</CardDescription>
              </CardHeader>
              <CardContent className="h-72">
                {isMounted ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={progressSeries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                      <XAxis dataKey="week" stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                      <YAxis stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                      <Tooltip
                        contentStyle={{
                          background: "hsl(var(--card))",
                          borderColor: "hsl(var(--border))",
                          borderRadius: "8px",
                          fontSize: "12px",
                        }}
                      />
                      <Line type="monotone" dataKey="communication" stroke="#14b8a6" strokeWidth={3} name="Speech score" />
                      <Line type="monotone" dataKey="interview" stroke="#8b5cf6" strokeWidth={3} name="Interview score" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full w-full bg-muted/20 animate-pulse rounded-lg" />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 4: Learning & Timeline */}
        <TabsContent value="timeline" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Timeline */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base font-bold">Career Timeline Milestones</CardTitle>
                <CardDescription className="text-xs">Chronological roadmap tracking achievements and targets.</CardDescription>
              </CardHeader>
              <CardContent className="relative pl-8 space-y-6 before:absolute before:left-[15px] before:top-2 before:bottom-2 before:w-[1.5px] before:bg-border">
                {timelineMilestones.map((m) => (
                  <div key={m.step} className="relative text-left">
                    <span className="absolute -left-[28px] top-0 h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-bold border bg-card text-muted-foreground border-border">
                      {m.step}
                    </span>
                    <div className="pl-2 space-y-1">
                      <div className="flex justify-between items-center">
                        <h4 className="text-xs font-bold text-slate-200">{m.role}</h4>
                        <span className="text-[9px] font-semibold border border-muted bg-muted/40 rounded-sm px-2 py-0.5">{m.status}</span>
                      </div>
                      <p className="text-[9px] text-muted-foreground">{m.timeline}</p>
                      <p className="text-[11px] text-muted-foreground leading-normal">{m.desc}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Achievements Grid */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold">Earned Badges & Achievements</CardTitle>
                <CardDescription className="text-xs">Trophies compiled from course completions.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4 pt-2">
                {[
                  { name: "Resume Pro", desc: "ATS 85+ score", icon: Trophy, color: "text-amber-400" },
                  { name: "Clean Coder", desc: "TS fundamentals", icon: Award, color: "text-sky-400" },
                  { name: "Speech Ace", desc: "Streak 14 days", icon: Trophy, color: "text-emerald-400" },
                  { name: "Ready Screen", desc: "Pass Tech Screen", icon: ShieldCheck, color: "text-violet-400" },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <div key={item.name} className="p-3 border border-border bg-card/20 rounded-xl flex flex-col items-center justify-center text-center space-y-2">
                      <Icon className={`h-8 w-8 ${item.color}`} />
                      <div>
                        <p className="font-bold text-[10px] text-slate-200">{item.name}</p>
                        <p className="text-[9px] text-muted-foreground">{item.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 5: Reports */}
        <TabsContent value="reports" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold">Downloadable Report Briefs</CardTitle>
                  <CardDescription className="text-xs">AI-synthesized diagnostic PDF files ready for recruiters.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    { name: "Overall Career Readiness Report", date: "Generated Jul 6, 2026", size: "1.2 MB" },
                    { name: "Speech & Fluency Diagnostic Summary", date: "Generated Jul 3, 2026", size: "0.8 MB" },
                    { name: "Technical Interview Screen Transcripts", date: "Generated Jun 29, 2026", size: "2.4 MB" },
                  ].map((rep) => (
                    <div key={rep.name} className="flex items-center justify-between p-3.5 bg-card/30 border border-border rounded-xl">
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-primary" />
                        <div className="text-left">
                          <p className="font-semibold text-xs text-slate-200">{rep.name}</p>
                          <p className="text-[9px] text-muted-foreground mt-0.5">{rep.date}</p>
                        </div>
                      </div>
                      <Button size="sm" variant="outline" className="gap-1.5 text-xs font-semibold cursor-pointer">
                        <Download className="h-3.5 w-3.5" /> Download
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            <Card className="bg-secondary text-secondary-foreground border-2 border-border">
              <CardContent className="p-6 flex flex-col justify-between h-full space-y-6">
                <div>
                  <p className="text-[9px] font-bold uppercase tracking-wider text-slate-400">PDF Document Preview</p>
                  <h3 className="text-xl font-bold mt-2">CareerOS Assessment Statement</h3>
                  <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                    A certified layout including score distributions, ATS keyword gaps matched, speech counts, and executive placement compatibility details.
                  </p>
                </div>
                <div className="flex justify-between items-center pt-4 border-t border-slate-200">
                  <div>
                    <p className="text-2xl font-bold">86%</p>
                    <p className="text-[10px] text-slate-400">Overall score</p>
                  </div>
                  <Button size="sm" className="bg-slate-950 text-white hover:bg-slate-900 cursor-pointer">Export PDF</Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-[400px] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      }
    >
      <SuspenseWrapper />
    </Suspense>
  );
}

function SuspenseWrapper() {
  return <AnalyticsContent />;
}
