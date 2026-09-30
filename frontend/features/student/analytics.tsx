"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download, FileText, Target, TrendingUp, Trophy, Mic } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { api } from "@/lib/api";

function downloadCsv(filename: string, rows: (string | number)[][]) {
  const csv = rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function AnalyticsView() {
  const dashboard = useQuery({ queryKey: ["student-dashboard"], queryFn: api.studentDashboard });
  const roadmap = useQuery({ queryKey: ["roadmap"], queryFn: api.activeRoadmap });
  const feed = useQuery({ queryKey: ["recommendations"], queryFn: api.recommendationFeed });

  // Recharts needs a client-side mount to measure its container.
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);

  // Record that the analytics view was opened (POST /analytics/events); failures must not affect the UI.
  React.useEffect(() => {
    void api.logEvent({ event_type: "PAGE_VIEWED", module: "analytics" }).catch(() => undefined);
  }, []);

  const stats = dashboard.data;
  const modules = roadmap.data?.modules ?? [];
  const moduleProgress = modules.map((m) => ({
    name: m.title.length > 18 ? `${m.title.slice(0, 17)}…` : m.title,
    progress: m.tasks.length ? Math.round((m.tasks.filter((t) => t.status === "COMPLETED").length / m.tasks.length) * 100) : 0,
  }));

  const byCategory = Object.entries(
    (feed.data?.recommendations ?? []).reduce<Record<string, number>>((acc, r) => {
      acc[r.category] = (acc[r.category] ?? 0) + 1;
      return acc;
    }, {})
  ).map(([category, count]) => ({ category, count }));

  const exportSnapshot = () => {
    if (!stats) return;
    downloadCsv("careeros-analytics-snapshot.csv", [
      ["Metric", "Value"],
      ["Career readiness", stats.career_readiness],
      ["Resume (ATS) score", stats.resume_score],
      ["Interview score", stats.interview_score],
      ["Interviews today", stats.today_interviews],
      ["Learning tasks today", stats.today_tasks],
      ["ATS score delta", stats.trends.ats_score_delta],
      ["Interview score delta", stats.trends.interview_score_delta],
      ...moduleProgress.map((m) => [`Roadmap module: ${m.name}`, `${m.progress}%`]),
    ]);
  };

  const metrics = [
    { label: "Career Readiness", value: stats?.career_readiness ?? 0, icon: Target },
    { label: "ATS Resume Score", value: stats?.resume_score ?? 0, icon: FileText },
    { label: "Interview Score", value: stats?.interview_score ?? 0, icon: Mic },
  ];

  return (
    <div className="space-y-6 text-left">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-primary">
            <TrendingUp className="h-3.5 w-3.5" />
            Career Insights Center
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Analytics</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">Your readiness scores and learning progress, computed from your activity.</p>
        </div>
        <Button className="gap-2 shrink-0" onClick={exportSnapshot} disabled={!stats}>
          <Download className="h-4 w-4" /> Download Snapshot (CSV)
        </Button>
      </div>

      <ErrorBanner error={dashboard.error} onRetry={() => void dashboard.refetch()} />

      {dashboard.isLoading ? (
        <LoadingBlock />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {metrics.map((m) => {
            const Icon = m.icon;
            return (
              <Card key={m.label}>
                <CardContent className="p-5 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-semibold text-muted-foreground uppercase">{m.label}</span>
                    <div className="p-2 bg-primary/10 text-primary rounded-lg">
                      <Icon className="h-4 w-4" />
                    </div>
                  </div>
                  <p className="text-2xl font-bold">{Math.round(m.value)}</p>
                  <Progress value={m.value} indicatorClassName="bg-primary" />
                </CardContent>
              </Card>
            );
          })}
          <Card>
            <CardContent className="p-5 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-semibold text-muted-foreground uppercase">Today</span>
                <div className="p-2 bg-primary/10 text-primary rounded-lg">
                  <Trophy className="h-4 w-4" />
                </div>
              </div>
              <p className="text-sm">
                <span className="text-2xl font-bold">{stats?.today_tasks ?? 0}</span> tasks
              </p>
              <p className="text-xs text-muted-foreground">{stats?.today_interviews ?? 0} interviews completed</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Roadmap Progress</CardTitle>
            <CardDescription className="text-xs">Completion by module (%)</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            {roadmap.isLoading ? (
              <LoadingBlock />
            ) : moduleProgress.length === 0 ? (
              <EmptyState title="No roadmap yet" description="Generate one in the Training Academy." />
            ) : mounted ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={moduleProgress}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="name" fontSize={11} />
                  <YAxis domain={[0, 100]} fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="progress" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Recommendations by Category</CardTitle>
            <CardDescription className="text-xs">From your AI recommendation feed</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            {feed.isLoading ? (
              <LoadingBlock />
            ) : byCategory.length === 0 ? (
              <EmptyState title="No recommendations yet" description="Refresh recommendations from your dashboard." />
            ) : mounted ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byCategory}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="category" fontSize={11} />
                  <YAxis allowDecimals={false} fontSize={11} />
                  <Tooltip />
                  <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
