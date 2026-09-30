"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, Building2, MapPin, Search } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from "@/components/ui/feedback";
import { api, OpenJob } from "@/lib/api";
import { useNotificationStore } from "@/store/useNotificationStore";

export function JobBoard() {
  const queryClient = useQueryClient();
  const addNotification = useNotificationStore((s) => s.addNotification);
  const [query, setQuery] = React.useState("");
  const [expanded, setExpanded] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);

  const jobs = useQuery({ queryKey: ["open-jobs"], queryFn: api.openJobs });
  const applications = useQuery({ queryKey: ["my-applications"], queryFn: api.myApplications });
  const appliedIds = new Set(applications.data?.map((a) => a.job_id));

  const apply = useMutation({
    mutationFn: (job: OpenJob) => api.applyToJob(job.id),
    onSuccess: async (_app, job) => {
      setNotice(`Applied to ${job.title}.`);
      addNotification("jobs", "Application submitted", `${job.title}${job.company_name ? ` at ${job.company_name}` : ""}`, "/jobs?tab=tracker");
      await queryClient.invalidateQueries({ queryKey: ["my-applications"] });
    },
  });

  const q = query.trim().toLowerCase();
  const visible = (jobs.data ?? []).filter(
    (j) => !q || j.title.toLowerCase().includes(q) || (j.company_name ?? "").toLowerCase().includes(q) || (j.location ?? "").toLowerCase().includes(q)
  );

  return (
    <div className="space-y-4 text-left">
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input className="pl-9" placeholder="Search by title, company, or location…" value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>
      <SuccessBanner message={notice} />
      <ErrorBanner error={apply.error} />
      {jobs.isLoading ? (
        <LoadingBlock label="Loading jobs…" />
      ) : jobs.error ? (
        <ErrorBanner error={jobs.error} onRetry={() => void jobs.refetch()} />
      ) : visible.length === 0 ? (
        <EmptyState
          title={q ? "No jobs match your search" : "No open jobs yet"}
          description={q ? "Try a different keyword." : "Recruiters have not posted any openings."}
        />
      ) : (
        visible.map((job) => {
          const applied = appliedIds.has(job.id);
          const open = expanded === job.id;
          return (
            <Card key={job.id}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <CardTitle className="text-sm font-bold flex items-center gap-2">
                      <Briefcase className="h-4 w-4 text-primary" /> {job.title}
                    </CardTitle>
                    <CardDescription className="text-xs flex items-center gap-3">
                      <span className="flex items-center gap-1">
                        <Building2 className="h-3 w-3" /> {job.company_name ?? "Company"}
                      </span>
                      {job.location && (
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" /> {job.location}
                        </span>
                      )}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <Button size="sm" variant="ghost" onClick={() => setExpanded(open ? null : job.id)}>
                      {open ? "Hide" : "Details"}
                    </Button>
                    <Button
                      size="sm"
                      disabled={applied || (apply.isPending && apply.variables?.id === job.id)}
                      isLoading={apply.isPending && apply.variables?.id === job.id}
                      onClick={() => apply.mutate(job)}
                    >
                      {applied ? "Applied" : "Apply"}
                    </Button>
                  </div>
                </div>
              </CardHeader>
              {open && (
                <CardContent className="space-y-3 text-xs">
                  <p className="whitespace-pre-wrap text-muted-foreground">{job.description}</p>
                  {job.requirements?.length ? (
                    <div>
                      <p className="font-semibold mb-1">Requirements</p>
                      <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground">
                        {job.requirements.map((r) => (
                          <li key={r}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {job.benefits?.length ? (
                    <div>
                      <p className="font-semibold mb-1">Benefits</p>
                      <ul className="list-disc pl-4 space-y-0.5 text-muted-foreground">
                        {job.benefits.map((b) => (
                          <li key={b}>{b}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </CardContent>
              )}
            </Card>
          );
        })
      )}
    </div>
  );
}

const STATUS_TONE: Record<string, string> = {
  Applied: "bg-sky-500/10 text-sky-500",
  Screening: "bg-amber-500/10 text-amber-500",
  Interview: "bg-violet-500/10 text-violet-500",
  Offer: "bg-emerald-500/10 text-emerald-500",
  Hired: "bg-emerald-500/20 text-emerald-500",
  Rejected: "bg-rose-500/10 text-rose-500",
};

export function ApplicationTracker() {
  const applications = useQuery({ queryKey: ["my-applications"], queryFn: api.myApplications });

  if (applications.isLoading) return <LoadingBlock label="Loading your applications…" />;
  if (applications.error) return <ErrorBanner error={applications.error} onRetry={() => void applications.refetch()} />;
  if (!applications.data?.length) {
    return <EmptyState title="No applications yet" description="Apply to a job from the Job Board and it will show up here." />;
  }

  return (
    <div className="space-y-3 text-left">
      {applications.data.map((a) => (
        <Card key={a.id}>
          <CardContent className="flex items-center justify-between gap-3 pt-6">
            <div>
              <p className="text-sm font-semibold">{a.job_title ?? "Job"}</p>
              <p className="text-xs text-muted-foreground">
                {a.company_name ?? "Company"} • applied {new Date(a.created_at).toLocaleDateString()}
                {a.fit_score ? ` • fit ${a.fit_score}` : ""}
              </p>
            </div>
            <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${STATUS_TONE[a.status] ?? "bg-muted text-foreground"}`}>{a.status}</span>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function PlacementDrives() {
  const queryClient = useQueryClient();
  const drives = useQuery({ queryKey: ["available-drives"], queryFn: api.availableDrives });
  const registrations = useQuery({ queryKey: ["my-registrations"], queryFn: api.myRegistrations });
  const registered = new Map(registrations.data?.map((r) => [r.drive_id, r]));

  const register = useMutation({
    mutationFn: (driveId: string) => api.registerForDrive(driveId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["my-registrations"] }),
  });

  if (drives.isLoading) return <LoadingBlock label="Loading placement drives…" />;
  if (drives.error) return <ErrorBanner error={drives.error} onRetry={() => void drives.refetch()} />;

  return (
    <div className="space-y-3 text-left">
      <ErrorBanner error={register.error ?? registrations.error} />
      {!drives.data?.length ? (
        <EmptyState title="No placement drives open" description="Your placement office has not announced any drives yet." />
      ) : (
        drives.data.map((d) => {
          const reg = registered.get(d.id);
          const busy = register.isPending && register.variables === d.id;
          return (
            <Card key={d.id}>
              <CardContent className="flex items-center justify-between gap-3 pt-6">
                <div>
                  <p className="text-sm font-semibold">{d.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {d.drive_type} • {d.status}
                    {d.date_of_drive ? ` • ${new Date(d.date_of_drive).toLocaleDateString()}` : ""}
                  </p>
                  {d.description && <p className="text-xs text-muted-foreground mt-1">{d.description}</p>}
                </div>
                {reg ? (
                  <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-500">{reg.status}</span>
                ) : (
                  <Button size="sm" isLoading={busy} disabled={register.isPending} onClick={() => register.mutate(d.id)}>
                    Register
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })
      )}
    </div>
  );
}
