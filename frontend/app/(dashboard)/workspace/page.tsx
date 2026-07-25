"use client";

import React, { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";

// Student component imports
import CareerDiscovery from "../discovery/page";
import ResumeCenter from "../resume/page";
import CareerDashboard from "../careers/page";
import JobsDashboard from "../jobs/page";

// Shared features/module screens imports
import {
  CommunicationCoach,
  InterviewStudio,
  MentorWorkspace,
  PortalDashboard,
  TrainingAcademy,
} from "@/features/platform/module-screens";

// Other role dashboard page imports
import RecruiterDashboard from "../recruiter/page";
import OfficerDashboard from "../officer/page";
import AdminDashboard from "../admin/page";

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
  ArrowRight,
  TrendingUp,
  Target,
  Trophy,
} from "lucide-react";

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

  // Overview panel for Student Workspace
  const StudentOverview = () => {
    return (
      <div className="space-y-8 text-left">
        {/* Welcome Header */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-8 border border-indigo-500/20 text-white shadow-xl">
          <div className="relative z-10 space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-500/20 border border-indigo-500/30 rounded-full text-xs text-indigo-300 font-semibold">
              <Sparkles className="h-3.5 w-3.5" /> Workspace Cockpit
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">Your Productivity Command Hub</h1>
            <p className="text-sm text-indigo-200/80 max-w-2xl leading-relaxed">
              Synthesize resume versions, practice speech, execute live mock interviews, and access lessons without leaving this unified productivity environment.
            </p>
          </div>
          <div className="absolute right-0 top-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />
        </div>

        {/* Workspace Quick Insights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card hoverEffect>
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-semibold uppercase tracking-wider">Target Pathway</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-lg font-bold text-slate-100">Lead Frontend Architect</p>
              <div className="flex items-center gap-2 text-xs text-emerald-500 font-semibold">
                <TrendingUp className="h-4 w-4" /> 92% Compatibility
              </div>
              <Progress value={92} indicatorClassName="bg-primary" />
            </CardContent>
          </Card>

          <Card hoverEffect>
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-semibold uppercase tracking-wider">AI Speech Confidence</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-lg font-bold text-slate-100">82% Strength Rating</p>
              <p className="text-xs text-muted-foreground">Filler Words: 6/min (Low)</p>
              <Progress value={82} indicatorClassName="bg-indigo-500" />
            </CardContent>
          </Card>

          <Card hoverEffect>
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-semibold uppercase tracking-wider">Interview Status</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-lg font-bold text-slate-100">82% Readiness Index</p>
              <p className="text-xs text-muted-foreground">React 19 Tech Screen: Strong</p>
              <Progress value={82} indicatorClassName="bg-violet-500" />
            </CardContent>
          </Card>
        </div>

        {/* Gateway Action List */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Workspace Navigation Gateways</CardTitle>
            <CardDescription className="text-xs">Quick jump directly into any workspace tool page.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
            {[
              { id: "discovery", label: "Career Discovery", desc: "Interact with AI onboarding chat.", icon: Compass },
              { id: "resume", label: "Resume Center", desc: "Optimize your resume ATS scoring.", icon: FileText },
              { id: "careers", label: "Career Dashboard", desc: "Track pathway timelines & skill gaps.", icon: GraduationCap },
              { id: "mentor", label: "AI Mentor", desc: "Access persistent conversation & chat.", icon: Bot },
              { id: "communication", label: "Speech Coach", desc: "Run speaking speed diagnostics.", icon: MessageSquareText },
              { id: "academy", label: "Training Academy", desc: "Access structured video & course lessons.", icon: BookOpen },
              { id: "interviews", label: "AI Interviews", desc: "Run simulated voice screening tests.", icon: Mic },
              { id: "jobs-prep", label: "Jobs & Prep", desc: "View recommended jobs & tracker.", icon: Briefcase },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabChange(item.id)}
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
  };

  // Student Workspace tabs rendering
  if (user.role === "student") {
    return (
      <div className="space-y-6 text-left">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-primary">Workspace Hub</h1>
          <p className="text-sm text-muted-foreground">
            A unified suite for career alignment, ATS scanning, speaking metrics, lessons, and mock test screens.
          </p>
        </div>

        <Tabs value={tabParam} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-6 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30 dark:bg-slate-950/40">
            <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
            <TabsTrigger value="discovery" className="text-xs">Career Discovery</TabsTrigger>
            <TabsTrigger value="resume" className="text-xs">Resume Center</TabsTrigger>
            <TabsTrigger value="careers" className="text-xs">Career Dashboard</TabsTrigger>
            <TabsTrigger value="mentor" className="text-xs">AI Mentor</TabsTrigger>
            <TabsTrigger value="communication" className="text-xs">Communication Coach</TabsTrigger>
            <TabsTrigger value="academy" className="text-xs">Training Academy</TabsTrigger>
            <TabsTrigger value="interviews" className="text-xs">AI Interviews</TabsTrigger>
            <TabsTrigger value="jobs-prep" className="text-xs">Jobs & Preparation</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <StudentOverview />
          </TabsContent>
          <TabsContent value="discovery" className="border-0 p-0 m-0">
            <CareerDiscovery />
          </TabsContent>
          <TabsContent value="resume">
            <ResumeCenter />
          </TabsContent>
          <TabsContent value="careers">
            <CareerDashboard />
          </TabsContent>
          <TabsContent value="mentor">
            <MentorWorkspace />
          </TabsContent>
          <TabsContent value="communication">
            <CommunicationCoach />
          </TabsContent>
          <TabsContent value="academy">
            <TrainingAcademy />
          </TabsContent>
          <TabsContent value="interviews">
            <InterviewStudio />
          </TabsContent>
          <TabsContent value="jobs-prep">
            <JobsDashboard />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  // Recruiter Workspace tabs rendering
  if (user.role === "recruiter") {
    return (
      <div className="space-y-6 text-left">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-primary">Hiring Hub Workspace</h1>
          <p className="text-sm text-muted-foreground">
            Manage candidates, openings, interview schedules, and placement audits.
          </p>
        </div>

        <Tabs value={tabParam} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-6 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30 dark:bg-slate-950/40">
            <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
            <TabsTrigger value="post-job" className="text-xs">Post Job</TabsTrigger>
            <TabsTrigger value="manage-jobs" className="text-xs">Manage Jobs</TabsTrigger>
            <TabsTrigger value="candidates" className="text-xs">Candidate Search</TabsTrigger>
            <TabsTrigger value="scheduling" className="text-xs">Scheduling</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <RecruiterDashboard />
          </TabsContent>
          <TabsContent value="post-job">
            <PortalDashboard type="recruiter" />
          </TabsContent>
          <TabsContent value="manage-jobs">
            <PortalDashboard type="recruiter" />
          </TabsContent>
          <TabsContent value="candidates">
            <PortalDashboard type="recruiter" />
          </TabsContent>
          <TabsContent value="scheduling">
            <PortalDashboard type="recruiter" />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  // Placement Officer Workspace tabs rendering
  if (user.role === "officer") {
    return (
      <div className="space-y-6 text-left">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-primary">Placement Officer Workspace</h1>
          <p className="text-sm text-muted-foreground">
            Track departmental placements, assign student courses, and review simulated performance charts.
          </p>
        </div>

        <Tabs value={tabParam} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-6 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30 dark:bg-slate-950/40">
            <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
            <TabsTrigger value="students" className="text-xs">Students</TabsTrigger>
            <TabsTrigger value="departments" className="text-xs">Departments</TabsTrigger>
            <TabsTrigger value="training" className="text-xs">Training Assignment</TabsTrigger>
            <TabsTrigger value="mock-interviews" className="text-xs">Mock Interviews</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OfficerDashboard />
          </TabsContent>
          <TabsContent value="students">
            <PortalDashboard type="officer" />
          </TabsContent>
          <TabsContent value="departments">
            <PortalDashboard type="officer" />
          </TabsContent>
          <TabsContent value="training">
            <PortalDashboard type="officer" />
          </TabsContent>
          <TabsContent value="mock-interviews">
            <PortalDashboard type="officer" />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  // Admin Workspace tabs rendering
  if (user.role === "admin") {
    return (
      <div className="space-y-6 text-left">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-primary">System Admin Workspace</h1>
          <p className="text-sm text-muted-foreground">
            Manage colleges, user databases, learning databases, moderations, and health monitoring logs.
          </p>
        </div>

        <Tabs value={tabParam} onValueChange={handleTabChange} className="w-full">
          <TabsList className="mb-6 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30 dark:bg-slate-950/40">
            <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
            <TabsTrigger value="users" className="text-xs">Users</TabsTrigger>
            <TabsTrigger value="recruiters" className="text-xs">Recruiters</TabsTrigger>
            <TabsTrigger value="colleges" className="text-xs">Colleges</TabsTrigger>
            <TabsTrigger value="content" className="text-xs">Learning Content</TabsTrigger>
            <TabsTrigger value="moderation" className="text-xs">Moderation</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <AdminDashboard />
          </TabsContent>
          <TabsContent value="users">
            <PortalDashboard type="admin" />
          </TabsContent>
          <TabsContent value="recruiters">
            <PortalDashboard type="admin" />
          </TabsContent>
          <TabsContent value="colleges">
            <PortalDashboard type="admin" />
          </TabsContent>
          <TabsContent value="content">
            <PortalDashboard type="admin" />
          </TabsContent>
          <TabsContent value="moderation">
            <PortalDashboard type="admin" />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  return null;
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
