"use client";

import React from "react";
import NextLink from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Target, X } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { EmptyState, ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { api } from "@/lib/api";

export function CareerJourneyView() {
  const queryClient = useQueryClient();
  const goals = useQuery({ queryKey: ["goals"], queryFn: api.listGoals });
  const roadmap = useQuery({ queryKey: ["roadmap"], queryFn: api.activeRoadmap });

  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [milestone, setMilestone] = React.useState("");
  const [milestones, setMilestones] = React.useState<string[]>([]);
  const [validation, setValidation] = React.useState<string | null>(null);

  const create = useMutation({
    mutationFn: () =>
      api.createGoal({
        title: title.trim(),
        description: description.trim() || undefined,
        milestones: milestones.map((m) => ({ title: m })),
      }),
    onSuccess: async () => {
      setTitle("");
      setDescription("");
      setMilestones([]);
      await queryClient.invalidateQueries({ queryKey: ["goals"] });
    },
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setValidation("Give your goal a title.");
      return;
    }
    setValidation(null);
    create.mutate();
  };

  const addMilestone = () => {
    const m = milestone.trim();
    if (m) setMilestones([...milestones, m]);
    setMilestone("");
  };

  const tasks = roadmap.data?.modules.flatMap((m) => m.tasks) ?? [];
  const done = tasks.filter((t) => t.status === "COMPLETED").length;

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Career Journey</h1>
        <p className="text-sm text-muted-foreground">Set goals with milestones and track your learning roadmap.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Target className="h-4 w-4 text-primary" /> Your Goals
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {goals.isLoading ? (
                <LoadingBlock />
              ) : goals.error ? (
                <ErrorBanner error={goals.error} onRetry={() => void goals.refetch()} />
              ) : !goals.data?.length ? (
                <EmptyState title="No goals yet" description="Create your first career goal on the right." />
              ) : (
                goals.data.map((g) => (
                  <div key={g.id} className="p-4 rounded-xl border border-border space-y-2">
                    <div className="flex justify-between items-start">
                      <p className="text-sm font-semibold">{g.title}</p>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-semibold">{g.status}</span>
                    </div>
                    {g.description && <p className="text-xs text-muted-foreground">{g.description}</p>}
                    {g.milestones.length > 0 && (
                      <ul className="text-xs space-y-1 list-disc pl-4 text-muted-foreground">
                        {g.milestones.map((m) => (
                          <li key={m.id}>{m.title}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">Learning Roadmap</CardTitle>
              <CardDescription className="text-xs">Progress on your active roadmap.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {roadmap.isLoading ? (
                <LoadingBlock />
              ) : !roadmap.data ? (
                <EmptyState
                  title="No roadmap yet"
                  action={
                    <NextLink href="/workspace?tab=academy">
                      <Button size="sm" variant="outline">
                        Generate a roadmap
                      </Button>
                    </NextLink>
                  }
                />
              ) : (
                <>
                  <p className="text-sm font-semibold">{roadmap.data.title}</p>
                  <Progress value={tasks.length ? (done / tasks.length) * 100 : 0} indicatorClassName="bg-teal-500" />
                  <p className="text-[11px] text-muted-foreground">
                    {done} of {tasks.length} tasks complete
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="lg:col-span-5 self-start">
          <CardHeader>
            <CardTitle className="text-base font-bold">New Goal</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-3">
              <ErrorBanner error={validation ?? create.error} />
              <Input placeholder="e.g. Land a backend internship" value={title} onChange={(e) => setTitle(e.target.value)} />
              <Input placeholder="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} />
              <div className="flex gap-2">
                <Input
                  placeholder="Add a milestone"
                  value={milestone}
                  onChange={(e) => setMilestone(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addMilestone();
                    }
                  }}
                />
                <Button type="button" variant="outline" size="icon" onClick={addMilestone} aria-label="Add milestone">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {milestones.length > 0 && (
                <ul className="space-y-1">
                  {milestones.map((m, i) => (
                    <li key={`${m}-${i}`} className="flex items-center justify-between text-xs rounded-md bg-muted/40 px-2 py-1">
                      {m}
                      <button type="button" aria-label={`Remove ${m}`} onClick={() => setMilestones(milestones.filter((_, j) => j !== i))}>
                        <X className="h-3 w-3" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <Button type="submit" className="w-full" isLoading={create.isPending}>
                Create goal
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
