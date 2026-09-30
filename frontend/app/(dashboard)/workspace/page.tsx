"use client";

import React, { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/useAuthStore";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { api } from "@/lib/api";

import { CareerDiscoveryView } from "@/features/student/career-discovery";
import { ResumeCenterView } from "@/features/student/resume-center";
import { CareerJourneyView } from "@/features/student/career-journey";
import { MentorWorkspaceView } from "@/features/student/mentor";
import { CommunicationCoachView } from "@/features/student/communication";
import { TrainingAcademyView } from "@/features/student/learning";
import { InterviewStudioView } from "@/features/student/interview";
import { ApplicationTracker, JobBoard, PlacementDrives } from "@/features/student/jobs";
import { RecruiterPortal } from "@/features/recruiter/recruiter-portal";
import { OfficerPortal } from "@/features/officer/officer-portal";
import { AdminPortal } from "@/features/admin/admin-portal";

import {
  Compass,
  FileText,
  GraduationCap,
  Briefcase,
  Mic,
  MessageSquareText,
  BookOpen,
  Bot,
  Sparkles,
} from "lucide-react";

function StudentOverview({ onOpen }: { onOpen: (tab: string) => void }) {
  const dashboard = useQuery({ queryKey: ["student-dashboard"], queryFn: api.studentDashboard });
  const s = dashboard.data;

  return (
    <div className="space-y-8 text-left">
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-8 border border-indigo-500/20 text-white shadow-xl">
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded-full text-xs text-indigo-300 font-semibold">
            <Sparkles className="h-3.5 w-3.5" /> Workspace Cockpit
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Your Productivity Command Hub</h1>
          <p className="text-sm text-indigo-200/80 max-w-2xl leading-relaxed">
            Analyse your resume, practise interviews and communication, follow your roadmap, and talk to your mentor in one place.
          </p>
        </div>
        <div className="absolute right-0 top-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />
      </div>

      <ErrorBanner error={dashboard.error} onRetry={() => void dashboard.refetch()} />
      {dashboard.isLoading ? (
        <LoadingBlock />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { label: "Career Readiness", value: s?.career_readiness ?? 0, tone: "bg-primary" },
            { label: "ATS Resume Score", value: s?.resume_score ?? 0, tone: "bg-indigo-500" },
            { label: "Interview Score", value: s?.interview_score ?? 0, tone: "bg-violet-500" },
          ].map((m) => (
            <Card key={m.label} hoverEffect>
              <CardHeader className="pb-2">
                <CardDescription className="text-xs font-semibold uppercase tracking-wider">{m.label}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-lg font-bold">{Math.round(m.value)}/100</p>
                <Progress value={m.value} indicatorClassName={m.tone} />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Workspace Navigation Gateways</CardTitle>
          <CardDescription className="text-xs">Quick jump directly into any workspace tool page.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
          {[
            { id: "discovery", label: "Career Discovery", desc: "Take the career assessment.", icon: Compass },
            { id: "resume", label: "Resume Center", desc: "Optimize your resume ATS scoring.", icon: FileText },
            { id: "careers", label: "Career Journey", desc: "Goals, milestones and roadmap progress.", icon: GraduationCap },
            { id: "mentor", label: "AI Mentor", desc: "Persistent conversation & advice.", icon: Bot },
            { id: "communication", label: "Communication Coach", desc: "Live grammar and tone feedback.", icon: MessageSquareText },
            { id: "academy", label: "Training Academy", desc: "Your personalised learning roadmap.", icon: BookOpen },
            { id: "interviews", label: "AI Interviews", desc: "Run live mock interviews.", icon: Mic },
            { id: "jobs-prep", label: "Jobs & Prep", desc: "Job board, tracker and drives.", icon: Briefcase },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onOpen(item.id)}
                className="flex items-start gap-4 p-4 border border-border bg-card/40 hover:bg-primary/5 hover:border-primary/30 transition-all rounded-xl text-left cursor-pointer group"
              >
                <div className="p-2.5 bg-primary/10 rounded-lg text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-semibold text-xs text-foreground">{item.label}</p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">{item.desc}</p>
                </div>
              </button>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}

function JobsPrep() {
  const [tab, setTab] = React.useState("board");
  return (
    <Tabs value={tab} onValueChange={setTab}>
      <TabsList className="mb-4 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30">
        <TabsTrigger value="board" className="text-xs">Job Board</TabsTrigger>
        <TabsTrigger value="tracker" className="text-xs">Application Tracker</TabsTrigger>
        <TabsTrigger value="drives" className="text-xs">Placement Drives</TabsTrigger>
      </TabsList>
      <TabsContent value="board"><JobBoard /></TabsContent>
      <TabsContent value="tracker"><ApplicationTracker /></TabsContent>
      <TabsContent value="drives"><PlacementDrives /></TabsContent>
    </Tabs>
  );
}

function WorkspaceContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuthStore();

  const tabParam = searchParams.get("tab") || "overview";

  const handleTabChange = (value: string) => {
    const params = new URLSearchParams(window.location.search);
    params.set("tab", value);
    router.push(`/workspace?${params.toString()}`);
  };

  if (!user) return null;

  if (user.role === "recruiter") return <RecruiterPortal />;
  if (user.role === "officer") return <OfficerPortal />;
  if (user.role === "admin") return <AdminPortal />;

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-primary">Workspace Hub</h1>
        <p className="text-sm text-muted-foreground">
          A unified suite for career alignment, ATS scanning, communication practice, lessons, and mock interviews.
        </p>
      </div>

      <Tabs value={tabParam} onValueChange={handleTabChange} className="w-full">
        <TabsList className="mb-6 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30 dark:bg-slate-950/40">
          <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
          <TabsTrigger value="discovery" className="text-xs">Career Discovery</TabsTrigger>
          <TabsTrigger value="resume" className="text-xs">Resume Center</TabsTrigger>
          <TabsTrigger value="careers" className="text-xs">Career Journey</TabsTrigger>
          <TabsTrigger value="mentor" className="text-xs">AI Mentor</TabsTrigger>
          <TabsTrigger value="communication" className="text-xs">Communication Coach</TabsTrigger>
          <TabsTrigger value="academy" className="text-xs">Training Academy</TabsTrigger>
          <TabsTrigger value="interviews" className="text-xs">AI Interviews</TabsTrigger>
          <TabsTrigger value="jobs-prep" className="text-xs">Jobs & Preparation</TabsTrigger>
        </TabsList>

        <TabsContent value="overview"><StudentOverview onOpen={handleTabChange} /></TabsContent>
        <TabsContent value="discovery" className="border-0 p-0 m-0"><CareerDiscoveryView /></TabsContent>
        <TabsContent value="resume"><ResumeCenterView /></TabsContent>
        <TabsContent value="careers"><CareerJourneyView /></TabsContent>
        <TabsContent value="mentor"><MentorWorkspaceView /></TabsContent>
        <TabsContent value="communication"><CommunicationCoachView /></TabsContent>
        <TabsContent value="academy"><TrainingAcademyView /></TabsContent>
        <TabsContent value="interviews"><InterviewStudioView /></TabsContent>
        <TabsContent value="jobs-prep"><JobsPrep /></TabsContent>
      </Tabs>
    </div>
  );
}

export default function WorkspacePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-[400px] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      }
    >
      <WorkspaceContent />
    </Suspense>
  );
}
