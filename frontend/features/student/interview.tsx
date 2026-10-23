"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Mic, Send } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { JsonView } from "@/components/ui/json-view";
import { api, errorMessage } from "@/lib/api";
import { SocketEvent, useSessionSocket } from "@/lib/useSessionSocket";
import { useNotificationStore } from "@/store/useNotificationStore";

const TYPES = ["TECHNICAL", "HR", "BEHAVIORAL", "SYSTEM_DESIGN"];
const DIFFICULTIES = ["EASY", "MEDIUM", "HARD"];

type Phase = "setup" | "live" | "finished";
interface Turn {
  role: "ai" | "user";
  text: string;
}

const selectClass =
  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-hidden focus:ring-2 focus:ring-ring";

export function InterviewStudioView() {
  const queryClient = useQueryClient();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [type, setType] = React.useState("TECHNICAL");
  const [difficulty, setDifficulty] = React.useState("MEDIUM");
  const [company, setCompany] = React.useState("");

  const [phase, setPhase] = React.useState<Phase>("setup");
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [turns, setTurns] = React.useState<Turn[]>([]);
  const [questionId, setQuestionId] = React.useState<string | null>(null);
  const [evaluating, setEvaluating] = React.useState(false);
  const [answer, setAnswer] = React.useState("");
  const [validation, setValidation] = React.useState<string | null>(null);

  const onEvent = React.useCallback((event: SocketEvent) => {
    if (event.event_type === "NEXT_QUESTION") {
      const p = event.payload ?? {};
      setQuestionId(String(p.question_id));
      setTurns((t) => [...t, { role: "ai", text: String(p.text) }]);
      setEvaluating(false);
    } else if (event.event_type === "EVALUATING") {
      setEvaluating(true);
    } else if (event.event_type === "INTERVIEW_COMPLETED") {
      setPhase("finished");
      setEvaluating(false);
    }
  }, []);

  const socket = useSessionSocket("interviews", onEvent);

  const start = useMutation({
    mutationFn: async () => {
      const session = await api.createInterviewSession({
        interview_type: type,
        difficulty,
        company: company.trim() || undefined,
      });
      await socket.connect(session.id);
      return session;
    },
    onSuccess: (session) => {
      setSessionId(session.id);
      setTurns([]);
      setQuestionId(null);
      setPhase("live");
      socket.send({ event_type: "START" });
    },
  });

  // The final report is produced after FINISH; poll until it is available.
  const report = useQuery({
    queryKey: ["interview-report", sessionId],
    queryFn: () => api.interviewReport(sessionId as string),
    enabled: phase === "finished" && Boolean(sessionId),
    refetchInterval: (query) => (query.state.data ? false : 2500),
  });

  const notified = React.useRef<string | null>(null);
  React.useEffect(() => {
    if (report.data && notified.current !== report.data.session_id) {
      notified.current = report.data.session_id;
      addNotification("interviews", "Interview report ready", `Overall score: ${Math.round(report.data.overall_score)}/100`, "/workspace?tab=interviews");
      void queryClient.invalidateQueries({ queryKey: ["student-dashboard"] });
    }
  }, [report.data, addNotification, queryClient]);

  const submitAnswer = (e: React.FormEvent) => {
    e.preventDefault();
    const text = answer.trim();
    if (!text) {
      setValidation("Type an answer before submitting.");
      return;
    }
    if (!questionId) return;
    setValidation(null);
    if (socket.send({ event_type: "ANSWER_SUBMITTED", payload: { question_id: questionId, answer_text: text } })) {
      setTurns((t) => [...t, { role: "user", text }]);
      setAnswer("");
      setQuestionId(null);
    }
  };

  const finish = () => {
    socket.send({ event_type: "FINISH" });
  };

  const reset = () => {
    socket.close();
    setPhase("setup");
    setSessionId(null);
    setTurns([]);
    start.reset();
  };

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
          <Mic className="h-7 w-7 text-primary" /> Interview Studio
        </h1>
        <p className="text-sm text-muted-foreground">Practise with reviewed interview questions and get a report. Scores are rule-based estimates of how well your answers cover the expected ideas, not an AI or recruiter judgement.</p>
      </div>

      {phase === "setup" && (
        <Card className="max-w-xl">
          <CardHeader>
            <CardTitle className="text-base font-bold">Configure your interview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ErrorBanner error={start.error ? errorMessage(start.error) : null} />
            <label className="text-[10px] font-semibold uppercase text-muted-foreground">Type</label>
            <select className={selectClass} value={type} onChange={(e) => setType(e.target.value)}>
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace("_", " ")}
                </option>
              ))}
            </select>
            <label className="text-[10px] font-semibold uppercase text-muted-foreground">Difficulty</label>
            <select className={selectClass} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              {DIFFICULTIES.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <label className="text-[10px] font-semibold uppercase text-muted-foreground">Target company (optional)</label>
            <Input value={company} onChange={(e) => setCompany(e.target.value)} placeholder="e.g. Stripe" />
            <Button className="w-full" isLoading={start.isPending} onClick={() => start.mutate()}>
              Start interview
            </Button>
          </CardContent>
        </Card>
      )}

      {phase === "live" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Live interview</CardTitle>
            <CardDescription className="text-xs">
              {type.replace("_", " ")} • {difficulty} {company ? `• ${company}` : ""} • connection: {socket.status}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3 max-h-[380px] overflow-y-auto rounded-xl bg-muted/30 p-4">
              {turns.length === 0 && <LoadingBlock label="Waiting for the first question…" />}
              {turns.map((t, i) => (
                <div
                  key={i}
                  className={
                    t.role === "ai"
                      ? "max-w-[85%] rounded-xl bg-card border border-border p-3 text-sm"
                      : "max-w-[85%] ml-auto rounded-xl bg-primary text-primary-foreground p-3 text-sm"
                  }
                >
                  {t.text}
                </div>
              ))}
              {evaluating && <p className="text-xs text-muted-foreground">Evaluating your answer…</p>}
            </div>
            <ErrorBanner error={validation ?? socket.error} />
            <form onSubmit={submitAnswer} className="flex gap-2">
              <Input
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder={questionId ? "Type your answer…" : "Waiting for the next question…"}
                disabled={!questionId}
              />
              <Button type="submit" size="icon" disabled={!questionId} aria-label="Submit answer">
                <Send className="h-4 w-4" />
              </Button>
            </form>
            <div className="flex justify-between">
              <Button variant="ghost" size="sm" onClick={reset}>
                Cancel
              </Button>
              <Button variant="outline" size="sm" onClick={finish} disabled={turns.length === 0}>
                Finish &amp; get report
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {phase === "finished" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Interview report</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ErrorBanner error={report.error} onRetry={() => void report.refetch()} />
            {!report.data ? (
              <LoadingBlock label="Generating your report…" />
            ) : (
              <>
                {[
                  ["Overall", report.data.overall_score],
                  ["Technical", report.data.technical_score],
                  ["Communication", report.data.communication_score],
                ].map(([label, value]) => (
                  <div key={String(label)} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span>{label}</span>
                      <span>{Math.round(Number(value))}/100</span>
                    </div>
                    <Progress value={Number(value)} indicatorClassName="bg-primary" />
                  </div>
                ))}
                <JsonView value={report.data.detailed_analysis} />
                {report.data.recommended_learning?.length ? (
                  <div>
                    <p className="text-[10px] font-semibold uppercase text-muted-foreground mb-1">Recommended learning</p>
                    <JsonView value={report.data.recommended_learning} />
                  </div>
                ) : null}
              </>
            )}
            <Button variant="outline" onClick={reset}>
              New interview
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
