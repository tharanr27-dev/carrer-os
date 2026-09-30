"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, CheckCircle2, ExternalLink } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { EmptyState, ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { api } from "@/lib/api";
import { useNotificationStore } from "@/store/useNotificationStore";

export function TrainingAcademyView() {
  const queryClient = useQueryClient();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [role, setRole] = React.useState("");
  const [company, setCompany] = React.useState("");

  // The backend only exposes a roadmap once it is ACTIVE (404 while GENERATING), so after a
  // generate request keep polling until it shows up, or give up after a minute.
  const [waitingSince, setWaitingSince] = React.useState<number | null>(null);
  const [timedOut, setTimedOut] = React.useState(false);
  const roadmap = useQuery({
    queryKey: ["roadmap"],
    queryFn: api.activeRoadmap,
    refetchInterval: (query) => (waitingSince !== null || query.state.data?.status === "GENERATING" ? 2500 : false),
  });

  React.useEffect(() => {
    if (waitingSince === null) return;
    if (roadmap.data?.status === "ACTIVE" && roadmap.dataUpdatedAt > waitingSince) {
      setWaitingSince(null);
    } else if (Date.now() - waitingSince > 60_000) {
      setWaitingSince(null);
      setTimedOut(true);
    }
  }, [waitingSince, roadmap.data, roadmap.dataUpdatedAt]);

  const generate = useMutation({
    mutationFn: () => api.generateRoadmap({ target_role: role.trim() || undefined, target_company: company.trim() || undefined }),
    onSuccess: async () => {
      setTimedOut(false);
      setWaitingSince(Date.now());
      addNotification("learning", "Roadmap requested", "We are generating your personalised learning roadmap.", "/workspace?tab=academy");
      await queryClient.invalidateQueries({ queryKey: ["roadmap"] });
    },
  });

  const complete = useMutation({
    mutationFn: (taskId: string) => api.completeTask(taskId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["roadmap"] }),
        queryClient.invalidateQueries({ queryKey: ["student-dashboard"] }),
      ]);
    },
  });

  const data = roadmap.data;
  const tasks = data?.modules.flatMap((m) => m.tasks) ?? [];
  const done = tasks.filter((t) => t.status === "COMPLETED").length;

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
          <BookOpen className="h-7 w-7 text-primary" /> Training Academy
        </h1>
        <p className="text-sm text-muted-foreground">A personalised roadmap of modules and tasks toward your target role.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Generate a roadmap</CardTitle>
          <CardDescription className="text-xs">Creating a new one archives your current roadmap.</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col md:flex-row gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              generate.mutate();
            }}
          >
            <Input placeholder="Target role (e.g. Backend Engineer)" value={role} onChange={(e) => setRole(e.target.value)} />
            <Input placeholder="Target company (optional)" value={company} onChange={(e) => setCompany(e.target.value)} />
            <Button type="submit" isLoading={generate.isPending || waitingSince !== null || data?.status === "GENERATING"}>
              Generate
            </Button>
          </form>
          <ErrorBanner error={generate.error} className="mt-3" />
        </CardContent>
      </Card>

      <ErrorBanner error={complete.error} />

      {timedOut && <ErrorBanner error="Roadmap generation is taking longer than expected. Try generating again." />}

      {roadmap.isLoading ? (
        <LoadingBlock />
      ) : waitingSince !== null ? (
        <LoadingBlock label="Generating your roadmap…" />
      ) : roadmap.error ? (
        <ErrorBanner error={roadmap.error} onRetry={() => void roadmap.refetch()} />
      ) : !data ? (
        <EmptyState title="No roadmap yet" description="Enter a target role above to generate your first roadmap." />
      ) : data.status === "GENERATING" ? (
        <LoadingBlock label="Generating your roadmap…" />
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">{data.title}</CardTitle>
              <CardDescription className="text-xs">
                {[data.target_role, data.target_company].filter(Boolean).join(" @ ") || "General"} • v{data.version}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-1">
              <Progress value={tasks.length ? (done / tasks.length) * 100 : 0} indicatorClassName="bg-teal-500" />
              <p className="text-[11px] text-muted-foreground">
                {done} of {tasks.length} tasks complete
              </p>
            </CardContent>
          </Card>

          {data.modules.map((m) => (
            <Card key={m.id}>
              <CardHeader>
                <CardTitle className="text-sm font-bold">{m.title}</CardTitle>
                {m.description && <CardDescription className="text-xs">{m.description}</CardDescription>}
              </CardHeader>
              <CardContent className="space-y-2">
                {m.tasks.map((t) => {
                  const completed = t.status === "COMPLETED";
                  return (
                    <div key={t.id} className="flex items-start justify-between gap-3 p-3 rounded-xl border border-border">
                      <div className="space-y-0.5 min-w-0">
                        <p className={`text-xs font-semibold ${completed ? "line-through text-muted-foreground" : ""}`}>{t.title}</p>
                        {t.description && <p className="text-[11px] text-muted-foreground">{t.description}</p>}
                        <p className="text-[10px] text-muted-foreground">
                          {t.difficulty}
                          {t.estimated_minutes ? ` • ${t.estimated_minutes} min` : ""}
                          {t.resource_type ? ` • ${t.resource_type}` : ""}
                        </p>
                        {t.resource_url && (
                          <a href={t.resource_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[10px] text-primary hover:underline">
                            Open resource <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                      {completed ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" aria-label="Completed" />
                      ) : (
                        <Button size="sm" variant="outline" disabled={complete.isPending} onClick={() => complete.mutate(t.id)}>
                          Mark done
                        </Button>
                      )}
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          ))}
        </>
      )}
    </div>
  );
}
