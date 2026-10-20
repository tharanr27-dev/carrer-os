"use client";

import React, { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Briefcase } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApplicationTracker, JobBoard, PlacementDrives } from "@/features/student/jobs";
import { RecommendedJobsBoard } from "@/features/student/recommended-jobs";
import { InterviewStudioView } from "@/features/student/interview";

// Older links used ?tab=portal for the board.
const BOARD_ALIASES = ["portal"];

function JobsDashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const rawTab = searchParams.get("tab") || "board";
  const tab = BOARD_ALIASES.includes(rawTab) ? "board" : rawTab;

  const handleTabChange = (value: string) => {
    const params = new URLSearchParams(window.location.search);
    params.set("tab", value);
    router.push(`/jobs?${params.toString()}`);
  };

  return (
    <div className="space-y-6 text-left">
      <div>
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-primary">
          <Briefcase className="h-3.5 w-3.5" />
          Job Command Center
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight">Jobs</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Browse open roles, explore recommended IT jobs, track your applications, register for placement drives, and prepare for interviews.
        </p>
      </div>

      <Tabs value={tab} onValueChange={handleTabChange}>
        <TabsList className="flex h-auto w-full flex-wrap justify-start gap-1 p-1 bg-muted/30 dark:bg-slate-950/40">
          <TabsTrigger value="board" className="text-xs">Job Board</TabsTrigger>
          <TabsTrigger value="recommended" className="text-xs">Recommended IT Jobs</TabsTrigger>
          <TabsTrigger value="tracker" className="text-xs">Application Tracker</TabsTrigger>
          <TabsTrigger value="drives" className="text-xs">Placement Drives</TabsTrigger>
          <TabsTrigger value="prep" className="text-xs">Interview Preparation</TabsTrigger>
        </TabsList>
        <TabsContent value="board"><JobBoard /></TabsContent>
        <TabsContent value="recommended"><RecommendedJobsBoard /></TabsContent>
        <TabsContent value="tracker"><ApplicationTracker /></TabsContent>
        <TabsContent value="drives"><PlacementDrives /></TabsContent>
        <TabsContent value="prep"><InterviewStudioView /></TabsContent>
      </Tabs>
    </div>
  );
}

export default function JobsDashboard() {
  return (
    <Suspense fallback={<div className="h-64 animate-pulse rounded-2xl bg-muted/20" />}>
      <JobsDashboardContent />
    </Suspense>
  );
}
