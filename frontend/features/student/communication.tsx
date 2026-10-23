"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquareText, Send } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { JsonView } from "@/components/ui/json-view";
import { api, errorMessage } from "@/lib/api";
import { SocketEvent, useSessionSocket } from "@/lib/useSessionSocket";
import { useNotificationStore } from "@/store/useNotificationStore";

const MODES = ["WORKPLACE", "INTERVIEW", "PRESENTATION", "CASUAL"];

type Phase = "setup" | "live" | "finished";
interface Message {
  text: string;
  feedback?: { grammar_score?: number; feedbacks?: unknown };
}

const selectClass =
  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-hidden focus:ring-2 focus:ring-ring";

export function CommunicationCoachView() {
  const queryClient = useQueryClient();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [mode, setMode] = React.useState("WORKPLACE");
  const [phase, setPhase] = React.useState<Phase>("setup");
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [text, setText] = React.useState("");
  const [analyzing, setAnalyzing] = React.useState(false);
  const [validation, setValidation] = React.useState<string | null>(null);

  const onEvent = React.useCallback((event: SocketEvent) => {
    if (event.event_type === "ANALYZING") setAnalyzing(true);
    else if (event.event_type === "LIVE_FEEDBACK") {
      const p = event.payload ?? {};
      setAnalyzing(false);
      // Feedback belongs to the most recent user message still awaiting it.
      setMessages((all) => {
        const idx = [...all].reverse().findIndex((m) => !m.feedback);
        if (idx === -1) return all;
        const target = all.length - 1 - idx;
        return all.map((m, i) => (i === target ? { ...m, feedback: { grammar_score: Number(p.grammar_score), feedbacks: p.feedbacks } } : m));
      });
    } else if (event.event_type === "SESSION_COMPLETED") setPhase("finished");
  }, []);

  const socket = useSessionSocket("communication", onEvent);

  const start = useMutation({
    mutationFn: async () => {
      const session = await api.createCommunicationSession(mode);
      await socket.connect(session.id);
      return session;
    },
    onSuccess: (session) => {
      setSessionId(session.id);
      setMessages([]);
      setPhase("live");
      socket.send({ event_type: "START" });
    },
  });

  const report = useQuery({
    queryKey: ["communication-report", sessionId],
    queryFn: () => api.communicationReport(sessionId as string),
    enabled: phase === "finished" && Boolean(sessionId),
    refetchInterval: (query) => (query.state.data ? false : 2500),
  });

  const notified = React.useRef<string | null>(null);
  React.useEffect(() => {
    if (report.data && notified.current !== report.data.session_id) {
      notified.current = report.data.session_id;
      addNotification("learning", "Communication report ready", `Overall score: ${report.data.overall_score.toFixed(1)}/10`, "/workspace?tab=communication");
      void queryClient.invalidateQueries({ queryKey: ["student-dashboard"] });
    }
  }, [report.data, addNotification, queryClient]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const value = text.trim();
    if (!value) {
      setValidation("Write something to analyse first.");
      return;
    }
    setValidation(null);
    if (socket.send({ event_type: "MESSAGE_SUBMITTED", payload: { text: value } })) {
      setMessages((m) => [...m, { text: value }]);
      setText("");
    }
  };

  const reset = () => {
    socket.close();
    setPhase("setup");
    setSessionId(null);
    setMessages([]);
    start.reset();
  };

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
          <MessageSquareText className="h-7 w-7 text-primary" /> Communication Coach
        </h1>
        <p className="text-sm text-muted-foreground">Get feedback on tone, clarity, filler words and writing mechanics. These are text-based measurements, not AI; grammar is a mechanical check only and accent or dialect is never assessed.</p>
      </div>

      {phase === "setup" && (
        <Card className="max-w-xl">
          <CardHeader>
            <CardTitle className="text-base font-bold">Choose a scenario</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ErrorBanner error={start.error ? errorMessage(start.error) : null} />
            <select className={selectClass} value={mode} onChange={(e) => setMode(e.target.value)}>
              {MODES.map((m) => (
                <option key={m} value={m}>
                  {m.charAt(0) + m.slice(1).toLowerCase()}
                </option>
              ))}
            </select>
            <Button className="w-full" isLoading={start.isPending} onClick={() => start.mutate()}>
              Start session
            </Button>
          </CardContent>
        </Card>
      )}

      {phase === "live" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Live session</CardTitle>
            <CardDescription className="text-xs">Mode: {mode} • connection: {socket.status}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3 max-h-[380px] overflow-y-auto rounded-xl bg-muted/30 p-4">
              {messages.length === 0 && <p className="text-xs text-muted-foreground">Write a message to receive feedback.</p>}
              {messages.map((m, i) => (
                <div key={i} className="space-y-2">
                  <div className="ml-auto max-w-[85%] rounded-xl bg-primary text-primary-foreground p-3 text-sm">{m.text}</div>
                  {m.feedback && (
                    <div className="max-w-[85%] rounded-xl bg-card border border-border p-3 text-xs space-y-1">
                      <p className="font-semibold">Writing-mechanics score: {m.feedback.grammar_score}/10</p>
                      <JsonView value={m.feedback.feedbacks} />
                    </div>
                  )}
                </div>
              ))}
              {analyzing && <p className="text-xs text-muted-foreground">Analysing…</p>}
            </div>
            <ErrorBanner error={validation ?? socket.error} />
            <form onSubmit={submit} className="flex gap-2">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={2}
                placeholder="Type what you would say…"
                className="flex-1 rounded-md border border-input bg-background/50 px-3 py-2 text-sm focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
              />
              <Button type="submit" size="icon" aria-label="Analyse message">
                <Send className="h-4 w-4" />
              </Button>
            </form>
            <div className="flex justify-between">
              <Button variant="ghost" size="sm" onClick={reset}>
                Cancel
              </Button>
              <Button variant="outline" size="sm" onClick={() => socket.send({ event_type: "FINISH" })} disabled={messages.length === 0}>
                Finish &amp; get report
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {phase === "finished" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Session report</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ErrorBanner error={report.error} onRetry={() => void report.refetch()} />
            {!report.data ? (
              <LoadingBlock label="Generating your report…" />
            ) : (
              <>
                {[
                  ["Overall", report.data.overall_score],
                  ["Writing mechanics", report.data.grammar_score],
                  ["Vocabulary", report.data.vocabulary_score],
                  ["Tone", report.data.tone_score],
                  ["Filler-word control", report.data.fluency_score],
                ].map(([label, value]) => (
                  <div key={String(label)} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span>{label}</span>
                      <span>{Number(value)}/10</span>
                    </div>
                    <Progress value={Math.min(100, Number(value) * (Number(value) <= 10 ? 10 : 1))} indicatorClassName="bg-primary" />
                  </div>
                ))}
                {(
                  [
                    ["Strengths", report.data.strengths],
                    ["Weaknesses", report.data.weaknesses],
                    ["Improvement suggestions", report.data.improvement_suggestions],
                  ] as const
                ).map(([label, list]) =>
                  list.length ? (
                    <div key={label}>
                      <p className="text-[10px] font-semibold uppercase text-muted-foreground mb-1">{label}</p>
                      <ul className="list-disc pl-4 text-xs space-y-0.5">
                        {list.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null
                )}
              </>
            )}
            <Button variant="outline" onClick={reset}>
              New session
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
