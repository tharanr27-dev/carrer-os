"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Check, Search, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorBanner } from "@/components/ui/feedback";
import {
  api,
  RoleItem,
  RoleResolution,
  RoleReviewFilter,
  RoleSession,
  RoleSessionCreate,
  RoleStatus,
  RoleSummary,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { Bar, Chip, fmtPct, SkeletonBlock } from "./shared";

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-2 text-xs shadow-xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring";

const STATUS_TONE: Record<RoleStatus, string> = {
  correct: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
  partial: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
  incorrect: "bg-red-500/15 text-red-700 dark:text-red-300 border-red-500/30",
  manual_review: "bg-sky-500/15 text-sky-700 dark:text-sky-300 border-sky-500/30",
  unanswered: "bg-muted text-muted-foreground border-border",
};
const STATUS_TEXT: Record<RoleStatus, string> = {
  correct: "Correct",
  partial: "Partially Correct",
  incorrect: "Incorrect",
  manual_review: "Needs Manual Review",
  unanswered: "Unanswered",
};
const FILTERS: { value: RoleReviewFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "correct", label: "Correct" },
  { value: "partial", label: "Partially Correct" },
  { value: "incorrect", label: "Incorrect" },
  { value: "unanswered", label: "Unanswered" },
];

function StatusBadge({ status }: { status: RoleStatus }) {
  return <span className={cn("rounded-full border px-2 py-0.5 text-[10px] font-semibold", STATUS_TONE[status])}>{STATUS_TEXT[status]}</span>;
}

function useDebounced<T>(value: T, ms = 250): T {
  const [v, setV] = React.useState(value);
  React.useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

/** Entry point of the "Role Training" tab. */
export function RoleTraining() {
  const qc = useQueryClient();
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const session = useQuery({
    queryKey: ["role-session", sessionId],
    queryFn: () => api.roleSession(sessionId as string),
    enabled: !!sessionId,
    staleTime: 30_000, // a session we just started/answered is already in the cache; do not refetch it straight away
    retry: false,
  });

  const open = (s: RoleSession) => {
    qc.setQueryData(["role-session", s.id], s);
    setSessionId(s.id);
  };
  const leave = () => {
    setSessionId(null);
    void qc.invalidateQueries({ queryKey: ["role-sessions"] });
    void qc.invalidateQueries({ queryKey: ["role-progress"] });
    void qc.invalidateQueries({ queryKey: ["training-progress"] });
  };

  if (!sessionId) return <RoleSetup onStarted={open} onOpen={(id) => setSessionId(id)} />;
  if (session.isLoading) return <SkeletonBlock rows={3} />;
  if (session.error || !session.data) return <ErrorBanner error={session.error ?? "Could not load this session."} onRetry={() => void session.refetch()} />;
  return session.data.status === "COMPLETED" ? (
    <RoleReviewScreen session={session.data} onStarted={open} onLeave={leave} />
  ) : (
    <RoleRunner session={session.data} onLeave={leave} />
  );
}

// ───────────────────────────── setup ─────────────────────────────

function RoleSetup({ onStarted, onOpen }: { onStarted: (s: RoleSession) => void; onOpen: (id: string) => void }) {
  const [query, setQuery] = React.useState("");
  const [title, setTitle] = React.useState("");
  const [level, setLevel] = React.useState("");
  const [difficulty, setDifficulty] = React.useState("");
  const [count, setCount] = React.useState(10);
  const [topics, setTopics] = React.useState<string[]>([]);
  const [generate, setGenerate] = React.useState(true);
  const debounced = useDebounced(query.trim());

  const search = useQuery({ queryKey: ["role-search", debounced], queryFn: () => api.roleSearch(debounced), staleTime: 60_000, retry: false });
  const resolved = useQuery({
    queryKey: ["role-resolve", title],
    queryFn: () => api.roleResolve(title),
    enabled: title.length >= 2,
    retry: false,
  });
  const recent = useQuery({ queryKey: ["role-sessions", title || null], queryFn: () => api.roleSessions(title || undefined), retry: false });
  const start = useMutation({ mutationFn: (b: RoleSessionCreate) => api.roleSessionStart(b), onSuccess: onStarted });

  const pick = (t: string) => {
    setTitle(t);
    setTopics([]);
    start.reset();
  };
  const toggleTopic = (slug: string) => setTopics((cur) => (cur.includes(slug) ? cur.filter((x) => x !== slug) : [...cur, slug]));
  const r: RoleResolution | undefined = resolved.data;
  const canStart = !!r && r.can_start && !start.isPending;
  const typed = query.trim();
  const showCustom = typed.length >= 2 && search.data && !search.data.exact_match;

  return (
    <div className="space-y-5 text-left">
      <p className="text-sm text-muted-foreground">
        Prepare for any job role. Pick one from the list, or type your own job title. Questions are matched to the role, and every
        session gives you instant feedback and a full review.
      </p>

      <Card>
        <CardContent className="space-y-3 pt-5">
          <label htmlFor="role-search" className="text-xs font-semibold">Job role</label>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input id="role-search" className="pl-9" placeholder="Search or type a job title, e.g. Prompt Engineer" value={query}
              maxLength={60} onChange={(e) => setQuery(e.target.value)} />
          </div>
          {search.error ? <ErrorBanner error={search.error} onRetry={() => void search.refetch()} /> : null}
          <div className="flex flex-wrap gap-2" role="group" aria-label="Matching roles">
            {(search.data?.recent ?? []).filter((x) => !typed && x.title).map((x) => (
              <button key={x.key} type="button" onClick={() => pick(x.title)} className="rounded-full border border-dashed px-3 py-1 text-xs hover:bg-muted">
                Recent: {x.title}
              </button>
            ))}
            {(search.data?.roles ?? []).map((role) => (
              <button
                key={role.title} type="button" onClick={() => pick(role.title)} aria-pressed={title === role.title}
                className={cn("rounded-full border px-3 py-1 text-xs hover:bg-muted", title === role.title && "border-primary bg-primary/10 font-semibold")}
              >
                {role.title}
                <span className="ml-1 text-[10px] text-muted-foreground">{role.available_questions} reviewed</span>
              </button>
            ))}
            {showCustom && (
              <button type="button" onClick={() => pick(typed)} aria-pressed={title === typed}
                className={cn("rounded-full border border-dashed border-primary px-3 py-1 text-xs", title === typed && "bg-primary/10 font-semibold")}>
                Use custom title: &ldquo;{typed}&rdquo;
              </button>
            )}
          </div>
          {search.data && search.data.roles.length === 0 && !typed && <p className="text-xs text-muted-foreground">No roles to show.</p>}
        </CardContent>
      </Card>

      {title && (
        <Card>
          <CardContent className="space-y-4 pt-5">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-bold">{title}</h3>
              {r?.matched_title && r.matched_title !== title && <Chip tone="info">closest known role: {r.matched_title}</Chip>}
              {r && !r.mapped && <Chip tone="warn">custom role</Chip>}
            </div>
            {resolved.isLoading && <SkeletonBlock rows={1} />}
            {resolved.error ? <ErrorBanner error={resolved.error} onRetry={() => void resolved.refetch()} /> : null}
            {r && (
              <>
                {r.notes.map((n) => <p key={n} className="text-xs text-muted-foreground">{n}</p>)}
                <p className="text-xs text-muted-foreground">
                  {r.available_questions} reviewed question{r.available_questions === 1 ? "" : "s"} match this role; {r.unseen_questions} you have not seen yet.
                </p>
                {r.message && <p role="status" className="rounded-md border border-amber-500/30 bg-amber-500/10 p-2 text-xs text-amber-800 dark:text-amber-300">{r.message}</p>}
                {r.topics.length > 0 && (
                  <fieldset className="space-y-1.5">
                    <legend className="text-xs font-semibold">Topics (optional: leave empty for a balanced mix)</legend>
                    <div className="flex flex-wrap gap-2">
                      {r.topics.map((t) => (
                        <button key={t.slug} type="button" aria-pressed={topics.includes(t.slug)} onClick={() => toggleTopic(t.slug)}
                          className={cn("rounded-full border px-3 py-1 text-xs", topics.includes(t.slug) ? "border-primary bg-primary/10 font-semibold" : "hover:bg-muted")}>
                          {topics.includes(t.slug) && <Check className="mr-1 inline h-3 w-3" aria-hidden="true" />}
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </fieldset>
                )}
                <div className="grid gap-3 sm:grid-cols-3">
                  <label className="space-y-1 text-xs font-semibold">Experience level
                    <select className={selectClass} value={level} onChange={(e) => setLevel(e.target.value)}>
                      <option value="">Automatic{r.level_hint ? ` (${r.level_hint})` : ""}</option>
                      <option value="fresher">Fresher</option><option value="junior">Junior</option><option value="mid">Mid-level</option>
                    </select>
                  </label>
                  <label className="space-y-1 text-xs font-semibold">Difficulty
                    <select className={selectClass} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
                      <option value="">Adaptive (based on your results)</option>
                      <option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option>
                    </select>
                  </label>
                  <label className="space-y-1 text-xs font-semibold">Number of questions
                    <select className={selectClass} value={count} onChange={(e) => setCount(Number(e.target.value))}>
                      {[5, 8, 10, 15, 20, 30].map((n) => <option key={n} value={n}>{n}</option>)}
                    </select>
                  </label>
                </div>
                <label className="flex items-start gap-2 text-xs">
                  <input type="checkbox" className="mt-0.5" checked={generate && r.ai_available} disabled={!r.ai_available}
                    onChange={(e) => setGenerate(e.target.checked)} />
                  <span>
                    Use AI to create fresh questions when stored ones run out
                    {!r.ai_available && <span className="block text-muted-foreground">Not available: no AI provider is configured on this server.</span>}
                  </span>
                </label>
                <ErrorBanner error={start.error} />
                <Button
                  disabled={!canStart}
                  isLoading={start.isPending}
                  onClick={() => start.mutate({ role_title: title, level: (level || null) as RoleSessionCreate["level"], difficulty: (difficulty || null) as RoleSessionCreate["difficulty"], topics, count, generate: generate && r.ai_available })}
                >
                  Start practice <ArrowRight className="ml-1 h-4 w-4" aria-hidden="true" />
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}

      <section aria-label="Your role sessions" className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Your recent role sessions</h3>
        {recent.isLoading && <SkeletonBlock rows={1} />}
        {recent.data && recent.data.items.length === 0 && <EmptyState title="No role sessions yet" description="Pick a role above to start your first one." className="py-4" />}
        <ul className="space-y-1.5">
          {(recent.data?.items ?? []).map((s) => (
            <li key={s.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border p-2 text-xs">
              <span><strong>{s.role_title}</strong> · {s.answered}/{s.total_questions} answered · {s.status === "COMPLETED" ? `score ${fmtPct(s.percentage)}` : "in progress"}</span>
              <Button size="sm" variant="outline" onClick={() => onOpen(s.id)}>{s.status === "COMPLETED" ? "Open review" : "Continue"}</Button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

// ───────────────────────────── runner ─────────────────────────────

function ResultCard({ item }: { item: RoleItem }) {
  const r = item.result;
  if (!r) return null;
  return (
    <div className="space-y-2 rounded-lg border p-3 text-xs" aria-live="polite" data-testid="role-feedback">
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge status={r.status} />
        {r.marks != null && r.max_marks != null && <span className="font-semibold">{r.marks} / {r.max_marks} marks</span>}
        {r.status === "manual_review" && <span className="text-muted-foreground">Not scored</span>}
      </div>
      {item.qtype === "mcq" && r.correct_answer && (
        <p><span className="font-semibold">Correct answer: </span>{r.correct_answer}</p>
      )}
      {item.qtype === "text" && (
        <>
          {r.expected_concepts && r.expected_concepts.length > 0 && (
            <p><span className="font-semibold">Expected concepts: </span>{r.expected_concepts.join(", ")}</p>
          )}
          {r.model_answer && <p className="whitespace-pre-wrap"><span className="font-semibold">Model answer: </span>{r.model_answer}</p>}
        </>
      )}
      {r.explanation && <p className="whitespace-pre-wrap"><span className="font-semibold">Explanation: </span>{r.explanation}</p>}
      {r.got_right.length > 0 && (
        <div><p className="font-semibold text-emerald-700 dark:text-emerald-300">What you got right</p>
          <ul className="list-disc pl-5">{r.got_right.map((g) => <li key={g}>{g}</li>)}</ul></div>
      )}
      {r.missing.length > 0 && (
        <div><p className="font-semibold text-amber-700 dark:text-amber-300">What was missing or incorrect</p>
          <ul className="list-disc pl-5">{r.missing.map((g) => <li key={g}>{g}</li>)}</ul></div>
      )}
      {r.suggestion && <p><span className="font-semibold">Suggestion: </span>{r.suggestion}</p>}
      {r.disclaimer && <p className="text-[10px] text-muted-foreground">{r.disclaimer}</p>}
    </div>
  );
}

function QuestionChips({ item }: { item: RoleItem }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <Chip>{item.topic_label}</Chip>
      <Chip>{item.difficulty}</Chip>
      {item.kind && <Chip>{item.kind}</Chip>}
      {item.max_marks != null && <Chip>{item.max_marks} mark{item.max_marks === 1 ? "" : "s"}</Chip>}
      {item.is_repeat && <Chip tone="info">Seen before</Chip>}
      {item.source === "generated" && <Chip tone="warn">AI-generated · unreviewed, check the explanation</Chip>}
    </div>
  );
}

function RoleRunner({ session, onLeave }: { session: RoleSession; onLeave: () => void }) {
  const qc = useQueryClient();
  const items = session.items;
  const firstOpen = Math.max(0, items.findIndex((i) => !i.answered));
  const [cursor, setCursor] = React.useState(firstOpen);
  const [draft, setDraft] = React.useState<{ index?: number; text: string }>({ text: "" });
  const [startedAt, setStartedAt] = React.useState(() => Date.now());
  const cur = items[Math.min(cursor, items.length - 1)];
  const answeredCount = items.filter((i) => i.answered).length;
  const isLast = cursor >= items.length - 1;

  React.useEffect(() => {
    setDraft({ text: "" });
    setStartedAt(Date.now());
  }, [cursor]);

  const submit = useMutation({
    mutationFn: () =>
      api.roleSessionAnswer(session.id, {
        item_id: cur.id,
        ...(cur.qtype === "mcq" ? { index: draft.index } : { text: draft.text }),
        time_taken_sec: Math.round((Date.now() - startedAt) / 1000),
      }),
    onSuccess: (res) =>
      qc.setQueryData<RoleSession>(["role-session", session.id], (old) =>
        old ? { ...old, answered: old.items.filter((i) => i.answered || i.id === res.item.id).length, items: old.items.map((i) => (i.id === res.item.id ? res.item : i)) } : old
      ),
  });
  const finish = useMutation({
    mutationFn: () => api.roleSessionFinish(session.id),
    onSuccess: (s) => qc.setQueryData(["role-session", session.id], s),
  });

  if (!cur) return <EmptyState title="No questions" description="This session has no questions." />;
  const ready = cur.qtype === "mcq" ? draft.index !== undefined : draft.text.trim().length > 0;
  const unanswered = items.length - answeredCount;
  const go = (n: number) => {
    submit.reset();
    setCursor(Math.max(0, Math.min(items.length - 1, n)));
  };

  return (
    <div className="space-y-4 text-left">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs text-muted-foreground">{session.role.title} · {session.level} · {session.difficulty}</p>
          <p className="text-sm font-semibold" aria-live="polite">Question {cursor + 1} of {items.length} · {answeredCount} answered</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onLeave}>Save & exit</Button>
      </div>
      <Bar value={(answeredCount / items.length) * 100} label="Session progress" />

      {session.notices.map((n) => (
        <p key={n} role="status" className="rounded-md border border-sky-500/30 bg-sky-500/10 p-2 text-xs text-sky-800 dark:text-sky-300">{n}</p>
      ))}
      {session.plan && (
        <details className="rounded-md border p-2 text-xs">
          <summary className="cursor-pointer font-semibold">Why these questions?</summary>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
            {session.plan.notes.map((n) => <li key={n}>{n}</li>)}
            {session.plan.allocation.map((a) => <li key={a.topic}>{a.count} on {a.label}: {a.reason}</li>)}
          </ul>
        </details>
      )}

      <Card>
        <CardContent className="space-y-4 pt-5">
          <QuestionChips item={cur} />
          <h3 id="role-q" className="whitespace-pre-wrap text-sm font-semibold leading-relaxed">{cur.prompt}</h3>

          {cur.qtype === "mcq" && cur.options && (
            <div role="radiogroup" aria-labelledby="role-q" className="space-y-2">
              {cur.options.map((opt, i) => {
                const res = cur.result;
                const picked = cur.answered ? res?.your_answer?.index === i : draft.index === i;
                const isCorrect = cur.answered && res?.correct_index === i;
                return (
                  <label key={opt} className={cn("flex cursor-pointer items-start gap-2 rounded-lg border p-2.5 text-xs",
                    picked && "border-primary bg-primary/5", isCorrect && "border-emerald-500 bg-emerald-500/10", cur.answered && "cursor-default")}>
                    <input type="radio" name="role-option" className="mt-0.5" checked={picked} disabled={cur.answered}
                      onChange={() => setDraft({ ...draft, index: i })} />
                    <span>{opt}</span>
                  </label>
                );
              })}
            </div>
          )}
          {cur.qtype === "text" && (
            <div className="space-y-1">
              <label htmlFor="role-answer" className="text-xs font-semibold">Your answer</label>
              <textarea id="role-answer" rows={6} maxLength={6000} className={cn(selectClass, "h-auto w-full resize-y p-2 text-sm")}
                value={cur.answered ? cur.result?.your_answer?.text ?? "" : draft.text} readOnly={cur.answered}
                placeholder="Explain in your own words. Aim for the key ideas, with an example where it helps."
                onChange={(e) => setDraft({ ...draft, text: e.target.value })} />
            </div>
          )}

          <ErrorBanner error={submit.error} />
          {cur.answered ? <ResultCard item={cur} /> : null}

          <div className="flex flex-wrap items-center gap-2">
            {!cur.answered && (
              <Button onClick={() => submit.mutate()} disabled={!ready} isLoading={submit.isPending}>Submit Answer</Button>
            )}
            {!isLast && (
              <Button variant={cur.answered ? "default" : "outline"} onClick={() => go(cursor + 1)}>
                {cur.answered ? "Next Question" : "Skip"} <ArrowRight className="ml-1 h-4 w-4" aria-hidden="true" />
              </Button>
            )}
            {cursor > 0 && <Button variant="ghost" size="sm" onClick={() => go(cursor - 1)}>Previous</Button>}
            {(isLast || answeredCount === items.length) && (
              <Button variant={cur.answered ? "default" : "outline"} onClick={() => finish.mutate()} isLoading={finish.isPending}>
                Finish assessment
              </Button>
            )}
          </div>
          {!isLast && answeredCount < items.length && (
            <button type="button" className="text-[11px] text-muted-foreground underline" onClick={() => finish.mutate()}>
              Finish now ({unanswered} unanswered question{unanswered === 1 ? "" : "s"} will score 0)
            </button>
          )}
          <ErrorBanner error={finish.error} />
        </CardContent>
      </Card>
    </div>
  );
}

// ───────────────────────────── review ─────────────────────────────

function SummaryPanel({ s }: { s: RoleSummary }) {
  return (
    <Card>
      <CardContent className="space-y-4 pt-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs text-muted-foreground">{s.role_title} · {s.level} · {s.difficulty}</p>
            <p className="text-3xl font-extrabold" data-testid="role-score">{s.percentage == null ? "—" : `${Math.round(s.percentage)}%`}</p>
            <p className="text-xs text-muted-foreground">{s.marks_earned} of {s.marks_available} marks</p>
          </div>
          <dl className="grid grid-cols-3 gap-x-5 gap-y-1 text-center text-xs sm:grid-cols-6">
            {[["Questions", s.total_questions], ["Answered", s.answered], ["Unanswered", s.unanswered], ["Correct", s.correct],
              ["Partial", s.partial], ["Incorrect", s.incorrect]].map(([k, v]) => (
              <div key={String(k)}><dt className="text-muted-foreground">{k}</dt><dd className="text-base font-bold">{v}</dd></div>
            ))}
          </dl>
        </div>
        {s.manual_review > 0 && (
          <p className="text-xs text-sky-700 dark:text-sky-300">{s.manual_review} question(s) need manual review: they earn no marks and are left out of the total.</p>
        )}
        {s.topics.length > 0 && <p className="text-xs text-muted-foreground">Topics: {s.topics.join(", ")}</p>}
        <section aria-label="Topic-wise performance" className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Topic-wise performance</h4>
          {s.by_topic.map((t) => (
            <div key={t.topic} className="space-y-1">
              <div className="flex justify-between text-xs"><span>{t.label}</span><span>{t.pct == null ? "Not scored" : `${Math.round(t.pct)}%`} · {t.earned}/{t.available} marks</span></div>
              <Bar value={t.pct} label={`${t.label} score`} tone={t.pct != null && t.pct >= 75 ? "good" : t.pct != null && t.pct < 60 ? "warn" : "primary"} />
            </div>
          ))}
        </section>
        <div className="grid gap-3 sm:grid-cols-2 text-xs">
          <div><p className="font-semibold text-emerald-700 dark:text-emerald-300">Strong areas</p>
            <p className="text-muted-foreground">{s.strong_topics.length ? s.strong_topics.join(", ") : "None yet (75% or more in a topic)."}</p></div>
          <div><p className="font-semibold text-amber-700 dark:text-amber-300">Weak areas</p>
            <p className="text-muted-foreground">{s.weak_topics.length ? s.weak_topics.join(", ") : "None below 60%."}</p></div>
        </div>
        {s.revision.length > 0 && (
          <div className="text-xs"><p className="font-semibold">Suggested topics for revision</p>
            <ul className="list-disc pl-5 text-muted-foreground">{s.revision.map((r) => <li key={r.topic + r.reason}><strong>{r.label}</strong>: {r.reason}</li>)}</ul></div>
        )}
        <details className="text-xs"><summary className="cursor-pointer font-semibold">How this score is calculated</summary>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">{s.scoring_rules.map((r) => <li key={r}>{r}</li>)}</ul></details>
      </CardContent>
    </Card>
  );
}

function ReviewItem({ item }: { item: RoleItem }) {
  const r = item.result;
  const yours = item.qtype === "mcq" && r?.your_answer?.index != null && item.options ? item.options[r.your_answer.index] : r?.your_answer?.text;
  return (
    <li className="space-y-2 rounded-xl border p-3 text-xs" data-testid="review-item">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-semibold">Q{item.position}</span>
        <span className="flex items-center gap-2">
          {r && <StatusBadge status={r.status} />}
          {r?.marks != null && r.max_marks != null && <span className="font-semibold">{r.marks}/{r.max_marks}</span>}
        </span>
      </div>
      <QuestionChips item={item} />
      <p className="whitespace-pre-wrap text-sm font-medium">{item.prompt}</p>
      <p className="whitespace-pre-wrap"><span className="font-semibold">Your answer: </span>{yours || "— not answered"}</p>
      {r && <ResultCard item={item} />}
    </li>
  );
}

function RoleReviewScreen({ session, onStarted, onLeave }: { session: RoleSession; onStarted: (s: RoleSession) => void; onLeave: () => void }) {
  const [filter, setFilter] = React.useState<RoleReviewFilter>("all");
  const review = useQuery({ queryKey: ["role-review", session.id, filter], queryFn: () => api.roleSessionReview(session.id, filter), retry: false });
  const again = useMutation({
    mutationFn: (focus: "mixed" | "weak") => api.roleSessionAgain(session.id, focus),
    onSuccess: onStarted,
  });
  const summary = session.summary;
  const counts = review.data?.counts;
  const filters = [...FILTERS, ...(counts && counts.manual_review > 0 ? [{ value: "manual_review" as RoleReviewFilter, label: "Needs Manual Review" }] : [])];

  return (
    <div className="space-y-4 text-left">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-bold">Assessment review</h2>
        <Button variant="ghost" size="sm" onClick={onLeave}>Choose another role</Button>
      </div>
      {summary && <SummaryPanel s={summary} />}

      <div className="flex flex-wrap items-center gap-2">
        <Button onClick={() => again.mutate("mixed")} isLoading={again.isPending && again.variables === "mixed"} disabled={again.isPending}>
          <Sparkles className="mr-1 h-4 w-4" aria-hidden="true" /> Practise Again
        </Button>
        <Button variant="outline" onClick={() => again.mutate("weak")} isLoading={again.isPending && again.variables === "weak"} disabled={again.isPending}>
          Improve Weak Areas
        </Button>
        <span className="text-[11px] text-muted-foreground">New sessions prefer questions you have not seen and use this result to choose topics.</span>
      </div>
      <ErrorBanner error={again.error} />

      <div role="tablist" aria-label="Review filter" className="flex flex-wrap gap-1.5">
        {filters.map((f) => (
          <button key={f.value} role="tab" aria-selected={filter === f.value} onClick={() => setFilter(f.value)}
            className={cn("rounded-md border px-3 py-1.5 text-xs", filter === f.value ? "border-primary bg-primary/10 font-semibold" : "hover:bg-muted")}>
            {f.label}{counts ? ` (${counts[f.value]})` : ""}
          </button>
        ))}
      </div>
      {review.isLoading && <SkeletonBlock rows={2} />}
      {review.error ? <ErrorBanner error={review.error} onRetry={() => void review.refetch()} /> : null}
      {review.data && review.data.items.length === 0 && <EmptyState title="Nothing in this filter" description="No questions match this filter." className="py-4" />}
      <ul className="space-y-3">{(review.data?.items ?? []).map((it) => <ReviewItem key={it.id} item={it} />)}</ul>
    </div>
  );
}
