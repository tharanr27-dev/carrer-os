"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ChevronLeft, ChevronRight, Clock, Lightbulb, Sparkles, XCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorBanner } from "@/components/ui/feedback";
import { api, TrainingAction, TrainingAttempt, TrainingItem } from "@/lib/api";
import { Bar, Chip, fmtDuration, fmtPct, ROUND_LABELS, SCORE_KIND_LABEL, SkeletonBlock } from "./shared";

interface Draft {
  index?: number;
  text: string;
  passed: string;
  total: string;
}

const emptyDraft: Draft = { text: "", passed: "", total: "" };

function useCountdown(deadline: string | null, active: boolean) {
  const [left, setLeft] = React.useState<number | null>(null);
  React.useEffect(() => {
    if (!deadline || !active) {
      setLeft(null);
      return;
    }
    const tick = () => setLeft(Math.max(0, Math.round((new Date(deadline).getTime() - Date.now()) / 1000)));
    tick();
    const t = setInterval(tick, 1000);
    return () => clearInterval(t);
  }, [deadline, active]);
  return left;
}

export function AttemptRunner({
  attemptId,
  onExit,
  onAction,
}: {
  attemptId: string;
  onExit: () => void;
  onAction: (a: TrainingAction["action"]) => void;
}) {
  const qc = useQueryClient();
  const key = React.useMemo(() => ["training-attempt", attemptId], [attemptId]);
  const attemptQ = useQuery({ queryKey: key, queryFn: () => api.trainingAttempt(attemptId), staleTime: Infinity, retry: false });
  const attempt = attemptQ.data;

  const [idx, setIdx] = React.useState<number | null>(null);
  const [drafts, setDrafts] = React.useState<Record<string, Draft>>({});
  const [hintsOpen, setHintsOpen] = React.useState(false);
  const [notice, setNotice] = React.useState<string[]>([]);
  const shownAt = React.useRef<number>(Date.now());
  const autoFinished = React.useRef(false);

  const setAttempt = React.useCallback((a: TrainingAttempt) => qc.setQueryData(key, a), [qc, key]);

  React.useEffect(() => {
    if (attempt && idx === null) {
      const firstOpen = attempt.items.findIndex((i) => !i.answered);
      setIdx(attempt.status === "COMPLETED" || firstOpen < 0 ? 0 : firstOpen);
    }
  }, [attempt, idx]);

  React.useEffect(() => {
    shownAt.current = Date.now();
    setHintsOpen(false);
  }, [idx]);

  const finish = useMutation({ mutationFn: () => api.trainingFinish(attemptId), onSuccess: setAttempt });
  const answer = useMutation({
    mutationFn: (v: { item: TrainingItem; draft: Draft }) => {
      const { item, draft } = v;
      const base = { item_id: item.id, time_taken_sec: Math.round((Date.now() - shownAt.current) / 1000) };
      if (item.qtype === "mcq") return api.trainingAnswer(attemptId, { ...base, index: draft.index });
      if (item.qtype === "code") {
        return api.trainingAnswer(attemptId, {
          ...base,
          text: draft.text,
          self_passed: Number(draft.passed || 0),
          self_total: Number(draft.total || item.coding?.tests.length || 1),
        });
      }
      return api.trainingAnswer(attemptId, { ...base, text: draft.text });
    },
    onSuccess: (res, v) => {
      const cur = qc.getQueryData<TrainingAttempt>(key);
      if (!cur) return;
      let items = cur.items.map((i) =>
        i.id !== v.item.id
          ? i
          : res.item ?? { ...i, answered: true, answer: v.item.qtype === "mcq" ? { index: v.draft.index } : { text: v.draft.text } }
      );
      if (res.follow_up) {
        const at = items.findIndex((i) => i.id === v.item.id);
        items = [...items.slice(0, at + 1), res.follow_up, ...items.slice(at + 1).map((i) => ({ ...i, position: i.position + 1 }))];
      }
      setAttempt({ ...cur, items });
    },
  });
  const more = useMutation({
    mutationFn: (generate: boolean) => api.trainingNext(attemptId, { generate, count: generate ? 3 : 1 }),
    onSuccess: (res) => {
      setNotice(res.notices);
      setAttempt(res.attempt);
      const first = res.added[0];
      if (first) setIdx(res.attempt.items.findIndex((i) => i.id === first.id));
    },
  });

  const inProgress = attempt?.status === "IN_PROGRESS";
  const remaining = useCountdown(attempt?.deadline ?? null, !!inProgress);
  React.useEffect(() => {
    if (remaining === 0 && inProgress && !autoFinished.current) {
      autoFinished.current = true;
      finish.mutate();
    }
  }, [remaining, inProgress, finish]);

  if (attemptQ.isLoading) return <SkeletonBlock rows={3} />;
  if (attemptQ.error || !attempt) return <ErrorBanner error={attemptQ.error ?? "Could not load this session."} onRetry={() => void attemptQ.refetch()} />;
  if (attempt.status === "COMPLETED") return <AttemptResults attempt={attempt} onExit={onExit} onAction={onAction} />;

  const items = attempt.items;
  const cur = items[idx ?? 0];
  if (!cur) return <ErrorBanner error="This session has no questions." />;
  const draft = drafts[cur.id] ?? emptyDraft;
  const setDraft = (patch: Partial<Draft>) => setDrafts((d) => ({ ...d, [cur.id]: { ...(d[cur.id] ?? emptyDraft), ...patch } }));
  const isExam = attempt.mode === "exam";
  const isMock = attempt.mode === "mock";
  const lastIdx = items.length - 1;
  const answeredCount = items.filter((i) => i.answered).length;
  const canSubmit =
    !cur.answered || isExam
      ? cur.qtype === "mcq"
        ? draft.index !== undefined
        : draft.text.trim().split(/\s+/).filter(Boolean).length >= 3
      : false;
  const showFeedback = cur.answered && !!cur.result && !isExam;
  const canGoNext = (idx ?? 0) < lastIdx && (!isMock || cur.answered);
  const timeLabel = remaining != null ? `${String(Math.floor(remaining / 60)).padStart(2, "0")}:${String(remaining % 60).padStart(2, "0")}` : null;

  return (
    <div className="space-y-4 text-left">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs text-muted-foreground">
            {ROUND_LABELS[attempt.round] ?? attempt.round}
            {attempt.topic ? ` · ${cur.topic_label}` : ""} · {isExam ? "Exam mode" : isMock ? "Mock interview" : "Practice"}
          </p>
          <p className="text-sm font-semibold" aria-live="polite">
            Question {(idx ?? 0) + 1} of {items.length} · {answeredCount} answered
          </p>
        </div>
        <div className="flex items-center gap-2">
          {timeLabel && (
            <span
              role="timer"
              aria-label={`Time left ${timeLabel}`}
              className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 font-mono text-xs ${remaining! < 60 ? "border-destructive text-destructive" : ""}`}
            >
              <Clock className="h-3.5 w-3.5" aria-hidden="true" /> {timeLabel}
            </span>
          )}
          <Button variant="ghost" size="sm" onClick={onExit}>
            Save & exit
          </Button>
        </div>
      </div>
      <Bar value={(answeredCount / items.length) * 100} label="Session progress" />

      {[...(attempt.config?.notices ?? []), ...notice].map((n) => (
        <p key={n} role="status" className="rounded-md border border-sky-500/30 bg-sky-500/10 p-2 text-xs text-sky-800 dark:text-sky-300">
          {n}
        </p>
      ))}

      <Card>
        <CardContent className="space-y-4 pt-5">
          <div className="flex flex-wrap items-center gap-1.5">
            <Chip>{cur.difficulty}</Chip>
            {cur.label && <Chip>{cur.label}</Chip>}
            {cur.is_follow_up && <Chip tone="info">Follow-up</Chip>}
            {cur.source === "generated" && <Chip tone="warn">AI-generated · unreviewed, check the explanation</Chip>}
          </div>
          <h3 className="whitespace-pre-wrap text-sm font-semibold leading-relaxed" id="q-prompt">
            {cur.coding?.title ? cur.prompt.replace(`${cur.coding.title}\n\n`, "") : cur.prompt}
          </h3>
          {cur.coding && <CodingDetails coding={cur.coding} title={cur.coding.title} hintsOpen={hintsOpen} toggleHints={() => setHintsOpen((v) => !v)} />}

          {cur.qtype === "mcq" && cur.options && (
            <div role="radiogroup" aria-labelledby="q-prompt" className="space-y-2">
              {cur.options.map((opt, i) => {
                const locked = cur.answered && !isExam;
                // Exam answers stay editable: a new pick (draft) wins over the saved one.
                const selected = locked ? cur.answer?.index : (draft.index ?? cur.answer?.index);
                const picked = selected === i;
                const res = showFeedback ? cur.result : null;
                const tone = res
                  ? i === res.correct_index
                    ? "border-emerald-500 bg-emerald-500/10"
                    : picked
                      ? "border-destructive bg-destructive/10"
                      : ""
                  : picked
                    ? "border-primary bg-primary/5"
                    : "hover:bg-muted/40";
                return (
                  <label key={i} className={`flex cursor-pointer items-start gap-2 rounded-lg border p-2.5 text-sm ${tone} ${locked ? "cursor-default" : ""}`}>
                    <input
                      type="radio"
                      name={`q-${cur.id}`}
                      className="mt-1"
                      checked={picked}
                      disabled={locked}
                      onChange={() => setDraft({ index: i })}
                    />
                    <span className="whitespace-pre-wrap">{opt}</span>
                  </label>
                );
              })}
            </div>
          )}

          {cur.qtype !== "mcq" && (
            <div className="space-y-2">
              <label htmlFor="answer-box" className="text-xs font-medium text-muted-foreground">
                {cur.qtype === "code" ? "Write your solution (any language). It is not executed." : "Your answer"}
              </label>
              <textarea
                id="answer-box"
                rows={cur.qtype === "code" ? 10 : 6}
                className={`w-full rounded-md border bg-background p-2 text-sm focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring ${cur.qtype === "code" ? "font-mono text-xs" : ""}`}
                value={cur.answered && !isExam ? (cur.answer?.text ?? "") : draft.text}
                disabled={cur.answered && !isExam}
                maxLength={6000}
                onChange={(e) => setDraft({ text: e.target.value })}
                placeholder={cur.qtype === "code" ? "def solve(): ..." : "Use your own real experience and examples."}
              />
              {cur.qtype === "code" && !cur.answered && (
                <div className="grid max-w-md grid-cols-2 gap-2 text-xs">
                  <label className="space-y-1">
                    <span className="text-muted-foreground">Test cases you believe pass</span>
                    <input
                      type="number"
                      min={0}
                      max={cur.coding?.tests.length ?? 10}
                      className="w-full rounded-md border bg-background p-1.5"
                      value={draft.passed}
                      onChange={(e) => setDraft({ passed: e.target.value, total: String(cur.coding?.tests.length ?? 1) })}
                    />
                  </label>
                  <p className="self-end text-muted-foreground">of {cur.coding?.tests.length ?? 1} listed. Self-assessed: the platform does not run your code.</p>
                </div>
              )}
              {cur.qtype === "text" && !cur.answered && (cur.label?.includes("scenario") || cur.topic === "behavioural") && (
                <p className="text-xs text-muted-foreground">Tip: structure it as Situation, Task, Action, Result (STAR).</p>
              )}
            </div>
          )}

          <ErrorBanner error={answer.error} />

          <div className="flex flex-wrap items-center justify-between gap-2 border-t pt-3">
            <Button variant="outline" size="sm" disabled={(idx ?? 0) === 0 || isMock} onClick={() => setIdx((i) => Math.max(0, (i ?? 0) - 1))}>
              <ChevronLeft className="mr-1 h-3.5 w-3.5" aria-hidden="true" /> Previous
            </Button>
            <div className="flex flex-wrap gap-2">
              {(!cur.answered || isExam) && (
                <Button size="sm" disabled={!canSubmit} isLoading={answer.isPending} onClick={() => answer.mutate({ item: cur, draft })}>
                  {isExam ? "Save answer" : "Submit answer"}
                </Button>
              )}
              {canGoNext && (
                <Button size="sm" variant={cur.answered ? "default" : "outline"} onClick={() => setIdx((i) => (i ?? 0) + 1)}>
                  Next <ChevronRight className="ml-1 h-3.5 w-3.5" aria-hidden="true" />
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {showFeedback && cur.result && <FeedbackPanel item={cur} />}

      <div className="flex flex-wrap items-center justify-between gap-2">
        {attempt.mode === "practice" && attempt.round !== "resume" && (idx ?? 0) === lastIdx ? (
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" isLoading={more.isPending} onClick={() => more.mutate(false)}>
              More questions
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={!attempt.ai_available || !attempt.topic || more.isPending}
              title={attempt.ai_available ? "Generate new practice questions with AI" : "AI generation is not configured on this server"}
              onClick={() => more.mutate(true)}
            >
              <Sparkles className="mr-1 h-3.5 w-3.5" aria-hidden="true" /> Generate new (AI)
            </Button>
          </div>
        ) : (
          <span />
        )}
        <Button
          size="sm"
          variant={answeredCount === items.length ? "default" : "outline"}
          isLoading={finish.isPending}
          onClick={() => {
            if (isExam && answeredCount < items.length && !window.confirm(`${items.length - answeredCount} question(s) are unanswered and will score zero. Submit anyway?`)) return;
            finish.mutate();
          }}
        >
          {isExam ? "Submit exam" : "Finish & see results"}
        </Button>
      </div>
      <ErrorBanner error={more.error ?? finish.error} />
    </div>
  );
}

function CodingDetails({ coding, title, hintsOpen, toggleHints }: { coding: NonNullable<TrainingItem["coding"]>; title: string; hintsOpen: boolean; toggleHints: () => void }) {
  return (
    <div className="space-y-2 rounded-lg border bg-muted/20 p-3 text-xs">
      <p className="font-semibold">{title}</p>
      <p><span className="font-medium">Input:</span> {coding.input_format}</p>
      <p><span className="font-medium">Output:</span> {coding.output_format}</p>
      {coding.constraints.length > 0 && <p><span className="font-medium">Constraints:</span> {coding.constraints.join(" · ")}</p>}
      {coding.schema_sql && <pre className="overflow-x-auto rounded bg-background p-2">{coding.schema_sql}</pre>}
      {coding.examples.map((e, i) => (
        <div key={i} className="grid gap-2 sm:grid-cols-2">
          <pre className="overflow-x-auto rounded bg-background p-2"><span className="text-muted-foreground">Example input{"\n"}</span>{e.input}</pre>
          <pre className="overflow-x-auto rounded bg-background p-2"><span className="text-muted-foreground">Example output{"\n"}</span>{e.output}</pre>
        </div>
      ))}
      <p className="text-muted-foreground">Expected: time {coding.time_complexity}, space {coding.space_complexity} · Concepts: {coding.concepts.join(", ")}</p>
      <button type="button" onClick={toggleHints} aria-expanded={hintsOpen} className="inline-flex items-center gap-1 font-medium text-primary hover:underline">
        <Lightbulb className="h-3 w-3" aria-hidden="true" /> {hintsOpen ? "Hide hints" : "Show hints"}
      </button>
      {hintsOpen && <ul className="list-disc space-y-1 pl-5">{coding.hints.map((h) => <li key={h}>{h}</li>)}</ul>}
      <details>
        <summary className="cursor-pointer font-medium">Test cases ({coding.tests.length})</summary>
        <ul className="mt-1 space-y-1">
          {coding.tests.map((t, i) => (
            <li key={i}><code className="whitespace-pre-wrap">{t.input.replace(/\n/g, " ⏎ ")}</code> → <code>{t.output.replace(/\n/g, " ⏎ ")}</code></li>
          ))}
        </ul>
      </details>
    </div>
  );
}

function FeedbackPanel({ item }: { item: TrainingItem }) {
  const r = item.result!;
  const ev = r.evaluation;
  return (
    <Card role="region" aria-label="Feedback" className={r.is_correct === false ? "border-destructive/40" : r.is_correct ? "border-emerald-500/40" : ""}>
      <CardContent className="space-y-3 pt-5 text-sm">
        <div className="flex flex-wrap items-center gap-2">
          {r.is_correct === true && <span className="inline-flex items-center gap-1 font-semibold text-emerald-600"><CheckCircle2 className="h-4 w-4" aria-hidden="true" /> Correct</span>}
          {r.is_correct === false && <span className="inline-flex items-center gap-1 font-semibold text-destructive"><XCircle className="h-4 w-4" aria-hidden="true" /> Not quite</span>}
          {r.score_kind && <Chip tone="info">{SCORE_KIND_LABEL[r.score_kind]}{r.is_correct == null && r.score != null ? `: ${fmtPct(r.score * 100)}` : ""}</Chip>}
        </div>
        {r.explanation && <p className="whitespace-pre-wrap text-xs leading-relaxed"><span className="font-semibold">Explanation: </span>{r.explanation}</p>}
        {ev?.criteria && (
          <div className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
            {Object.entries(ev.criteria).map(([k, v]) => (
              <div key={k} className="space-y-1 text-xs">
                <div className="flex justify-between"><span className="capitalize">{k}</span><span>{v}/5</span></div>
                <Bar value={(v / 5) * 100} label={`${k} ${v} out of 5`} />
              </div>
            ))}
          </div>
        )}
        {ev?.strengths && ev.strengths.length > 0 && <ul className="list-disc pl-5 text-xs text-emerald-700 dark:text-emerald-400">{ev.strengths.map((s) => <li key={s}>{s}</li>)}</ul>}
        {ev?.improvements && ev.improvements.length > 0 && <ul className="list-disc pl-5 text-xs">{ev.improvements.map((s) => <li key={s}>{s}</li>)}</ul>}
        {ev?.self_total != null && <p className="text-xs">You marked {ev.self_passed} of {ev.self_total} test cases as passing.</p>}
        {r.model_answer && (
          <div className="rounded-md bg-muted/40 p-3 text-xs">
            <p className="mb-1 font-semibold">{item.qtype === "code" ? "Reference solution (Python)" : "Model answer"}</p>
            <pre className="whitespace-pre-wrap font-sans">{r.model_answer}</pre>
          </div>
        )}
        {ev?.stronger_answer && <p className="text-xs"><span className="font-semibold">A stronger answer: </span>{ev.stronger_answer}</p>}
        {ev?.disclaimer && <p className="text-[11px] text-muted-foreground">{ev.disclaimer}</p>}
        {ev?.fallback_reason && <p className="text-[11px] text-muted-foreground">{ev.fallback_reason}</p>}
      </CardContent>
    </Card>
  );
}

export function AttemptResults({ attempt, onExit, onAction }: { attempt: TrainingAttempt; onExit: () => void; onAction: (a: TrainingAction["action"]) => void }) {
  const s = attempt.summary;
  const [open, setOpen] = React.useState<string | null>(null);
  if (!s) return <ErrorBanner error="No summary was saved for this session." />;
  const tiles = [
    { label: "Overall", value: fmtPct(s.overall_pct) },
    { label: "Objective (MCQ)", value: s.objective_total ? `${s.correct}/${s.objective_total} · ${fmtPct(s.objective_pct)}` : "—" },
    { label: "Estimated (written)", value: fmtPct(s.estimated_pct) },
    { label: "Self-assessed (code)", value: fmtPct(s.self_assessed_pct) },
    { label: "Answered", value: `${s.answered}/${s.total_questions}` },
    { label: "Avg time / question", value: fmtDuration(s.avg_time_sec) },
  ];
  return (
    <div className="space-y-4 text-left">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-base font-bold" id="results-heading">Results · {ROUND_LABELS[attempt.round] ?? attempt.round}</h3>
        <Button size="sm" variant="outline" onClick={onExit}>Back to Interview Preparation</Button>
      </div>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3" aria-labelledby="results-heading">
        {tiles.map((t) => (
          <Card key={t.label}><CardContent className="pt-4"><p className="text-[11px] text-muted-foreground">{t.label}</p><p className="text-lg font-bold">{t.value}</p></CardContent></Card>
        ))}
      </div>
      {s.change_vs_previous != null && (
        <p className="text-xs">Compared with your previous attempt ({fmtPct(s.previous_overall_pct)}): <span className="font-semibold">{s.change_vs_previous >= 0 ? "+" : ""}{s.change_vs_previous} points</span>.</p>
      )}
      {s.readiness_note && <p className="rounded-md border bg-muted/30 p-3 text-xs">{s.readiness_note}</p>}
      {Object.keys(s.by_round).length > 1 && (
        <Card><CardContent className="space-y-2 pt-4">
          <p className="text-sm font-semibold">By round</p>
          {Object.entries(s.by_round).map(([r, v]) => (
            <div key={r} className="space-y-1 text-xs"><div className="flex justify-between"><span>{v.label}</span><span>{fmtPct(v.score_pct)}</span></div><Bar value={v.score_pct} label={`${v.label} score`} /></div>
          ))}
        </CardContent></Card>
      )}
      <div className="grid gap-3 md:grid-cols-2">
        <Card><CardContent className="space-y-2 pt-4">
          <p className="text-sm font-semibold">By topic</p>
          {s.by_topic.length === 0 && <p className="text-xs text-muted-foreground">No scored answers yet.</p>}
          {s.by_topic.map((t) => (
            <div key={`${t.round}-${t.topic}`} className="space-y-1 text-xs"><div className="flex justify-between"><span>{t.label}</span><span>{fmtPct(t.score_pct)} · {t.attempted}</span></div><Bar value={t.score_pct} label={`${t.label} score`} tone={t.score_pct >= 75 ? "good" : t.score_pct < 60 ? "warn" : "primary"} /></div>
          ))}
        </CardContent></Card>
        <Card><CardContent className="space-y-2 pt-4 text-xs">
          <p className="text-sm font-semibold">Strong and weak areas</p>
          <p><span className="font-medium text-emerald-600">Strong:</span> {s.strengths.length ? s.strengths.join(", ") : "none identified yet"}</p>
          <p><span className="font-medium text-amber-600">Needs work:</span> {s.weak_areas.length ? s.weak_areas.join(", ") : "none below 60%"}</p>
          {s.suggestions.map((sg) => (
            <div key={sg.title} className="flex items-center justify-between gap-2 rounded-md border p-2">
              <div><p className="font-medium">{sg.title}</p><p className="text-muted-foreground">{sg.reason}</p></div>
              <Button size="sm" variant="outline" onClick={() => onAction(sg.action)}>Practise</Button>
            </div>
          ))}
        </CardContent></Card>
      </div>
      <p className="text-[11px] text-muted-foreground">{s.score_notes}</p>
      <Card><CardContent className="space-y-2 pt-4">
        <p className="text-sm font-semibold">Review your answers</p>
        {attempt.items.map((it) => (
          <div key={it.id} className="rounded-md border">
            <button type="button" aria-expanded={open === it.id} onClick={() => setOpen(open === it.id ? null : it.id)} className="flex w-full items-start justify-between gap-2 p-2 text-left text-xs">
              <span className="line-clamp-2">{it.position}. {it.prompt}</span>
              <span className="shrink-0">{it.result?.is_correct === true ? "✓ Correct" : it.result?.is_correct === false ? "✗ Wrong" : it.answered ? "Answered" : "Skipped"}</span>
            </button>
            {open === it.id && (
              <div className="space-y-2 border-t p-2">
                {it.qtype === "mcq" && it.options && (
                  <ul className="space-y-1 text-xs">
                    {it.options.map((o, i) => (
                      <li key={i} className={i === it.result?.correct_index ? "font-semibold text-emerald-600" : i === it.answer?.index ? "text-destructive" : ""}>
                        {i === it.result?.correct_index ? "✓ " : i === it.answer?.index ? "✗ " : "• "}{o}
                      </li>
                    ))}
                  </ul>
                )}
                {it.qtype !== "mcq" && it.answer?.text && <p className="whitespace-pre-wrap text-xs"><span className="font-semibold">Your answer: </span>{it.answer.text}</p>}
                {it.result && <FeedbackPanel item={it} />}
              </div>
            )}
          </div>
        ))}
      </CardContent></Card>
    </div>
  );
}
