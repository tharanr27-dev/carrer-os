"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building, Users } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from "@/components/ui/feedback";
import { api, Job, JobApplication } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

const DOMAIN_RE = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/i;

const selectClass = "flex h-9 rounded-md border border-input bg-background px-2 text-xs";

function CompanySetup() {
  const refreshUser = useAuthStore((s) => s.refreshUser);
  const [form, setForm] = React.useState({ name: "", domain: "", description: "" });
  const [validation, setValidation] = React.useState<string | null>(null);

  const create = useMutation({
    mutationFn: () =>
      api.createCompany({ name: form.name.trim(), domain: form.domain.trim().toLowerCase(), description: form.description.trim() || undefined }),
    onSuccess: () => refreshUser(),
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return setValidation("Company name is required.");
    if (!DOMAIN_RE.test(form.domain.trim())) return setValidation("Enter a valid company domain, e.g. acme.com.");
    setValidation(null);
    create.mutate();
  };

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle className="text-base font-bold flex items-center gap-2">
          <Building className="h-4 w-4 text-primary" /> Set up your company
        </CardTitle>
        <CardDescription className="text-xs">Create your company profile to start posting jobs and reviewing applicants.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-3">
          <ErrorBanner error={validation ?? create.error} />
          <Input placeholder="Company name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="Domain (acme.com)" value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} />
          <Input placeholder="Description (optional)" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <Button type="submit" className="w-full" isLoading={create.isPending}>
            Create company
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function PostJob({ onPosted }: { onPosted: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = React.useState({ title: "", description: "", location: "", requirements: "", benefits: "" });
  const [validation, setValidation] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);

  const lines = (v: string) =>
    v
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

  const create = useMutation({
    mutationFn: () =>
      api.createJob({
        title: form.title.trim(),
        description: form.description.trim(),
        location: form.location.trim() || undefined,
        requirements: lines(form.requirements),
        benefits: lines(form.benefits),
      }),
    onSuccess: async (job) => {
      setNotice(`"${job.title}" is now live on the job board.`);
      setForm({ title: "", description: "", location: "", requirements: "", benefits: "" });
      await queryClient.invalidateQueries({ queryKey: ["company-jobs"] });
      onPosted();
    },
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setNotice(null);
    if (!form.title.trim() || !form.description.trim()) return setValidation("Title and description are required.");
    setValidation(null);
    create.mutate();
  };

  const area = "w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring";
  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle className="text-base font-bold">Post a job</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-3">
          <SuccessBanner message={notice} />
          <ErrorBanner error={validation ?? create.error} />
          <Input placeholder="Job title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <textarea rows={5} className={area} placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <Input placeholder="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
          <textarea rows={3} className={area} placeholder="Requirements (one per line)" value={form.requirements} onChange={(e) => setForm({ ...form, requirements: e.target.value })} />
          <textarea rows={3} className={area} placeholder="Benefits (one per line)" value={form.benefits} onChange={(e) => setForm({ ...form, benefits: e.target.value })} />
          <Button type="submit" isLoading={create.isPending}>
            Publish job
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function JobsList({ jobs, onSelect }: { jobs: Job[]; onSelect: (id: string) => void }) {
  return (
    <div className="space-y-3">
      {jobs.map((j) => (
        <Card key={j.id}>
          <CardContent className="pt-6 flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">{j.title}</p>
              <p className="text-xs text-muted-foreground">
                {j.location ?? "Location not set"} • {j.status} • posted {new Date(j.created_at).toLocaleDateString()}
              </p>
            </div>
            <Button size="sm" variant="outline" onClick={() => onSelect(j.id)} className="gap-1">
              <Users className="h-3.5 w-3.5" /> Applicants
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function Applicants({ jobs, jobId, setJobId }: { jobs: Job[]; jobId: string | null; setJobId: (id: string) => void }) {
  const queryClient = useQueryClient();
  const job = jobs.find((j) => j.id === jobId);
  const stages = job?.pipeline_stages?.length ? job.pipeline_stages : ["Applied", "Screening", "Interview", "Offer", "Hired", "Rejected"];

  const applications = useQuery({
    queryKey: ["job-applications", jobId],
    queryFn: () => api.jobApplications(jobId as string),
    enabled: Boolean(jobId),
  });

  const update = useMutation({
    mutationFn: (v: { id: string; status: string }) => api.updateApplicationStatus(v.id, v.status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job-applications", jobId] }),
  });

  return (
    <div className="space-y-4">
      <select className={`${selectClass} w-full max-w-md`} value={jobId ?? ""} onChange={(e) => setJobId(e.target.value)} aria-label="Select job">
        <option value="" disabled>
          Select a job…
        </option>
        {jobs.map((j) => (
          <option key={j.id} value={j.id}>
            {j.title}
          </option>
        ))}
      </select>
      <ErrorBanner error={update.error} />
      {!jobId ? (
        <EmptyState title="Choose a job" description="Pick a job to review its applicants." />
      ) : applications.isLoading ? (
        <LoadingBlock label="Loading applicants…" />
      ) : applications.error ? (
        <ErrorBanner error={applications.error} onRetry={() => void applications.refetch()} />
      ) : !applications.data?.length ? (
        <EmptyState title="No applicants yet" description="Applications will appear here as candidates apply." />
      ) : (
        applications.data.map((a: JobApplication) => (
          <Card key={a.id}>
            <CardContent className="pt-6 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">Candidate {a.candidate_id.slice(0, 8)}</p>
                <p className="text-xs text-muted-foreground">
                  Applied {new Date(a.created_at).toLocaleDateString()}
                  {a.fit_score ? ` • fit ${a.fit_score}` : ""}
                </p>
              </div>
              <select
                className={selectClass}
                value={a.status}
                disabled={update.isPending}
                aria-label="Pipeline stage"
                onChange={(e) => update.mutate({ id: a.id, status: e.target.value })}
              >
                {[...new Set([a.status, ...stages])].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}

const SECTION_TAB: Record<string, string> = {
  "post-job": "post",
  "manage-jobs": "jobs",
  "candidate-search": "applicants",
  "shortlisted-candidates": "applicants",
  "candidate-details": "applicants",
};

export function RecruiterPortal({ section }: { section?: string }) {
  const user = useAuthStore((s) => s.user);
  const [tab, setTab] = React.useState(SECTION_TAB[section ?? ""] ?? "jobs");
  const [jobId, setJobId] = React.useState<string | null>(null);

  const hasCompany = Boolean(user?.companyId);
  const jobs = useQuery({ queryKey: ["company-jobs"], queryFn: api.companyJobs, enabled: hasCompany });

  return (
    <div className="space-y-6 text-left">
      <div>
        <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">Recruiter Workspace</span>
        <h1 className="text-3xl font-extrabold tracking-tight">Hiring Hub</h1>
        <p className="text-sm text-muted-foreground">Post openings and move candidates through your pipeline.</p>
      </div>

      {!hasCompany ? (
        <CompanySetup />
      ) : (
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="mb-4 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30">
            <TabsTrigger value="jobs" className="text-xs">Manage Jobs</TabsTrigger>
            <TabsTrigger value="post" className="text-xs">Post Job</TabsTrigger>
            <TabsTrigger value="applicants" className="text-xs">Applicants</TabsTrigger>
          </TabsList>
          <TabsContent value="jobs">
            {jobs.isLoading ? (
              <LoadingBlock />
            ) : jobs.error ? (
              <ErrorBanner error={jobs.error} onRetry={() => void jobs.refetch()} />
            ) : !jobs.data?.length ? (
              <EmptyState title="No jobs posted yet" description="Post your first opening to start receiving applications." />
            ) : (
              <JobsList
                jobs={jobs.data}
                onSelect={(id) => {
                  setJobId(id);
                  setTab("applicants");
                }}
              />
            )}
          </TabsContent>
          <TabsContent value="post">
            <PostJob onPosted={() => setTab("jobs")} />
          </TabsContent>
          <TabsContent value="applicants">
            <Applicants jobs={jobs.data ?? []} jobId={jobId} setJobId={setJobId} />
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
