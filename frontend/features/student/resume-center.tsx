"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileText, Lightbulb, UploadCloud } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from "@/components/ui/feedback";
import { api, ResumeSummary } from "@/lib/api";
import { useNotificationStore } from "@/store/useNotificationStore";
import { cn } from "@/lib/utils";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];
const MAX_BYTES = 5 * 1024 * 1024;

/** Client-side check mirroring the backend rules (PDF/DOCX, max 5 MB). */
function validateFile(file: File): string | null {
  if (!ACCEPTED_TYPES.includes(file.type)) return "Unsupported file type. Please upload a PDF or DOCX.";
  if (file.size === 0) return "That file is empty.";
  if (file.size > MAX_BYTES) return "File is too large. The limit is 5 MB.";
  return null;
}

export function ResumeCenterView() {
  const queryClient = useQueryClient();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [fileError, setFileError] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);

  const resumes = useQuery({
    queryKey: ["resumes"],
    queryFn: api.listResumes,
    // Status flips PROCESSING -> COMPLETED/FAILED in the background; keep polling until settled.
    refetchInterval: (query) => (query.state.data?.some((r) => r.status === "PROCESSING") ? 3000 : false),
  });
  const activeId = selectedId ?? resumes.data?.[0]?.id ?? null;
  const activeResume: ResumeSummary | undefined = resumes.data?.find((r) => r.id === activeId);

  // Analysis is produced asynchronously (upload returns 202); poll until it exists.
  const analysis = useQuery({
    queryKey: ["resume-analysis", activeId],
    queryFn: () => api.resumeAnalysis(activeId as string),
    enabled: Boolean(activeId),
    refetchInterval: (query) => (query.state.data ? false : 3000),
  });

  const notifiedRef = React.useRef<string | null>(null);
  React.useEffect(() => {
    if (analysis.data && notifiedRef.current !== analysis.data.id) {
      notifiedRef.current = analysis.data.id;
      addNotification("system", "Resume analysis ready", `ATS score: ${Math.round(analysis.data.ats_score)}/100`, "/workspace?tab=resume");
      void queryClient.invalidateQueries({ queryKey: ["student-dashboard"] });
    }
  }, [analysis.data, addNotification, queryClient]);

  const upload = useMutation({
    mutationFn: (file: File) => api.uploadResume(file),
    onSuccess: async (result) => {
      setNotice(`${result.file_name} uploaded. Analysis is running.`);
      setSelectedId(result.id);
      await queryClient.invalidateQueries({ queryKey: ["resumes"] });
    },
  });

  const download = useMutation({
    mutationFn: (id: string) => api.resumeDownload(id),
    onSuccess: ({ blob, filename }) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    },
  });

  const onFile = (file: File | undefined) => {
    setNotice(null);
    if (!file) return;
    const problem = validateFile(file);
    setFileError(problem);
    if (!problem) upload.mutate(file);
  };

  const result = analysis.data;

  return (
    <div className="space-y-8 text-left">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Resume Center</h1>
          <p className="text-sm text-muted-foreground">Check how complete, readable and well worded your resume is for applicant tracking systems (rule-based analysis).</p>
        </div>
        <Button variant="outline" onClick={() => inputRef.current?.click()} isLoading={upload.isPending}>
          Upload New Resume
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          className="hidden"
          onChange={(e) => {
            onFile(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </div>

      <SuccessBanner message={notice} />
      <ErrorBanner error={fileError ?? upload.error ?? download.error} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-5 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">Your Resumes</CardTitle>
              <CardDescription className="text-xs">PDF or DOCX, up to 5 MB.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {resumes.isLoading ? (
                <LoadingBlock />
              ) : resumes.error ? (
                <ErrorBanner error={resumes.error} onRetry={() => void resumes.refetch()} />
              ) : !resumes.data?.length ? (
                <button
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    onFile(e.dataTransfer.files?.[0]);
                  }}
                  onClick={() => inputRef.current?.click()}
                  className="w-full border-2 border-dashed rounded-xl p-8 flex flex-col items-center gap-2 hover:border-primary/50 transition-colors"
                >
                  <UploadCloud className="h-8 w-8 text-primary" />
                  <p className="text-sm font-semibold">Drag and drop your resume here</p>
                  <p className="text-xs text-muted-foreground">or click to browse</p>
                </button>
              ) : (
                resumes.data.map((r) => (
                  <div
                    key={r.id}
                    className={cn(
                      "flex items-center justify-between gap-3 p-3 rounded-xl border cursor-pointer",
                      r.id === activeId ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"
                    )}
                    onClick={() => setSelectedId(r.id)}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <FileText className="h-5 w-5 text-primary shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs font-semibold truncate">{r.file_name}</p>
                        <p className="text-[10px] text-muted-foreground">
                          {new Date(r.created_at).toLocaleString()} • {r.status}
                        </p>
                      </div>
                    </div>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label={`Download ${r.file_name}`}
                      disabled={download.isPending}
                      onClick={(e) => {
                        e.stopPropagation();
                        download.mutate(r.id);
                      }}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-7 space-y-6">
          {!activeResume ? (
            <Card>
              <CardContent>
                <EmptyState title="No analysis yet" description="Upload a resume to get your ATS score and suggestions." />
              </CardContent>
            </Card>
          ) : analysis.error ? (
            <ErrorBanner error={analysis.error} onRetry={() => void analysis.refetch()} />
          ) : !result ? (
            <Card>
              <CardContent>
                <LoadingBlock label={`Analysing ${activeResume.file_name}…`} />
              </CardContent>
            </Card>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold">ATS Analysis</CardTitle>
                  <CardDescription className="text-xs">{activeResume.file_name}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {result.keyword_analysis?.method === "rule_based_v1" ? (
                    <p className="rounded-md bg-muted/40 p-2 text-[11px] text-muted-foreground" data-testid="analysis-note">
                      Rule-based measurements of this document (readiness, wording and mechanics). They are not AI judgements and not
                      the output of any company&apos;s ATS.
                      {Array.isArray(result.keyword_analysis.warnings) && result.keyword_analysis.warnings.length > 0
                        ? ` ${(result.keyword_analysis.warnings as string[]).join(" ")}`
                        : ""}
                    </p>
                  ) : (
                    <p role="alert" className="rounded-md border border-amber-500/30 bg-amber-500/10 p-2 text-[11px] text-amber-700 dark:text-amber-400" data-testid="analysis-legacy">
                      This analysis came from an earlier simulated version and is NOT based on your file. Upload the résumé again
                      for a real analysis.
                    </p>
                  )}
                  {[
                    { label: "ATS readiness", value: result.ats_score, tone: "bg-indigo-500" },
                    { label: "Writing mechanics", value: result.grammar_score, tone: "bg-teal-500" },
                    { label: "Overall Quality", value: result.quality_score, tone: "bg-amber-500" },
                  ].map((m) => (
                    <div key={m.label} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span>{m.label}</span>
                        <span>{Math.round(m.value)}/100</span>
                      </div>
                      <Progress value={m.value} indicatorClassName={m.tone} />
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold flex items-center gap-2">
                    <Lightbulb className="h-4 w-4 text-amber-400" /> Suggestions
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {result.suggestions.length === 0 ? (
                    <p className="text-xs text-muted-foreground">No suggestions, your resume looks good.</p>
                  ) : (
                    result.suggestions.map((s, i) => (
                      <div key={i} className="p-3 rounded-xl border border-border text-xs space-y-1">
                        <div className="flex justify-between">
                          <span className="font-semibold">{s.category}</span>
                          <span className="text-[10px] text-muted-foreground">{s.impact} impact</span>
                        </div>
                        <p className="text-muted-foreground">{s.suggestion_text}</p>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>

              {Object.keys(result.keyword_analysis ?? {}).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base font-bold">Keyword Analysis</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-xs">
                    {Object.entries(result.keyword_analysis).map(([key, value]) => (
                      <div key={key}>
                        <p className="font-semibold capitalize mb-1">{key.replace(/_/g, " ")}</p>
                        {Array.isArray(value) ? (
                          <div className="flex flex-wrap gap-1.5">
                            {value.map((v) => (
                              <span key={String(v)} className="px-2 py-0.5 rounded-md bg-primary/10 text-primary text-[10px] font-semibold">
                                {String(v)}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <p className="text-muted-foreground">
                            {value !== null && typeof value === "object"
                              ? Object.entries(value as Record<string, unknown>)
                                  .map(([k, v]) => `${k.replace(/_/g, " ")}: ${typeof v === "boolean" ? (v ? "yes" : "no") : String(v)}`)
                                  .join(" · ")
                              : String(value)}
                          </p>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
