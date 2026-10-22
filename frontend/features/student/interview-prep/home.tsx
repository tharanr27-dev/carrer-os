"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Target } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner } from "@/components/ui/feedback";
import { api, TrainingAction, TrainingMeta, TrainingProgress, TrainingRound } from "@/lib/api";
import { Bar, fmtPct, ROUND_LABELS, SkeletonBlock, StatusPill } from "./shared";

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-2 text-xs shadow-xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring";

const ORDER: TrainingRound[] = ["aptitude", "technical", "coding", "communication", "hr", "resume", "managerial"];
const TAB_FOR_ROUND: Record<string, string> = {
  aptitude: "aptitude", technical: "technical", coding: "coding", communication: "communication",
  hr: "hr", managerial: "hr", resume: "resume",
};

export function useTrainingProgress() {
  return useQuery({ queryKey: ["training-progress"], queryFn: api.trainingProgress, staleTime: 30_000, retry: false });
}

function ProfileCard({ progress, meta }: { progress: TrainingProgress; meta?: TrainingMeta }) {
  const qc = useQueryClient();
  const p = progress.profile;
  const [role, setRole] = React.useState(p.target_role ?? "");
  const [level, setLevel] = React.useState<string>(p.level);
  const [language, setLanguage] = React.useState<string>(p.language);
  const save = useMutation({
    mutationFn: () => api.updateTrainingProfile({ target_role: role || null, level, language }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["training-progress"] }),
  });
  return (
    <Card>
      <CardContent className="space-y-3 pt-5">
        <p className="flex items-center gap-2 text-sm font-semibold"><Target className="h-4 w-4 text-primary" aria-hidden="true" /> Your target</p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <label htmlFor="tp-role" className="mb-1 block text-[11px] text-muted-foreground">Target job role</label>
            <select id="tp-role" className={selectClass} value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="">Not set</option>
              {(meta?.target_roles ?? []).map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="tp-level" className="mb-1 block text-[11px] text-muted-foreground">Experience level</label>
            <select id="tp-level" className={selectClass} value={level} onChange={(e) => setLevel(e.target.value)}>
              <option value="fresher">Fresher</option>
              <option value="junior">Junior (0–2 years)</option>
              <option value="mid">Mid (2+ years)</option>
            </select>
          </div>
          <div>
            <label htmlFor="tp-lang" className="mb-1 block text-[11px] text-muted-foreground">Explanations</label>
            <select id="tp-lang" className={selectClass} value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="en">English</option>
              <option value="ta">Tamil (limited, where available)</option>
            </select>
          </div>
        </div>
        <ErrorBanner error={save.error} />
        <div className="flex items-center gap-3">
          <Button size="sm" isLoading={save.isPending} onClick={() => save.mutate()}>Save target</Button>
          {save.isSuccess && <span role="status" className="text-xs text-emerald-600">Saved</span>}
        </div>
        <p className="text-[11px] text-muted-foreground">Your role and level choose which topics and difficulty are suggested. Tamil explanations are not available yet; practice is in English.</p>
      </CardContent>
    </Card>
  );
}

export function RoadmapHome({ onAction, onOpenAttempt, onGo, meta }: {
  onAction: (a: TrainingAction["action"]) => void;
  onOpenAttempt: (id: string) => void;
  onGo: (tab: string) => void;
  meta?: TrainingMeta;
}) {
  const q = useTrainingProgress();
  if (q.isLoading) return <SkeletonBlock rows={4} />;
  if (q.error || !q.data) return <ErrorBanner error={q.error ?? "Could not load your progress."} onRetry={() => void q.refetch()} />;
  const p = q.data;
  const empty = p.attempts_total === 0;
  const tiles: { key: TrainingRound; label: string }[] = [
    { key: "aptitude", label: "Aptitude" },
    { key: "technical", label: "Technical" },
    { key: "communication", label: "Communication" },
    { key: "hr", label: "HR" },
  ];
  const resumable = p.recent_attempts.find((a) => a.status === "IN_PROGRESS");

  return (
    <div className="space-y-5 text-left">
      <ProfileCard progress={p} meta={meta} />

      {resumable && (
        <Card className="border-primary/40"><CardContent className="flex flex-wrap items-center justify-between gap-2 pt-5 text-sm">
          <span>You have an unfinished {ROUND_LABELS[resumable.round] ?? resumable.round} session. Your answers so far are saved.</span>
          <Button size="sm" onClick={() => onOpenAttempt(resumable.id)}>Continue</Button>
        </CardContent></Card>
      )}

      <Card>
        <CardContent className="space-y-3 pt-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-semibold">Overall preparation</p>
            <span className="text-2xl font-bold" aria-label="Overall preparation score">{fmtPct(p.overall_pct)}</span>
          </div>
          <Bar value={p.overall_pct} label="Overall preparation" />
          <p className="text-xs text-muted-foreground">
            {empty
              ? "No practice saved yet. Your scores appear here after your first session."
              : `Based on ${p.total_scored_answers} scored answers across ${p.attempts_total} sessions. Current stage: ${p.current_stage.label}.`}
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {tiles.map((t) => {
          const r = p.rounds[t.key];
          return (
            <Card key={t.key}><CardContent className="space-y-1 pt-4">
              <p className="text-[11px] text-muted-foreground">{t.label}</p>
              <p className="text-xl font-bold">{fmtPct(r.combined_pct)}</p>
              <p className="text-[10px] text-muted-foreground">
                {r.attempted === 0 ? "Not attempted" : `${r.attempted} answers · ${r.objective_pct != null ? "objective" : "estimate"}`}
              </p>
            </CardContent></Card>
          );
        })}
      </div>

      <section aria-labelledby="roadmap-h" className="space-y-2">
        <h3 id="roadmap-h" className="text-sm font-semibold">My Training Roadmap</h3>
        <ol className="space-y-2">
          {ORDER.map((r, i) => {
            const rp = p.rounds[r];
            const current = p.current_stage.round === r;
            return (
              <li key={r}>
                <Card className={current ? "border-primary/50" : ""}><CardContent className="flex flex-wrap items-center justify-between gap-3 pt-4">
                  <div className="flex items-center gap-3">
                    <span aria-hidden="true" className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-xs font-bold">{i + 1}</span>
                    <div>
                      <p className="text-sm font-semibold">{ROUND_LABELS[r]} {current && <span className="ml-1 text-[10px] font-normal text-primary">Current stage</span>}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {rp.attempted === 0 ? "No answers yet" : `${rp.attempted} answers · ${fmtPct(rp.combined_pct)}`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusPill status={rp.status} />
                    <Button size="sm" variant="outline" onClick={() => onGo(TAB_FOR_ROUND[r])}>Open</Button>
                  </div>
                </CardContent></Card>
              </li>
            );
          })}
        </ol>
      </section>

      <section aria-labelledby="next-h" className="space-y-2">
        <h3 id="next-h" className="text-sm font-semibold">Recommended next practice</h3>
        {p.recommendations.map((r) => (
          <Card key={r.rule ?? r.title}><CardContent className="flex flex-wrap items-center justify-between gap-3 pt-4">
            <div><p className="text-sm font-semibold">{r.title}</p><p className="text-xs text-muted-foreground">{r.reason}</p></div>
            <Button size="sm" onClick={() => onAction(r.action)}>Start <ArrowRight className="ml-1 h-3.5 w-3.5" aria-hidden="true" /></Button>
          </CardContent></Card>
        ))}
      </section>

      <div className="grid gap-3 md:grid-cols-2">
        <Card><CardContent className="space-y-2 pt-4">
          <p className="text-sm font-semibold">Weakest topics</p>
          {p.weakest_topics.length === 0 ? (
            <p className="text-xs text-muted-foreground">None flagged yet. A topic needs at least 3 scored answers below 60%.</p>
          ) : (
            p.weakest_topics.map((t) => (
              <div key={`${t.round}-${t.topic}`} className="space-y-1 text-xs">
                <div className="flex justify-between"><span>{t.label}</span><span>{fmtPct(t.score_pct)}</span></div>
                <Bar value={t.score_pct} tone="warn" label={`${t.label} score`} />
              </div>
            ))
          )}
        </CardContent></Card>
        <Card><CardContent className="space-y-2 pt-4">
          <p className="text-sm font-semibold">Recent attempts</p>
          {p.recent_attempts.length === 0 ? (
            <EmptyState title="No attempts yet" description="Start with the recommendation above." className="py-4" />
          ) : (
            p.recent_attempts.map((a) => (
              <button key={a.id} type="button" onClick={() => onOpenAttempt(a.id)} className="flex w-full items-center justify-between rounded-md border p-2 text-left text-xs hover:bg-muted/40">
                <span>{ROUND_LABELS[a.round] ?? a.round}{a.topic ? ` · ${a.topic}` : ""} · {new Date(a.started_at).toLocaleDateString()}</span>
                <span>{a.status === "COMPLETED" ? fmtPct(a.overall_pct) : "In progress"}</span>
              </button>
            ))
          )}
        </CardContent></Card>
      </div>

      <Card><CardContent className="space-y-2 pt-4">
        <p className="text-sm font-semibold">Improvement over time</p>
        {p.trend.length < 2 ? (
          <p className="text-xs text-muted-foreground">Complete at least two sessions to see a trend.</p>
        ) : (
          <>
            <div className="flex h-24 items-end gap-1" role="img" aria-label={`Scores of your last ${p.trend.length} sessions`}>
              {p.trend.map((t) => (
                <div key={t.attempt_id} className="flex-1 rounded-t bg-primary/70" style={{ height: `${Math.max(4, t.overall_pct)}%` }} title={`${Math.round(t.overall_pct)}%`} />
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              {p.improvement_pct_points != null
                ? `First three vs latest three sessions: ${p.improvement_pct_points >= 0 ? "+" : ""}${p.improvement_pct_points} points.`
                : "Complete 6 sessions to compare early and recent results."}
            </p>
          </>
        )}
      </CardContent></Card>
      <details className="rounded-md border p-3 text-xs">
        <summary className="cursor-pointer font-medium">How scores and recommendations work</summary>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">{p.scoring_rules.map((s) => <li key={s}>{s}</li>)}</ul>
      </details>
    </div>
  );
}

export function ProgressHistory({ onOpenAttempt }: { onOpenAttempt: (id: string) => void }) {
  const [page, setPage] = React.useState(1);
  const hist = useQuery({ queryKey: ["training-history", page], queryFn: () => api.trainingHistory(page, 8), retry: false });
  const prog = useTrainingProgress();
  if (hist.isLoading || prog.isLoading) return <SkeletonBlock rows={3} />;
  if (hist.error || !hist.data) return <ErrorBanner error={hist.error ?? "Could not load history."} onRetry={() => void hist.refetch()} />;
  const pages = Math.max(1, Math.ceil(hist.data.total / hist.data.size));
  const p = prog.data;
  return (
    <div className="space-y-4 text-left">
      {p && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {ORDER.map((r) => (
            <Card key={r}><CardContent className="space-y-1 pt-4">
              <p className="text-[11px] text-muted-foreground">{ROUND_LABELS[r]}</p>
              <p className="text-lg font-bold">{fmtPct(p.rounds[r].combined_pct)}</p>
              <p className="text-[10px] text-muted-foreground">
                Obj {fmtPct(p.rounds[r].objective_pct)} · Est {fmtPct(p.rounds[r].estimated_pct)} · Self {fmtPct(p.rounds[r].self_assessed_pct)}
              </p>
            </CardContent></Card>
          ))}
        </div>
      )}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Attempt history</h3>
        {hist.data.items.length === 0 ? (
          <EmptyState title="No attempts yet" description="Your sessions will be listed here." />
        ) : (
          hist.data.items.map((a) => (
            <Card key={a.id}><CardContent className="flex flex-wrap items-center justify-between gap-2 pt-4 text-xs">
              <div>
                <p className="text-sm font-semibold">{ROUND_LABELS[a.round] ?? a.round}{a.topic ? ` · ${a.topic}` : ""} <span className="font-normal text-muted-foreground">({a.mode})</span></p>
                <p className="text-muted-foreground">{new Date(a.started_at).toLocaleString()}</p>
              </div>
              <div className="flex items-center gap-3">
                <span>{a.status === "COMPLETED" ? fmtPct(a.overall_pct) : "In progress"}</span>
                <Button size="sm" variant="outline" onClick={() => onOpenAttempt(a.id)}>{a.status === "COMPLETED" ? "Review" : "Continue"}</Button>
              </div>
            </CardContent></Card>
          ))
        )}
        {pages > 1 && (
          <nav aria-label="History pages" className="flex items-center justify-between pt-1 text-xs">
            <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage((n) => n - 1)}>Previous</Button>
            <span>Page {page} of {pages}</span>
            <Button size="sm" variant="outline" disabled={page >= pages} onClick={() => setPage((n) => n + 1)}>Next</Button>
          </nav>
        )}
      </div>
    </div>
  );
}
