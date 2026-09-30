"use client";

import React from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { BrainCircuit, CheckCircle, Send } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { EmptyState, ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { JsonView } from "@/components/ui/json-view";
import { api, AnswerSubmission, AssessmentQuestion } from "@/lib/api";
import { useNotificationStore } from "@/store/useNotificationStore";

export function CareerDiscoveryView() {
  const addNotification = useNotificationStore((s) => s.addNotification);
  const templates = useQuery({ queryKey: ["discovery-templates"], queryFn: api.discoveryTemplates });
  const template = templates.data?.[0];
  const questions = React.useMemo(
    () => [...(template?.questions ?? [])].sort((a, b) => a.order_index - b.order_index),
    [template]
  );

  const [step, setStep] = React.useState(0);
  const [answers, setAnswers] = React.useState<Record<string, AnswerSubmission>>({});
  const [draft, setDraft] = React.useState("");
  const [validation, setValidation] = React.useState<string | null>(null);
  const [assessmentId, setAssessmentId] = React.useState<string | null>(null);

  const submit = useMutation({
    mutationFn: (all: AnswerSubmission[]) => api.submitAssessment(template!.id, all),
    onSuccess: (res) => setAssessmentId(res.assessment_id),
  });

  // The report is generated in the background after submit; poll until it exists.
  const report = useQuery({
    queryKey: ["discovery-report", assessmentId],
    queryFn: () => api.discoveryReport(assessmentId as string),
    enabled: Boolean(assessmentId),
    refetchInterval: (query) => (query.state.data ? false : 2500),
  });

  const notified = React.useRef(false);
  React.useEffect(() => {
    if (report.data && !notified.current) {
      notified.current = true;
      addNotification("learning", "Career report ready", "Your career discovery report has been generated.", "/workspace?tab=discovery");
    }
  }, [report.data, addNotification]);

  const current: AssessmentQuestion | undefined = questions[step];
  const isChoice = current?.question_type === "MULTIPLE_CHOICE" && (current.options?.length ?? 0) > 0;

  const record = (q: AssessmentQuestion, value: string): AnswerSubmission =>
    q.question_type === "MULTIPLE_CHOICE" ? { question_id: q.id, selected_options: [value] } : { question_id: q.id, answer_text: value };

  const advance = (value: string) => {
    if (!current) return;
    const trimmed = value.trim();
    if (!trimmed) {
      setValidation("Please provide an answer to continue.");
      return;
    }
    setValidation(null);
    const next = { ...answers, [current.id]: record(current, trimmed) };
    setAnswers(next);
    setDraft("");
    if (step + 1 < questions.length) setStep(step + 1);
    else submit.mutate(questions.map((q) => next[q.id]));
  };

  const restart = () => {
    setStep(0);
    setAnswers({});
    setDraft("");
    setAssessmentId(null);
    submit.reset();
    notified.current = false;
  };

  if (templates.isLoading) return <LoadingBlock label="Loading assessment…" />;
  if (templates.error) return <ErrorBanner error={templates.error} onRetry={() => void templates.refetch()} />;
  if (!template || questions.length === 0) {
    return (
      <EmptyState
        title="No assessment available"
        description="An administrator needs to publish a career assessment template before you can take it."
      />
    );
  }

  if (assessmentId) {
    return (
      <div className="space-y-6 text-left">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Your Career Report</h1>
          <p className="text-sm text-muted-foreground">{template.title}</p>
        </div>
        <ErrorBanner error={report.error} onRetry={() => void report.refetch()} />
        {!report.data ? (
          <LoadingBlock label="Analysing your answers…" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {(
              [
                ["Personality", report.data.personality_analysis],
                ["Interests", report.data.interest_analysis],
                ["Skill Gaps", report.data.skill_gaps],
                ["Career Timeline", report.data.career_timeline],
              ] as const
            ).map(([title, value]) => (
              <Card key={title}>
                <CardHeader>
                  <CardTitle className="text-base font-bold">{title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <JsonView value={value} />
                </CardContent>
              </Card>
            ))}
            {report.data.matches.length > 0 && (
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base font-bold">Career Matches</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {report.data.matches.map((m) => (
                    <div key={m.job_title} className="p-3 rounded-xl border border-border text-xs">
                      <div className="flex justify-between font-semibold">
                        <span>{m.job_title}</span>
                        <span>{Math.round(m.suitability_score)}% fit</span>
                      </div>
                      <p className="text-muted-foreground mt-1">{m.reasoning}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        )}
        <Button variant="outline" onClick={restart}>
          Retake assessment
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-left max-w-2xl">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
          <BrainCircuit className="h-7 w-7 text-primary" /> Career Discovery
        </h1>
        <p className="text-sm text-muted-foreground">{template.description ?? template.title}</p>
      </div>

      <Progress value={(step / questions.length) * 100} indicatorClassName="bg-primary" />

      <Card>
        <CardHeader>
          <CardDescription className="text-xs">
            Question {step + 1} of {questions.length}
          </CardDescription>
          <CardTitle className="text-base">{current?.question_text}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ErrorBanner error={validation ?? submit.error} />
          {isChoice ? (
            <div className="grid gap-2">
              {current!.options!.map((option) => (
                <Button key={option} variant="outline" className="justify-start" disabled={submit.isPending} onClick={() => advance(option)}>
                  {option}
                </Button>
              ))}
            </div>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                advance(draft);
              }}
              className="flex gap-2"
            >
              <Input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Type your answer…" autoFocus />
              <Button type="submit" isLoading={submit.isPending} className="gap-1">
                {step + 1 === questions.length ? (
                  <>
                    <CheckCircle className="h-4 w-4" /> Finish
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" /> Next
                  </>
                )}
              </Button>
            </form>
          )}
          {step > 0 && (
            <Button variant="ghost" size="sm" onClick={() => setStep(step - 1)} disabled={submit.isPending}>
              Back
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
