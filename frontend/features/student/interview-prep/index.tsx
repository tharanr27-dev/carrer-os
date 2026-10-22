"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { GraduationCap } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, TrainingAction, TrainingAttemptCreate } from "@/lib/api";
import { ProgressHistory, RoadmapHome } from "./home";
import { RoundPractice } from "./round-practice";
import { MockSetup, ResumeProjects } from "./resume-mock";
import { AttemptRunner } from "./runner";

export const PREP_TABS = [
  { value: "roadmap", label: "My Roadmap" },
  { value: "aptitude", label: "Aptitude" },
  { value: "technical", label: "Technical" },
  { value: "coding", label: "Coding" },
  { value: "communication", label: "Communication Lab" },
  { value: "hr", label: "HR & Final Round" },
  { value: "resume", label: "Resume & Projects" },
  { value: "mock", label: "Mock Interview" },
  { value: "progress", label: "Performance" },
] as const;

export function InterviewPreparationView({ tab, onTabChange }: { tab: string; onTabChange: (t: string) => void }) {
  const qc = useQueryClient();
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const meta = useQuery({ queryKey: ["training-meta"], queryFn: api.trainingMeta, staleTime: 5 * 60_000, retry: false });

  const start = useMutation({
    mutationFn: (body: TrainingAttemptCreate) => api.trainingStart(body),
    onSuccess: (attempt) => {
      qc.setQueryData(["training-attempt", attempt.id], attempt);
      setActiveId(attempt.id);
    },
  });

  const exit = () => {
    setActiveId(null);
    start.reset();
    void qc.invalidateQueries({ queryKey: ["training-progress"] });
    void qc.invalidateQueries({ queryKey: ["training-history"] });
    void qc.invalidateQueries({ queryKey: ["training-meta"] });
  };

  const openAttempt = (id: string) => {
    void qc.invalidateQueries({ queryKey: ["training-attempt", id] });
    setActiveId(id);
  };

  const runAction = (a: TrainingAction["action"]) => {
    if (a.type === "mock") {
      setActiveId(null);
      onTabChange("mock");
      return;
    }
    setActiveId(null);
    start.mutate({ mode: a.mode ?? "practice", round: a.round, topic: a.topic ?? null, difficulty: a.difficulty ?? null, count: 10 });
  };

  const common = {
    meta: meta.data,
    loading: meta.isLoading,
    error: meta.error,
    onRetry: () => void meta.refetch(),
    onStart: (b: TrainingAttemptCreate) => start.mutate(b),
    starting: start.isPending,
    startError: start.error,
  };

  return (
    <div className="space-y-5">
      <div>
        <div className="mb-1 flex items-center gap-2 text-primary">
          <GraduationCap className="h-5 w-5" aria-hidden="true" />
          <span className="text-xs font-semibold uppercase tracking-wide">Placement training</span>
        </div>
        <h1 className="text-2xl font-extrabold tracking-tight">Interview Preparation</h1>
        <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
          Work through aptitude, technical, coding, communication, HR and final rounds, then rehearse a full mock interview. Everything shown here comes from your saved practice.
        </p>
        {meta.data && !meta.data.ai_available && meta.data.ai_note && (
          <p className="mt-2 max-w-3xl rounded-md border bg-muted/30 p-2 text-[11px] text-muted-foreground">{meta.data.ai_note}</p>
        )}
      </div>

      {activeId ? (
        <AttemptRunner attemptId={activeId} onExit={exit} onAction={runAction} />
      ) : (
        <Tabs value={tab} onValueChange={onTabChange}>
          <TabsList className="flex h-auto w-full flex-wrap justify-start gap-1 bg-muted/30 p-1 dark:bg-slate-950/40">
            {PREP_TABS.map((t) => (
              <TabsTrigger key={t.value} value={t.value} className="text-xs">{t.label}</TabsTrigger>
            ))}
          </TabsList>
          <div className="pt-4">
            <TabsContent value="roadmap">
              <RoadmapHome meta={meta.data} onAction={runAction} onOpenAttempt={openAttempt} onGo={onTabChange} />
            </TabsContent>
            <TabsContent value="aptitude">
              <RoundPractice {...common} rounds={["aptitude"]} allowExam intro="Quantitative, logical, verbal and technical-screening MCQs. Practice mode explains each answer immediately; exam mode is timed and reveals answers after you submit." />
            </TabsContent>
            <TabsContent value="technical">
              <RoundPractice {...common} rounds={["technical"]} allowExam intro="Programming languages, computer science, development and AI topics. Pick only what you need." />
            </TabsContent>
            <TabsContent value="coding">
              <RoundPractice {...common} rounds={["coding"]} intro="Problem-solving patterns with hints, test cases and reference solutions. Your code is NOT run by this platform: you mark yourself against the listed test cases." />
            </TabsContent>
            <TabsContent value="communication">
              <RoundPractice {...common} rounds={["communication"]} intro="Text-based speaking and writing practice: introductions, explaining concepts simply, workplace messages and difficult questions. Clarity, structure and relevance are assessed. Accent and regional English are not." />
            </TabsContent>
            <TabsContent value="hr">
              <RoundPractice {...common} rounds={["hr", "managerial"]} intro="HR, behavioural and managerial questions. Use your own real experiences; the model answers show structure, not scripts to memorise." />
            </TabsContent>
            <TabsContent value="resume">
              <ResumeProjects onStart={(b) => start.mutate(b)} starting={start.isPending} startError={start.error} />
            </TabsContent>
            <TabsContent value="mock">
              <MockSetup meta={meta.data} onStart={(b) => start.mutate(b)} starting={start.isPending} startError={start.error} />
            </TabsContent>
            <TabsContent value="progress">
              <ProgressHistory onOpenAttempt={openAttempt} />
            </TabsContent>
          </div>
        </Tabs>
      )}
    </div>
  );
}
