"use client";

import React from "react";
import NextLink from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from "@/components/ui/feedback";
import { useAuthStore } from "@/store/useAuthStore";
import { useNotificationStore } from "@/store/useNotificationStore";
import { api } from "@/lib/api";
import {
  ArrowRight,
  Bot,
  BookOpen,
  Briefcase,
  CheckCircle2,
  Compass,
  FileCheck,
  FileText,
  GraduationCap,
  MessageSquareText,
  Mic,
  RefreshCw,
  Sparkles,
  Target,
  Trophy,
  Zap,
} from "lucide-react";
import { motion } from "framer-motion";

const navCards = [
  { label: "Career Journey", desc: "View timelines & milestones", href: "/workspace?tab=careers", icon: GraduationCap, color: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20" },
  { label: "AI Interview", desc: "Simulate live mock screenings", href: "/workspace?tab=interviews", icon: Mic, color: "text-violet-400 bg-violet-500/10 border-violet-500/20" },
  { label: "Learning Center", desc: "Start structured lessons", href: "/workspace?tab=academy", icon: BookOpen, color: "text-teal-400 bg-teal-500/10 border-teal-500/20" },
  { label: "Jobs", desc: "Search matching openings", href: "/jobs", icon: Briefcase, color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
  { label: "Resume Center", desc: "Scan and optimize CV scores", href: "/workspace?tab=resume", icon: FileText, color: "text-sky-400 bg-sky-500/10 border-sky-500/20" },
  { label: "AI Mentor", desc: "Access persistent conversation", href: "/workspace?tab=mentor", icon: Bot, color: "text-pink-400 bg-pink-500/10 border-pink-500/20" },
  { label: "Communication Coach", desc: "Analyze grammar & tone", href: "/workspace?tab=communication", icon: MessageSquareText, color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
  { label: "Career Discovery", desc: "Take the career assessment", href: "/workspace?tab=discovery", icon: Compass, color: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
  { label: "Progress", desc: "View learning benchmarks", href: "/analytics", icon: Target, color: "text-rose-400 bg-rose-500/10 border-rose-500/20" },
];

function delta(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)} vs last period`;
}

export default function StudentDashboard() {
  const { user } = useAuthStore();
  const { notifications, addNotification } = useNotificationStore();
  const queryClient = useQueryClient();
  const [message, setMessage] = React.useState<string | null>(null);

  const dashboard = useQuery({ queryKey: ["student-dashboard"], queryFn: api.studentDashboard });
  const roadmap = useQuery({ queryKey: ["roadmap"], queryFn: api.activeRoadmap });
  const feed = useQuery({ queryKey: ["recommendations"], queryFn: api.recommendationFeed });
  const jobs = useQuery({ queryKey: ["open-jobs"], queryFn: api.openJobs });

  const complete = useMutation({
    mutationFn: (taskId: string) => api.completeTask(taskId),
    onSuccess: async () => {
      addNotification("learning", "Task completed", "Nice work, your learning streak has been updated.", "/workspace?tab=academy");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["roadmap"] }),
        queryClient.invalidateQueries({ queryKey: ["student-dashboard"] }),
      ]);
    },
  });

  const refreshRecs = useMutation({
    mutationFn: api.refreshRecommendations,
    onSuccess: () => {
      setMessage("Generating recommendations. They will appear here in a few seconds.");
      // Generation is asynchronous on the backend (202): poll the feed shortly after.
      [2500, 6000].forEach((ms) => setTimeout(() => void queryClient.invalidateQueries({ queryKey: ["recommendations"] }), ms));
    },
  });

  const feedback = useMutation({
    mutationFn: (v: { id: string; action: string }) => api.recommendationFeedback(v.id, v.action),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["recommendations"] }),
  });

  const firstName = user?.name.trim().split(/\s+/)[0] || "there";
  const stats = dashboard.data;

  const allTasks = roadmap.data?.modules.flatMap((m) => m.tasks) ?? [];
  const doneTasks = allTasks.filter((t) => t.status === "COMPLETED").length;
  const learningPct = allTasks.length ? Math.round((doneTasks / allTasks.length) * 100) : 0;
  const pendingTasks = allTasks.filter((t) => t.status !== "COMPLETED").slice(0, 4);

  return (
    <div className="space-y-8 text-left">
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
              {stats
                ? `Your career readiness is ${Math.round(stats.career_readiness)}%. Keep going with today's learning tasks.`
                : "Your live career metrics appear below as you use the platform."}
            </p>
          </div>
          <NextLink href="/workspace?tab=discovery">
            <Button className="bg-background/90 text-foreground hover:bg-background font-semibold shrink-0 border border-border shadow-sm">
              Launch Career Planner
            </Button>
          </NextLink>
        </div>
        <div className="absolute right-0 top-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />
      </motion.div>

      <ErrorBanner error={dashboard.error} onRetry={() => void dashboard.refetch()} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider">Career Readiness</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center pt-2">
            {dashboard.isLoading ? (
              <LoadingBlock label="" className="py-6" />
            ) : (
              <>
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
                      strokeDashoffset={`${2 * Math.PI * 40 * (1 - (stats?.career_readiness ?? 0) / 100)}`}
                    />
                  </svg>
                  <span className="absolute text-xl font-bold">{Math.round(stats?.career_readiness ?? 0)}%</span>
                </div>
                <p className="text-xs text-muted-foreground text-center mt-3 font-medium">
                  {stats && stats.career_readiness > 0 ? "Based on your activity" : "No activity scored yet"}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider">ATS Resume Score</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{Math.round(stats?.resume_score ?? 0)}/100</span>
              <FileCheck className="h-5 w-5 text-indigo-400" />
            </div>
            <div className="space-y-1">
              <Progress value={stats?.resume_score ?? 0} indicatorClassName="bg-indigo-500" />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>Resume strength</span>
                <span className="font-semibold">{stats ? delta(stats.trends.ats_score_delta) : "—"}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider">Learning Progress</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{learningPct}%</span>
              <BookOpen className="h-5 w-5 text-teal-400" />
            </div>
            <div className="space-y-1">
              <Progress value={learningPct} indicatorClassName="bg-teal-500" />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span className="truncate">{roadmap.data?.title ?? "No roadmap yet"}</span>
                <span>{allTasks.length ? `${allTasks.length - doneTasks} tasks left` : ""}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider">Interview Score</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{Math.round(stats?.interview_score ?? 0)}/100</span>
              <Trophy className="h-5 w-5 text-amber-400" />
            </div>
            <div className="space-y-1">
              <Progress value={stats?.interview_score ?? 0} indicatorClassName="bg-amber-500" />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>Today: {stats?.today_interviews ?? 0} interviews, {stats?.today_tasks ?? 0} tasks</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                  <NextLink key={card.label} href={card.href} className="w-full">
                    <div className="flex flex-col items-start p-4 border border-border bg-card/40 hover:bg-primary/5 hover:border-primary/30 transition-all rounded-xl text-left group h-full justify-between">
                      <div className={`p-2.5 rounded-lg border ${card.color} shrink-0 mb-3`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="space-y-1">
                        <p className="font-semibold text-xs group-hover:text-primary transition-colors">{card.label}</p>
                        <p className="text-[10px] text-muted-foreground leading-normal">{card.desc}</p>
                      </div>
                    </div>
                  </NextLink>
                );
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold">AI Recommendations</CardTitle>
                  <CardDescription className="text-xs">Ranked next steps generated from your platform activity.</CardDescription>
                </div>
                <Button size="sm" variant="outline" isLoading={refreshRecs.isPending} onClick={() => refreshRecs.mutate()} className="gap-1">
                  {!refreshRecs.isPending && <RefreshCw className="h-3.5 w-3.5" />}
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <SuccessBanner message={message} />
              <ErrorBanner error={refreshRecs.error ?? feedback.error ?? feed.error} onRetry={() => void feed.refetch()} />
              {feed.isLoading ? (
                <LoadingBlock />
              ) : !feed.data ? (
                <EmptyState
                  title="No recommendations yet"
                  description="Press Refresh to generate your first personalised feed."
                />
              ) : (
                feed.data.recommendations.slice(0, 5).map((rec) => (
                  <div key={rec.id} className="p-4 border border-border bg-card/30 rounded-xl space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-xs">{rec.title}</p>
                        <p className="text-[10px] text-muted-foreground">
                          {rec.category} • {rec.difficulty}
                        </p>
                      </div>
                      <span className="rounded-full bg-primary/20 text-primary border border-primary/20 px-2 py-0.5 text-[10px] font-bold whitespace-nowrap">
                        {Math.round(rec.confidence_score * 100)}% confidence
                      </span>
                    </div>
                    {rec.description && <p className="text-[11px] text-muted-foreground">{rec.description}</p>}
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" className="h-7 text-[10px]" disabled={feedback.isPending} onClick={() => feedback.mutate({ id: rec.id, action: "ACCEPTED" })}>
                        Accept
                      </Button>
                      <Button size="sm" variant="ghost" className="h-7 text-[10px]" disabled={feedback.isPending} onClick={() => feedback.mutate({ id: rec.id, action: "DISMISSED" })}>
                        Dismiss
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold">Open Jobs</CardTitle>
                  <CardDescription className="text-xs">Latest openings from hiring companies.</CardDescription>
                </div>
                <NextLink href="/jobs" className="text-xs text-primary hover:underline font-semibold flex items-center gap-1">
                  View All <ArrowRight className="h-3.5 w-3.5" />
                </NextLink>
              </div>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {jobs.isLoading ? (
                <LoadingBlock />
              ) : jobs.error ? (
                <ErrorBanner error={jobs.error} onRetry={() => void jobs.refetch()} />
              ) : jobs.data?.length ? (
                jobs.data.slice(0, 4).map((job) => (
                  <div key={job.id} className="p-4 border border-border bg-card/30 rounded-xl space-y-0.5">
                    <p className="font-semibold text-xs">{job.title}</p>
                    <p className="text-[10px] text-muted-foreground">
                      {job.company_name ?? "Company"} {job.location ? `• ${job.location}` : ""}
                    </p>
                  </div>
                ))
              ) : (
                <EmptyState className="md:col-span-2" title="No open jobs yet" description="Recruiters have not posted any openings." />
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="border-indigo-500/10 bg-gradient-to-b from-indigo-500/5 to-transparent">
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Sparkles className="h-4.5 w-4.5 text-indigo-400" /> Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2.5 text-xs">
              <NextLink href="/workspace?tab=resume" className="block">
                <Button className="w-full text-xs justify-start gap-2" variant="outline">
                  <FileCheck className="h-4 w-4 text-sky-400" /> Optimize ATS Score
                </Button>
              </NextLink>
              <NextLink href="/workspace?tab=interviews" className="block">
                <Button className="w-full text-xs justify-start gap-2" variant="outline">
                  <Zap className="h-4 w-4 text-violet-400" /> Launch Interview Room
                </Button>
              </NextLink>
              <NextLink href="/workspace?tab=mentor" className="block">
                <Button className="w-full text-xs justify-start gap-2" variant="outline">
                  <Bot className="h-4 w-4 text-pink-400" /> Consult AI Mentor
                </Button>
              </NextLink>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">Today&apos;s Tasks</CardTitle>
              <CardDescription className="text-xs">Next steps from your learning roadmap</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <ErrorBanner error={complete.error ?? roadmap.error} onRetry={() => void roadmap.refetch()} />
              {roadmap.isLoading ? (
                <LoadingBlock />
              ) : !roadmap.data ? (
                <EmptyState title="No roadmap yet" description="Generate one from the Learning Center to see tasks here." action={
                  <NextLink href="/workspace?tab=academy"><Button size="sm" variant="outline">Create roadmap</Button></NextLink>
                } />
              ) : roadmap.data.status === "GENERATING" ? (
                <LoadingBlock label="Your roadmap is being generated…" />
              ) : pendingTasks.length === 0 ? (
                <EmptyState title="All caught up" description="Every task in your roadmap is complete." />
              ) : (
                pendingTasks.map((task) => (
                  <button
                    key={task.id}
                    disabled={complete.isPending}
                    onClick={() => complete.mutate(task.id)}
                    className="w-full flex items-start gap-3 p-3 border rounded-xl text-left transition-all bg-muted/40 border-muted hover:border-primary/40 disabled:opacity-50"
                  >
                    <CheckCircle2 className="h-4.5 w-4.5 shrink-0 mt-0.5 text-muted-foreground" />
                    <span className="text-[11px] leading-normal font-semibold">{task.title}</span>
                  </button>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-bold">Recent Notifications</CardTitle>
                <NextLink href="/notification-center" className="text-xs text-primary hover:underline">
                  View All
                </NextLink>
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
                    <p className="font-bold text-xs truncate">{notif.title}</p>
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
