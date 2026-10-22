"use client";

import React from "react";
import { cn } from "@/lib/utils";
import type { TrainingRoundProgress } from "@/lib/api";

export const ROUND_LABELS: Record<string, string> = {
  aptitude: "Aptitude",
  technical: "Technical",
  coding: "Coding",
  communication: "Communication",
  hr: "HR",
  resume: "Resume & Projects",
  managerial: "Managerial / Final",
  mock: "Mock Interview",
};

export const STATUS_STYLE: Record<TrainingRoundProgress["status"] | "ready_for_review", { label: string; className: string }> = {
  not_started: { label: "Not started", className: "bg-muted text-muted-foreground" },
  in_progress: { label: "In progress", className: "bg-sky-500/10 text-sky-600 dark:text-sky-400" },
  needs_work: { label: "Needs work", className: "bg-amber-500/10 text-amber-600 dark:text-amber-400" },
  on_track: { label: "On track", className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" },
  strong: { label: "Strong", className: "bg-emerald-500/20 text-emerald-700 dark:text-emerald-300" },
  ready_for_review: { label: "Ready for review", className: "bg-violet-500/10 text-violet-600 dark:text-violet-400" },
};

export function StatusPill({ status }: { status: keyof typeof STATUS_STYLE }) {
  const s = STATUS_STYLE[status];
  return <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", s.className)}>{s.label}</span>;
}

export const fmtPct = (v: number | null | undefined) => (v == null ? "—" : `${Math.round(v)}%`);

export function fmtDuration(totalSec: number | null | undefined) {
  if (totalSec == null) return "—";
  const m = Math.floor(totalSec / 60);
  const s = Math.round(totalSec % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export function Bar({ value, label, tone = "primary" }: { value: number | null; label: string; tone?: "primary" | "good" | "warn" }) {
  const pct = value == null ? 0 : Math.max(0, Math.min(100, value));
  const color = tone === "good" ? "bg-emerald-500" : tone === "warn" ? "bg-amber-500" : "bg-primary";
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value == null ? undefined : Math.round(pct)}
      className="h-2 w-full overflow-hidden rounded-full bg-secondary dark:bg-slate-900"
    >
      <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
    </div>
  );
}

export function Chip({ children, tone = "muted" }: { children: React.ReactNode; tone?: "muted" | "warn" | "info" }) {
  const tones = {
    muted: "border bg-muted/40 text-muted-foreground",
    warn: "border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400",
    info: "border border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-400",
  };
  return <span className={cn("rounded px-2 py-0.5 text-[10px]", tones[tone])}>{children}</span>;
}

export const SCORE_KIND_LABEL: Record<string, string> = {
  objective: "Objective score",
  ai_estimate: "AI estimate",
  keyword_estimate: "Rule-based estimate",
  self_assessed: "Self-assessed",
};

export function SkeletonBlock({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3" role="status" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} data-testid="prep-skeleton" className="h-20 animate-pulse rounded-xl border bg-muted/30" />
      ))}
    </div>
  );
}
