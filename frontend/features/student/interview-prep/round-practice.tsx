"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner } from "@/components/ui/feedback";
import type { TrainingAttemptCreate, TrainingMeta, TrainingMode, TrainingRound } from "@/lib/api";
import { SkeletonBlock } from "./shared";

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-2 text-xs shadow-xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring";

interface Props {
  rounds: TrainingRound[];
  meta?: TrainingMeta;
  loading: boolean;
  error: unknown;
  onRetry: () => void;
  onStart: (body: TrainingAttemptCreate) => void;
  starting: boolean;
  startError: unknown;
  intro: string;
  allowExam?: boolean;
}

export function RoundPractice({ rounds, meta, loading, error, onRetry, onStart, starting, startError, intro, allowExam = false }: Props) {
  const [round, setRound] = React.useState<TrainingRound>(rounds[0]);
  const [topic, setTopic] = React.useState<string | null>(null);
  const [difficulty, setDifficulty] = React.useState("");
  const [mode, setMode] = React.useState<TrainingMode>("practice");
  const [count, setCount] = React.useState(10);
  const [minutes, setMinutes] = React.useState("");
  const [generate, setGenerate] = React.useState(false);

  if (loading) return <SkeletonBlock rows={3} />;
  if (error || !meta) return <ErrorBanner error={error ?? "Could not load topics."} onRetry={onRetry} />;
  const info = meta.rounds.find((r) => r.key === round);
  if (!info) return <EmptyState title="Nothing to practise yet" description="This round is not available." />;
  const total = info.groups.reduce((n, g) => n + g.topics.reduce((m, t) => m + t.questions, 0), 0);
  const topicInfo = info.groups.flatMap((g) => g.topics).find((t) => t.slug === topic);
  const isExam = mode === "exam";

  const start = () =>
    onStart({
      mode,
      round,
      topic,
      difficulty: difficulty || null,
      count,
      adaptive: true,
      generate: generate && !!topic,
      time_limit_sec: isExam && minutes ? Math.round(Number(minutes) * 60) : undefined,
    });

  return (
    <div className="space-y-4 text-left">
      <p className="text-sm text-muted-foreground">{intro}</p>
      {rounds.length > 1 && (
        <div role="tablist" aria-label="Round" className="flex gap-2">
          {rounds.map((r) => {
            const label = meta.rounds.find((x) => x.key === r)?.label ?? r;
            return (
              <button
                key={r}
                role="tab"
                aria-selected={round === r}
                onClick={() => {
                  setRound(r);
                  setTopic(null);
                }}
                className={`rounded-md border px-3 py-1.5 text-xs ${round === r ? "border-primary bg-primary/10 font-semibold" : ""}`}
              >
                {label}
              </button>
            );
          })}
        </div>
      )}

      {total === 0 ? (
        <EmptyState title="No questions available yet" description="This round has no reviewed questions to practise. Check back later." />
      ) : (
        <>
          <fieldset className="space-y-3">
            <legend className="mb-1 text-sm font-semibold">Choose a topic</legend>
            <button
              type="button"
              aria-pressed={topic === null}
              onClick={() => setTopic(null)}
              className={`w-full rounded-lg border p-2.5 text-left text-xs ${topic === null ? "border-primary bg-primary/5" : "hover:bg-muted/40"}`}
            >
              <span className="font-semibold">Adaptive mix</span> · all topics, weighted toward the ones you find hardest
            </button>
            {info.groups.map((g) => (
              <div key={g.name} className="space-y-1.5">
                <p className="text-xs font-medium text-muted-foreground">{g.name}</p>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {g.topics.map((t) => (
                    <button
                      key={t.slug}
                      type="button"
                      disabled={t.questions === 0}
                      aria-pressed={topic === t.slug}
                      onClick={() => setTopic(t.slug)}
                      className={`rounded-lg border p-2.5 text-left text-xs disabled:opacity-50 ${topic === t.slug ? "border-primary bg-primary/5" : "hover:bg-muted/40"}`}
                    >
                      <span className="block font-semibold">{t.label}</span>
                      <span className="text-muted-foreground">{t.questions} question{t.questions === 1 ? "" : "s"}</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </fieldset>

          <Card>
            <CardContent className="space-y-3 pt-5">
              <p className="text-sm font-semibold">
                Session settings{topicInfo ? ` · ${topicInfo.label}` : " · adaptive mix"}
              </p>
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                {allowExam && (
                  <div>
                    <label htmlFor={`mode-${rounds[0]}`} className="mb-1 block text-[11px] text-muted-foreground">Mode</label>
                    <select id={`mode-${rounds[0]}`} className={selectClass} value={mode} onChange={(e) => setMode(e.target.value as TrainingMode)}>
                      <option value="practice">Practice (no timer, instant feedback)</option>
                      <option value="exam">Exam (timed, answers after submit)</option>
                    </select>
                  </div>
                )}
                <div>
                  <label htmlFor={`diff-${rounds[0]}`} className="mb-1 block text-[11px] text-muted-foreground">Difficulty</label>
                  <select id={`diff-${rounds[0]}`} className={selectClass} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                    <option value="">Match my level</option>
                    {meta.difficulties.map((d) => (
                      <option key={d} value={d}>{d[0].toUpperCase() + d.slice(1)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor={`count-${rounds[0]}`} className="mb-1 block text-[11px] text-muted-foreground">Questions</label>
                  <select id={`count-${rounds[0]}`} className={selectClass} value={count} onChange={(e) => setCount(Number(e.target.value))}>
                    {[5, 10, 15, 20, 30].map((n) => (
                      <option key={n} value={n}>{n}</option>
                    ))}
                  </select>
                </div>
                {isExam && (
                  <div>
                    <label htmlFor={`min-${rounds[0]}`} className="mb-1 block text-[11px] text-muted-foreground">Time limit (minutes)</label>
                    <input
                      id={`min-${rounds[0]}`}
                      type="number"
                      min={1}
                      max={180}
                      placeholder="Auto"
                      className={selectClass}
                      value={minutes}
                      onChange={(e) => setMinutes(e.target.value)}
                    />
                  </div>
                )}
              </div>
              {!isExam && (
                <label className={`flex items-start gap-2 text-xs ${meta.ai_available && topic ? "" : "opacity-60"}`}>
                  <input
                    type="checkbox"
                    className="mt-0.5"
                    disabled={!meta.ai_available || !topic}
                    checked={generate}
                    onChange={(e) => setGenerate(e.target.checked)}
                  />
                  <span>
                    Include fresh AI-generated questions (unreviewed, labelled as such)
                    {!meta.ai_available && <span className="block text-muted-foreground">Not available: no AI provider is configured on this server.</span>}
                    {meta.ai_available && !topic && <span className="block text-muted-foreground">Pick a topic first.</span>}
                  </span>
                </label>
              )}
              <ErrorBanner error={startError} />
              <Button onClick={start} isLoading={starting}>
                {isExam ? "Start exam" : "Start practice"}
              </Button>
              <p className="text-[11px] text-muted-foreground">{meta.disclaimer}</p>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
