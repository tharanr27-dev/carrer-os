"use client";

import React, { Suspense } from "react";
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ApplicationTracker, GlobalSearch, InterviewStudio, JobPortal } from "@/features/platform/module-screens";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Briefcase,
  Building2,
  FileText,
  MapPin,
  DollarSign,
  Star,
  Bookmark,
  Zap,
  CheckCircle,
  FileWarning,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Job {
  id: string;
  role: string;
  company: string;
  rating: number;
  location: string;
  salary: string;
  type: string;
  matchScore: number;
  experience: string;
  remote: boolean;
  missingSkills: string[];
  skillsMatched: string[];
}

const mockJobs: Job[] = [
  {
    id: "job-1",
    role: "Software Engineer (Frontend)",
    company: "Stripe",
    rating: 4.8,
    location: "New York / Remote",
    salary: "$130k - $160k",
    type: "Full-Time",
    matchScore: 94,
    experience: "1-3 years",
    remote: true,
    missingSkills: ["Tailwind CSS v4", "Docker"],
    skillsMatched: ["React", "TypeScript", "Next.js", "State Management"],
  },
  {
    id: "job-2",
    role: "Front-End Architect",
    company: "Vercel",
    rating: 4.9,
    location: "Remote",
    salary: "$140k - $170k",
    type: "Full-Time",
    matchScore: 91,
    experience: "3+ years",
    remote: true,
    missingSkills: ["Server Actions", "CI/CD"],
    skillsMatched: ["Next.js", "TypeScript", "React 19", "CDNs"],
  },
  {
    id: "job-3",
    role: "Product Developer (React)",
    company: "Linear",
    rating: 4.7,
    location: "San Francisco / Hybrid",
    salary: "$120k - $145k",
    type: "Full-Time",
    matchScore: 86,
    experience: "1-3 years",
    remote: false,
    missingSkills: ["System Design", "SQL"],
    skillsMatched: ["React", "TypeScript", "UI/UX Fidelity"],
  },
  {
    id: "job-4",
    role: "React Developer Intern",
    company: "Supabase",
    rating: 4.6,
    location: "Remote",
    salary: "$80k - $105k",
    type: "Internship",
    matchScore: 78,
    experience: "Intern",
    remote: true,
    missingSkills: ["PostgreSQL", "Docker"],
    skillsMatched: ["React", "TypeScript", "API Integration"],
  },
];

function JobsDashboardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const tabParam = searchParams.get("tab") || "recommended";

  const handleTabChange = (value: string) => {
    const params = new URLSearchParams(window.location.search);
    params.set("tab", value);
    router.push(`/jobs?${params.toString()}`);
  };

  return (
    <div className="space-y-6 text-left">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-primary">
            <Briefcase className="h-3.5 w-3.5" />
            Job Command Center
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Jobs</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Matched jobs, search, saved roles, application tracking, company intelligence, and interview preparation in one place.
          </p>
        </div>
      </div>

      <Tabs value={tabParam} onValueChange={handleTabChange}>
        <TabsList className="flex h-auto w-full flex-wrap justify-start gap-1 p-1 bg-muted/30 dark:bg-slate-950/40">
          <TabsTrigger value="recommended" className="text-xs">Recommended Jobs</TabsTrigger>
          <TabsTrigger value="portal" className="text-xs">Job Portal</TabsTrigger>
          <TabsTrigger value="saved" className="text-xs">Saved Jobs</TabsTrigger>
          <TabsTrigger value="tracker" className="text-xs">Application Tracker</TabsTrigger>
          <TabsTrigger value="prep" className="text-xs">Interview Preparation</TabsTrigger>
          <TabsTrigger value="search" className="text-xs">Global Search</TabsTrigger>
          <TabsTrigger value="company" className="text-xs">Company Details</TabsTrigger>
          <TabsTrigger value="details" className="text-xs">Job Details</TabsTrigger>
        </TabsList>
        <TabsContent value="recommended"><RecommendedJobsPanel /></TabsContent>
        <TabsContent value="portal"><JobPortal /></TabsContent>
        <TabsContent value="saved"><SavedJobsPanel /></TabsContent>
        <TabsContent value="tracker"><ApplicationTracker /></TabsContent>
        <TabsContent value="prep"><InterviewStudio /></TabsContent>
        <TabsContent value="search"><GlobalSearch /></TabsContent>
        <TabsContent value="company"><CompanyDetailsPanel /></TabsContent>
        <TabsContent value="details"><JobDetailsPanel /></TabsContent>
      </Tabs>
    </div>
  );
}

export default function JobsDashboard() {
  return (
    <Suspense
      fallback={
        <div className="flex h-[400px] items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      }
    >
      <JobsDashboardContent />
    </Suspense>
  );
}

function RecommendedJobsPanel() {
  const [jobs] = React.useState<Job[]>(mockJobs);
  const [savedJobs, setSavedJobs] = React.useState<string[]>([]);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedJobForPrep, setSelectedJobForPrep] = React.useState<Job | null>(null);
  const [isPrepModalOpen, setIsPrepModalOpen] = React.useState(false);
  const [isPrepping, setIsPrepping] = React.useState(false);
  const [prepProgress, setPrepProgress] = React.useState(0);
  const [appliedJobs, setAppliedJobs] = React.useState<string[]>([]);

  const toggleSave = (id: string) => {
    setSavedJobs((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleApply = (id: string) => {
    if (appliedJobs.includes(id)) return;
    setAppliedJobs([...appliedJobs, id]);
  };

  const runMockPrep = () => {
    setIsPrepping(true);
    setPrepProgress(0);
    const interval = setInterval(() => {
      setPrepProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            setIsPrepping(false);
            setIsPrepModalOpen(false);
            alert("AI Prep Course completed! Mock test scores and solutions synced to your Profile.");
          }, 800);
          return 100;
        }
        return prev + 25;
      });
    }, 200);
  };

  const filteredJobs = jobs.filter((j) =>
    j.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
    j.company.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8 text-left">
      {/* Top Header */}
      <div>
        <h2 className="text-2xl font-extrabold tracking-tight">Recommended Jobs</h2>
        <p className="text-sm text-muted-foreground">
          Real-time matched job opportunities with instant AI interview simulations.
        </p>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex flex-col md:flex-row gap-3 w-full">
        <div className="relative flex-1">
          <Input
            type="text"
            placeholder="Search by role, company, or tech stack..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-11"
          />
          <Briefcase className="absolute left-3 top-3.5 h-4.5 w-4.5 text-muted-foreground" />
        </div>
        <Button variant="outline" className="h-11 flex gap-2 cursor-pointer">
          <SlidersHorizontal className="h-4 w-4" /> Filters
        </Button>
      </div>

      {/* Job list grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredJobs.map((job) => {
          const isSaved = savedJobs.includes(job.id);
          const hasApplied = appliedJobs.includes(job.id);

          return (
            <Card key={job.id} hoverEffect className="flex flex-col h-full justify-between relative">
              {/* Subtle top indicator glow for high match */}
              {job.matchScore >= 90 && (
                <div className="absolute top-0 inset-x-0 h-[1.5px] bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent" />
              )}

              {/* Card Header */}
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1 text-left">
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-slate-100">{job.role}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold">
                      <span>{job.company}</span>
                      <span className="flex items-center gap-0.5 text-amber-400"><Star className="h-3 w-3 fill-current" /> {job.rating}</span>
                    </div>
                  </div>

                  {/* Radial Gauge Match Score */}
                  <div className="relative flex items-center justify-center h-12 w-12 shrink-0">
                    <svg className="w-12 h-12 transform -rotate-90">
                      <circle cx="24" cy="24" r="20" stroke="currentColor" className="text-muted/10" strokeWidth="3" fill="transparent" />
                      <circle
                        cx="24"
                        cy="24"
                        r="20"
                        stroke="currentColor"
                        className={cn(
                          job.matchScore >= 90 ? "text-indigo-500" : "text-violet-500"
                        )}
                        strokeWidth="3"
                        fill="transparent"
                        strokeDasharray={`${2 * Math.PI * 20}`}
                        strokeDashoffset={`${2 * Math.PI * 20 * (1 - job.matchScore / 100)}`}
                      />
                    </svg>
                    <span className="absolute text-[10px] font-bold">{job.matchScore}%</span>
                  </div>
                </div>
              </CardHeader>

              {/* Card Content details */}
              <CardContent className="space-y-4 flex-1">
                {/* Meta details */}
                <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-[11px] text-muted-foreground font-medium">
                  <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {job.location}</span>
                  <span className="flex items-center gap-1"><DollarSign className="h-3.5 w-3.5" /> {job.salary}</span>
                  <span className="flex items-center gap-1"><Briefcase className="h-3.5 w-3.5" /> {job.experience}</span>
                </div>

                {/* Badges */}
                <div className="flex flex-wrap gap-1.5">
                  <span className="text-[9px] px-2 py-0.5 rounded-md bg-muted text-muted-foreground font-semibold uppercase">{job.type}</span>
                  {job.remote && (
                    <span className="text-[9px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold uppercase">Remote Friendly</span>
                  )}
                </div>

                {/* Missing Skills Indicator */}
                {job.missingSkills.length > 0 && (
                  <div className="p-2.5 rounded-lg bg-amber-500/5 border border-amber-500/10 space-y-1 text-left">
                    <p className="text-[10px] text-amber-400 font-semibold flex items-center gap-1">
                      <FileWarning className="h-3 w-3" /> Missing {job.missingSkills.length} recruiter terms:
                    </p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {job.missingSkills.map((s) => (
                        <span key={s} className="text-[9px] px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 font-semibold">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>

              {/* Footer Actions */}
              <CardFooter className="flex items-center justify-between border-t border-muted/20 pt-4 gap-2">
                <div className="flex gap-2">
                  {/* Bookmark Button */}
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => toggleSave(job.id)}
                    className={cn(
                      "h-9 w-9 shrink-0 cursor-pointer",
                      isSaved ? "text-indigo-400 border-indigo-400 bg-indigo-400/5" : "text-muted-foreground"
                    )}
                    title="Save Job"
                  >
                    <Bookmark className="h-4.5 w-4.5" />
                  </Button>

                  {/* Prepare Button */}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedJobForPrep(job);
                      setIsPrepModalOpen(true);
                    }}
                    className="text-xs font-semibold hover:border-violet-500/40 hover:bg-violet-500/5 cursor-pointer flex gap-1 items-center"
                  >
                    <Zap className="h-3.5 w-3.5 text-violet-400" /> Prep Interview
                  </Button>
                </div>

                {/* Apply Button */}
                <Button
                  size="sm"
                  onClick={() => handleApply(job.id)}
                  disabled={hasApplied}
                  className={cn(
                    "text-xs font-semibold cursor-pointer",
                    hasApplied && "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 pointer-events-none hover:bg-emerald-500/10"
                  )}
                >
                  {hasApplied ? <span className="flex items-center gap-1"><CheckCircle className="h-3.5 w-3.5" /> Applied</span> : "Apply Now"}
                </Button>
              </CardFooter>
            </Card>
          );
        })}
      </div>

      {/* Interactive Prep Modal Popup */}
      <Dialog open={isPrepModalOpen} onOpenChange={setIsPrepModalOpen}>
        {selectedJobForPrep && (
          <DialogContent className="max-w-md bg-card border-slate-900">
            <DialogHeader>
              <div className="mx-auto p-3 bg-violet-500/10 text-violet-400 rounded-full w-fit mb-3 animate-pulse">
                <Zap className="h-6 w-6" />
              </div>
              <DialogTitle className="text-center font-bold text-slate-100">AI Screen Prep Simulator</DialogTitle>
              <DialogDescription className="text-center text-xs">
                Unlock matching interview questions and tests for **{selectedJobForPrep.role}** at **{selectedJobForPrep.company}**.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 my-4 text-left leading-relaxed text-xs">
              <div className="space-y-2 border-b border-border pb-3">
                <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">Required skills matched</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {selectedJobForPrep.skillsMatched.map((s) => (
                    <span key={s} className="text-[9px] px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 font-semibold">
                      ✓ {s}
                    </span>
                  ))}
                </div>
              </div>

              {selectedJobForPrep.missingSkills.length > 0 ? (
                <div className="space-y-2">
                  <span className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider">Simulated Prep Targets (Missing)</span>
                  <p className="text-muted-foreground text-[10px]">We will auto-synthesize study documents and mock sessions for:</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedJobForPrep.missingSkills.map((s) => (
                      <span key={s} className="text-[9px] px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 font-semibold">
                        + {s}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Progress bar if prepping */}
              {isPrepping && (
                <div className="space-y-2 border-t border-border pt-3">
                  <div className="flex justify-between text-[10px]">
                    <span className="text-slate-200">Injecting syllabus nodes...</span>
                    <span className="font-mono">{prepProgress}%</span>
                  </div>
                  <Progress value={prepProgress} indicatorClassName="bg-violet-500" />
                </div>
              )}
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsPrepModalOpen(false)} disabled={isPrepping} className="cursor-pointer">
                Cancel
              </Button>
              <Button onClick={runMockPrep} isLoading={isPrepping} className="cursor-pointer">
                Launch Prep Engine
              </Button>
            </DialogFooter>
          </DialogContent>
        )}
      </Dialog>
    </div>
  );
}

function SavedJobsPanel() {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {mockJobs.slice(0, 2).map((job) => (
        <Card key={job.id} hoverEffect>
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-semibold">{job.role}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{job.company} - {job.location}</p>
              </div>
              <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[10px] font-bold text-primary">
                {job.matchScore}% match
              </span>
            </div>
            <Progress value={job.matchScore} className="mt-4" />
            <div className="mt-4 flex flex-wrap gap-2 text-[10px] font-semibold text-muted-foreground">
              {[job.type, job.experience, job.salary].map((item) => (
                <span key={item} className="rounded-md bg-muted px-2 py-1">{item}</span>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function CompanyDetailsPanel() {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {["Stripe", "Vercel", "Linear"].map((company, index) => (
        <Card key={company} hoverEffect>
          <CardContent className="p-5">
            <Building2 className="h-5 w-5 text-primary" />
            <h3 className="mt-4 font-semibold">{company}</h3>
            <p className="mt-2 text-xs leading-5 text-muted-foreground">
              Hiring signal, role difficulty, compensation bands, culture notes, benefits, ratings, and preparation focus.
            </p>
            <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg bg-muted/40 p-3">
                <p className="text-[10px] uppercase text-muted-foreground">Rating</p>
                <p className="font-bold">{(4.8 - index * 0.1).toFixed(1)}/5</p>
              </div>
              <div className="rounded-lg bg-muted/40 p-3">
                <p className="text-[10px] uppercase text-muted-foreground">Open Roles</p>
                <p className="font-bold">{12 - index * 3}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function JobDetailsPanel() {
  const job = mockJobs[0];

  return (
    <Card>
      <CardContent className="grid gap-6 p-6 lg:grid-cols-[1fr_320px]">
        <div>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold">{job.role}</h2>
              <p className="mt-1 text-sm text-muted-foreground">{job.company} - {job.location}</p>
            </div>
            <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-400">
              {job.matchScore}% match
            </span>
          </div>
          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {[job.salary, job.experience, job.type].map((item) => (
              <div key={item} className="rounded-lg border border-border bg-muted/30 p-4 text-xs font-semibold">
                {item}
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-xl border border-border bg-muted/20 p-5">
            <h3 className="flex items-center gap-2 text-sm font-semibold">
              <FileText className="h-4 w-4 text-primary" />
              Preparation Brief
            </h3>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Focus on Next.js architecture, system design tradeoffs, and concise project storytelling before applying.
            </p>
          </div>
        </div>
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-5">
          <Sparkles className="h-5 w-5 text-primary" />
          <h3 className="mt-4 text-sm font-semibold">AI Prep Targets</h3>
          <div className="mt-4 space-y-2">
            {job.missingSkills.map((skill) => (
              <div key={skill} className="rounded-lg bg-background/70 p-3 text-xs font-medium">
                {skill}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
