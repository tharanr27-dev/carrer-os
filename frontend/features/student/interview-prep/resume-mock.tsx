"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorBanner } from "@/components/ui/feedback";
import { api, TrainingAttemptCreate, TrainingMeta, TrainingRound } from "@/lib/api";
import { useTrainingProgress } from "./home";
import { ROUND_LABELS, SkeletonBlock } from "./shared";

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-2 text-xs shadow-xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring";

type Project = { title: string; description?: string | null; tech_stack?: string | null };

export function ResumeProjects({ onStart, starting, startError }: { onStart: (b: TrainingAttemptCreate) => void; starting: boolean; startError: unknown }) {
  const qc = useQueryClient();
  const prof = useQuery({ queryKey: ["training-profile"], queryFn: api.trainingProfile, retry: false });
  const [projects, setProjects] = React.useState<Project[] | null>(null);
  const [skills, setSkills] = React.useState<string | null>(null);
  const [degree, setDegree] = React.useState<string | null>(null);

  const save = useMutation({
    mutationFn: (reset: boolean) =>
      reset
        ? api.updateTrainingProfile({ reset_resume_data: true })
        : api.updateTrainingProfile({
            resume_data: {
              projects: (projects ?? prof.data!.resume_data.projects).filter((p) => p.title.trim()),
              skills: (skills ?? prof.data!.resume_data.skills.join(", ")).split(",").map((s) => s.trim()).filter(Boolean),
              degree: (degree ?? prof.data!.resume_data.degree ?? "") || null,
            },
          }),
    onSuccess: () => {
      setProjects(null);
      setSkills(null);
      setDegree(null);
      void qc.invalidateQueries({ queryKey: ["training-profile"] });
      void qc.invalidateQueries({ queryKey: ["training-progress"] });
    },
  });

  if (prof.isLoading) return <SkeletonBlock rows={3} />;
  if (prof.error || !prof.data) return <ErrorBanner error={prof.error ?? "Could not load your details."} onRetry={() => void prof.refetch()} />;
  const rd = prof.data.resume_data;
  const list = projects ?? rd.projects;
  const skillText = skills ?? rd.skills.join(", ");
  const degreeText = degree ?? rd.degree ?? "";
  const hasData = list.some((p) => p.title.trim()) || skillText.trim().length > 0;
  const setProject = (i: number, patch: Partial<Project>) => setProjects(list.map((p, n) => (n === i ? { ...p, ...patch } : p)));

  return (
    <div className="space-y-4 text-left">
      <p className="text-sm text-muted-foreground">
        Questions are built only from the details below. They come from your Career OS profile and résumé
        {rd.source === "student_edited" ? " (you have edited them)" : ""}. Correct anything that is wrong or missing, because nothing is invented for you.
      </p>
      <Card><CardContent className="space-y-4 pt-5">
        <div className="space-y-3">
          <p className="text-sm font-semibold">Projects</p>
          {list.length === 0 && <p className="text-xs text-muted-foreground">No projects found. Add one to practise project questions.</p>}
          {list.map((p, i) => (
            <div key={i} className="grid gap-2 rounded-lg border p-3 sm:grid-cols-2">
              <div>
                <label htmlFor={`pt-${i}`} className="mb-1 block text-[11px] text-muted-foreground">Project title</label>
                <Input id={`pt-${i}`} className="h-9 text-xs" value={p.title} maxLength={120} onChange={(e) => setProject(i, { title: e.target.value })} />
              </div>
              <div>
                <label htmlFor={`ps-${i}`} className="mb-1 block text-[11px] text-muted-foreground">Technologies used</label>
                <Input id={`ps-${i}`} className="h-9 text-xs" value={p.tech_stack ?? ""} maxLength={200} onChange={(e) => setProject(i, { tech_stack: e.target.value })} />
              </div>
              <div className="sm:col-span-2">
                <label htmlFor={`pd-${i}`} className="mb-1 block text-[11px] text-muted-foreground">What it does and your role</label>
                <Input id={`pd-${i}`} className="h-9 text-xs" value={p.description ?? ""} maxLength={1000} onChange={(e) => setProject(i, { description: e.target.value })} />
              </div>
              <Button type="button" size="sm" variant="ghost" className="w-fit text-destructive" onClick={() => setProjects(list.filter((_, n) => n !== i))}>
                <Trash2 className="mr-1 h-3.5 w-3.5" aria-hidden="true" /> Remove project
              </Button>
            </div>
          ))}
          <Button type="button" size="sm" variant="outline" disabled={list.length >= 10} onClick={() => setProjects([...list, { title: "", description: "", tech_stack: "" }])}>
            <Plus className="mr-1 h-3.5 w-3.5" aria-hidden="true" /> Add project
          </Button>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <label htmlFor="rs-skills" className="mb-1 block text-[11px] text-muted-foreground">Skills (comma separated)</label>
            <Input id="rs-skills" className="h-9 text-xs" value={skillText} onChange={(e) => setSkills(e.target.value)} />
          </div>
          <div>
            <label htmlFor="rs-degree" className="mb-1 block text-[11px] text-muted-foreground">Degree</label>
            <Input id="rs-degree" className="h-9 text-xs" value={degreeText} maxLength={120} onChange={(e) => setDegree(e.target.value)} />
          </div>
        </div>
        <ErrorBanner error={save.error} />
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" variant="outline" isLoading={save.isPending} onClick={() => save.mutate(false)}>Save corrections</Button>
          {rd.source === "student_edited" && <Button size="sm" variant="ghost" onClick={() => save.mutate(true)}>Reset to profile data</Button>}
          {save.isSuccess && <span role="status" className="text-xs text-emerald-600">Saved</span>}
        </div>
      </CardContent></Card>
      <ErrorBanner error={startError} />
      <Button disabled={!hasData} isLoading={starting} onClick={() => onStart({ mode: "practice", round: "resume", count: 8 })}>
        Start project interview
      </Button>
      {!hasData && <p className="text-xs text-muted-foreground">Add at least one project or skill (and save) to start.</p>}
      <p className="text-[11px] text-muted-foreground">Answer with what you really did. If you did not build or decide something, say so honestly and explain what you learned.</p>
    </div>
  );
}

const ALL_ROUNDS: TrainingRound[] = ["aptitude", "technical", "coding", "communication", "hr", "resume", "managerial"];

export function MockSetup({ meta, onStart, starting, startError }: { meta?: TrainingMeta; onStart: (b: TrainingAttemptCreate) => void; starting: boolean; startError: unknown }) {
  const prog = useTrainingProgress();
  const [role, setRole] = React.useState<string | null>(null);
  const [level, setLevel] = React.useState<string | null>(null);
  const [rounds, setRounds] = React.useState<TrainingRound[]>(["aptitude", "technical", "hr"]);
  const [duration, setDuration] = React.useState(30);
  const [difficulty, setDifficulty] = React.useState("");

  const effRole = role ?? prog.data?.profile.target_role ?? "";
  const effLevel = level ?? prog.data?.profile.level ?? "fresher";
  const toggle = (r: TrainingRound) => setRounds((cur) => (cur.includes(r) ? cur.filter((x) => x !== r) : [...cur, r]));
  const preset = (rs: TrainingRound[]) => setRounds(rs);
  const perRound = Math.max(2, Math.min(8, Math.floor(duration / (3 * Math.max(rounds.length, 1)))));

  return (
    <div className="space-y-4 text-left">
      <p className="text-sm text-muted-foreground">
        A mock interview asks one question at a time, in order. Model answers appear only after you answer, and follow-up questions may be asked based on your reply.
      </p>
      <Card><CardContent className="space-y-4 pt-5">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label htmlFor="mk-role" className="mb-1 block text-[11px] text-muted-foreground">Target job role</label>
            <select id="mk-role" className={selectClass} value={effRole} onChange={(e) => setRole(e.target.value)}>
              <option value="">Any IT role</option>
              {(meta?.target_roles ?? []).map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="mk-level" className="mb-1 block text-[11px] text-muted-foreground">Experience level</label>
            <select id="mk-level" className={selectClass} value={effLevel} onChange={(e) => setLevel(e.target.value)}>
              <option value="fresher">Fresher</option>
              <option value="junior">Junior</option>
              <option value="mid">Mid</option>
            </select>
          </div>
          <div>
            <label htmlFor="mk-duration" className="mb-1 block text-[11px] text-muted-foreground">Duration</label>
            <select id="mk-duration" className={selectClass} value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
              {[15, 30, 45, 60, 90].map((d) => <option key={d} value={d}>{d} minutes</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="mk-diff" className="mb-1 block text-[11px] text-muted-foreground">Difficulty</label>
            <select id="mk-diff" className={selectClass} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value="">Match my level</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
        </div>

        <fieldset>
          <legend className="mb-2 text-xs font-medium">Included rounds</legend>
          <div className="mb-2 flex flex-wrap gap-2">
            <Button type="button" size="sm" variant="outline" onClick={() => preset(["aptitude", "technical"])}>Aptitude + technical</Button>
            <Button type="button" size="sm" variant="outline" onClick={() => preset(["technical", "coding"])}>Technical + coding</Button>
            <Button type="button" size="sm" variant="outline" onClick={() => preset(["technical", "hr"])}>Technical + HR</Button>
            <Button type="button" size="sm" variant="outline" onClick={() => preset(ALL_ROUNDS)}>Full simulation</Button>
          </div>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
            {ALL_ROUNDS.map((r) => (
              <label key={r} className="flex items-center gap-2 rounded-md border p-2 text-xs">
                <input type="checkbox" checked={rounds.includes(r)} onChange={() => toggle(r)} />
                {ROUND_LABELS[r]}
              </label>
            ))}
          </div>
        </fieldset>
        <p className="text-xs text-muted-foreground">About {perRound} question{perRound === 1 ? "" : "s"} per round (roughly 3 minutes each). Coding has up to 2 problems; the project round needs details from the Resume &amp; Projects tab.</p>
        <ErrorBanner error={startError} />
        <Button
          disabled={rounds.length === 0}
          isLoading={starting}
          onClick={() => onStart({ mode: "mock", mock: { role: effRole || null, level: effLevel, rounds, duration_min: duration, difficulty: difficulty || null, language: "en" } })}
        >
          Start mock interview
        </Button>
        {rounds.length === 0 && <p className="text-xs text-destructive">Select at least one round.</p>}
      </CardContent></Card>
    </div>
  );
}
