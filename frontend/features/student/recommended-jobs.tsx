"use client";

import React from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Building2, Calendar, ChevronLeft, ChevronRight, ExternalLink, Globe, Info, Search, Sparkles } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorBanner } from "@/components/ui/feedback";
import { api, RecommendedJobItem, RecommendedJobsParams } from "@/lib/api";

export const ROLE_PRESETS = [
  "Python Developer",
  "Frontend Developer",
  "Backend Developer",
  "Full Stack Developer",
  "Software Engineer",
  "Data Analyst",
  "AI/ML Engineer",
  "DevOps Engineer",
] as const;

// Values accepted by the backend (and verified against the upstream API).
const SENIORITY_OPTIONS = [
  { value: "", label: "Any level" },
  { value: "entry-level", label: "Entry level" },
  { value: "mid-level", label: "Mid level" },
  { value: "senior", label: "Senior" },
];

type Eligibility = "IN" | "WORLDWIDE" | "ANY";

interface Filters {
  q: string;
  role: string;
  seniority: string;
  eligibility: Eligibility;
  excludeWorldwide: boolean;
  page: number;
}

const DEFAULT_FILTERS: Filters = {
  q: "software developer",
  role: "",
  seniority: "",
  eligibility: "IN",
  excludeWorldwide: false,
  page: 1,
};

export function toApiParams(f: Filters): RecommendedJobsParams {
  return {
    q: f.q.trim() || undefined,
    country: f.eligibility === "IN" ? "IN" : undefined,
    worldwide: f.eligibility === "WORLDWIDE" ? true : undefined,
    exclude_worldwide: f.eligibility === "IN" && f.excludeWorldwide ? true : undefined,
    seniority: f.seniority || undefined,
    page: f.page,
  };
}

/** Apply links must be https URLs on himalayas.app; anything else is not rendered as a link. */
export function safeApplyUrl(url: string): string | null {
  try {
    const u = new URL(url);
    const ok = u.protocol === "https:" && (u.hostname === "himalayas.app" || u.hostname.endsWith(".himalayas.app"));
    return ok ? u.toString() : null;
  } catch {
    return null;
  }
}

export function formatSalary(job: RecommendedJobItem): string | null {
  const { salary_min: min, salary_max: max } = job;
  if (min == null && max == null) return null;
  const cur = job.salary_currency ? ` ${job.salary_currency}` : "";
  const period = job.salary_period ? ` / ${job.salary_period}` : "";
  const fmt = (n: number) => n.toLocaleString("en-US");
  if (min != null && max != null) return `${fmt(min)} – ${fmt(max)}${cur}${period}`;
  return min != null ? `From ${fmt(min)}${cur}${period}` : `Up to ${fmt(max as number)}${cur}${period}`;
}

function CompanyLogo({ name, src }: { name: string; src: string | null }) {
  const [failed, setFailed] = React.useState(false);
  if (src && !failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={src}
        alt=""
        referrerPolicy="no-referrer"
        loading="lazy"
        onError={() => setFailed(true)}
        className="h-10 w-10 shrink-0 rounded-lg border bg-background object-cover"
      />
    );
  }
  return (
    <div
      aria-hidden="true"
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border bg-muted/40 text-xs font-bold text-muted-foreground"
    >
      {name.slice(0, 2).toUpperCase()}
    </div>
  );
}

function JobCard({ job }: { job: RecommendedJobItem }) {
  const [open, setOpen] = React.useState(false);
  const applyUrl = safeApplyUrl(job.apply_url);
  const salary = formatSalary(job);
  const descId = `job-desc-${job.id.replace(/[^a-zA-Z0-9]/g, "-").slice(-60)}`;

  return (
    <Card className="transition-colors hover:border-primary/40">
      <CardContent className="space-y-3 pt-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex min-w-0 items-start gap-3">
            <CompanyLogo name={job.company} src={job.company_logo} />
            <div className="min-w-0 space-y-1">
              <h3 className="text-sm font-bold leading-snug">{job.title}</h3>
              <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                <span className="flex items-center gap-1 font-medium text-foreground">
                  <Building2 className="h-3.5 w-3.5" aria-hidden="true" />
                  {job.company}
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                  <Globe className="h-3 w-3" aria-hidden="true" />
                  {job.remote ? "Remote" : job.location}
                </span>
                {job.posted_at && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" aria-hidden="true" />
                    <span className="sr-only">Posted </span>
                    {new Date(job.posted_at).toLocaleDateString()}
                  </span>
                )}
              </p>
              <p className="text-[11px] text-muted-foreground">
                {job.eligible_countries.length > 0
                  ? `Open to candidates in: ${job.eligible_countries.slice(0, 4).join(", ")}${
                      job.eligible_countries.length > 4 ? ` +${job.eligible_countries.length - 4} more` : ""
                    }`
                  : "No country restriction listed"}
              </p>
              <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                {job.employment_type && <Badge>{job.employment_type}</Badge>}
                {job.seniority.map((s) => (
                  <Badge key={s}>{s}</Badge>
                ))}
                {salary && (
                  <span className="rounded border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-600 dark:text-amber-400">
                    {salary}
                  </span>
                )}
              </div>
            </div>
          </div>
          {applyUrl ? (
            <a
              href={applyUrl}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`Apply now for ${job.title} at ${job.company} (opens Himalayas in a new tab)`}
              className="inline-flex h-8 shrink-0 items-center justify-center gap-1.5 self-start rounded-md bg-primary px-3 text-xs font-semibold text-primary-foreground shadow-xs transition hover:bg-primary/90 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
            >
              Apply Now <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
          ) : null}
        </div>

        {job.match && (
          <p
            className="flex items-start gap-1.5 rounded-md bg-primary/5 px-2.5 py-1.5 text-[11px] text-foreground"
            data-testid="job-match"
          >
            <Sparkles className="mt-0.5 h-3 w-3 shrink-0 text-primary" aria-hidden="true" />
            <span>
              {job.match.reason}{" "}
              <span className="text-muted-foreground">Skill match estimate: {job.match.score}%</span>
            </span>
          </p>
        )}

        {job.description && (
          <div>
            <p
              id={descId}
              className={`whitespace-pre-line text-xs leading-relaxed text-muted-foreground ${open ? "" : "line-clamp-3"}`}
            >
              {job.description}
            </p>
            <button
              type="button"
              aria-expanded={open}
              aria-controls={descId}
              onClick={() => setOpen((v) => !v)}
              className="mt-1 text-[11px] font-medium text-primary hover:underline focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
            >
              {open ? "Show less" : "Show more"}
            </button>
          </div>
        )}

        <p className="border-t pt-2 text-[11px] text-muted-foreground">
          Source:{" "}
          <a href="https://himalayas.app" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">
            {job.source}
          </a>
        </p>
      </CardContent>
    </Card>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return <span className="rounded border bg-muted/40 px-2 py-0.5 text-[10px] text-muted-foreground">{children}</span>;
}

function JobSkeletons() {
  return (
    <div className="space-y-3" role="status" aria-busy="true" aria-label="Loading job listings">
      {[0, 1, 2].map((i) => (
        <div key={i} className="animate-pulse space-y-3 rounded-xl border p-5" data-testid="job-skeleton">
          <div className="flex gap-3">
            <div className="h-10 w-10 rounded-lg bg-muted" />
            <div className="flex-1 space-y-2">
              <div className="h-3 w-2/3 rounded bg-muted" />
              <div className="h-3 w-1/3 rounded bg-muted" />
            </div>
          </div>
          <div className="h-3 w-full rounded bg-muted" />
          <div className="h-3 w-5/6 rounded bg-muted" />
        </div>
      ))}
    </div>
  );
}

const selectClass =
  "h-9 w-full rounded-md border border-input bg-background px-2 text-xs shadow-xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring";

export function RecommendedJobsBoard() {
  const [filters, setFilters] = React.useState<Filters>(DEFAULT_FILTERS);
  const [keyword, setKeyword] = React.useState(DEFAULT_FILTERS.q);
  const listTop = React.useRef<HTMLDivElement>(null);

  const params = toApiParams(filters);
  const { data, isLoading, error, refetch, isFetching, isPlaceholderData } = useQuery({
    queryKey: ["recommended-jobs", params],
    queryFn: () => api.recommendedJobs(params),
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const update = (patch: Partial<Filters>) => setFilters((f) => ({ ...f, page: 1, ...patch }));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    update({ q: keyword, role: "" });
  };

  const goToPage = (page: number) => {
    setFilters((f) => ({ ...f, page }));
    listTop.current?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  };

  const jobs = data?.jobs ?? [];
  const totalPages = data?.total_pages ?? 0;
  const busy = isFetching && isPlaceholderData;

  return (
    <section aria-labelledby="recommended-it-jobs-heading" className="space-y-4 text-left">
      <div>
        <h2 id="recommended-it-jobs-heading" className="text-lg font-bold">
          Recommended IT Jobs
        </h2>
        <p className="text-xs text-muted-foreground">
          Live remote listings from{" "}
          <a href="https://himalayas.app" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">
            Himalayas
          </a>
          . Applications open the original listing.
        </p>
      </div>

      <div className="flex items-start gap-2.5 rounded-xl border border-blue-500/20 bg-blue-500/10 p-3 text-xs">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-500" aria-hidden="true" />
        <p className="leading-relaxed text-muted-foreground">
          <span className="font-semibold text-foreground">Remote roles only.</span> “India” means employers accept
          candidates from India, not that the job is in Chennai, Coimbatore, Madurai or elsewhere in Tamil Nadu. This
          source has no city-level or on-site listings, and it does not cover every vacancy in India.
        </p>
      </div>

      <form onSubmit={submit} className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-12" role="search">
        <div className="sm:col-span-2 lg:col-span-5">
          <label htmlFor="rj-keyword" className="mb-1 block text-[11px] font-medium text-muted-foreground">
            Job title or keyword
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <Input
              id="rj-keyword"
              className="h-9 pl-9 text-xs"
              placeholder="e.g. python, react, data analyst"
              maxLength={100}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </div>
        </div>
        <div className="lg:col-span-3">
          <label htmlFor="rj-role" className="mb-1 block text-[11px] font-medium text-muted-foreground">
            Role
          </label>
          <select
            id="rj-role"
            className={selectClass}
            value={filters.role}
            onChange={(e) => {
              const role = e.target.value;
              if (role) setKeyword(role);
              update({ role, q: role || keyword });
            }}
          >
            <option value="">Choose a role…</option>
            {ROLE_PRESETS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
        <div className="lg:col-span-2">
          <label htmlFor="rj-level" className="mb-1 block text-[11px] font-medium text-muted-foreground">
            Experience level
          </label>
          <select id="rj-level" className={selectClass} value={filters.seniority} onChange={(e) => update({ seniority: e.target.value })}>
            {SENIORITY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div className="lg:col-span-2">
          <label htmlFor="rj-where" className="mb-1 block text-[11px] font-medium text-muted-foreground">
            Candidate location
          </label>
          <select
            id="rj-where"
            className={selectClass}
            value={filters.eligibility}
            onChange={(e) => update({ eligibility: e.target.value as Eligibility })}
          >
            <option value="IN">Open to India</option>
            <option value="WORLDWIDE">Worldwide remote</option>
            <option value="ANY">Any country</option>
          </select>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 sm:col-span-2 lg:col-span-12">
          <label
            className={`flex items-center gap-1.5 text-xs ${filters.eligibility === "IN" ? "" : "opacity-50"}`}
          >
            <input
              type="checkbox"
              className="h-3.5 w-3.5"
              disabled={filters.eligibility !== "IN"}
              checked={filters.excludeWorldwide}
              onChange={(e) => update({ excludeWorldwide: e.target.checked })}
            />
            Only roles that list India (hide worldwide)
          </label>
          <Button type="submit" size="sm" className="px-4">
            Search jobs
          </Button>
        </div>
      </form>

      <div ref={listTop} className="flex min-h-4 flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground" aria-live="polite">
        <span>
          {data && data.total > 0
            ? `${data.total.toLocaleString()} listing${data.total === 1 ? "" : "s"} · page ${data.page} of ${totalPages}`
            : ""}
        </span>
        {busy && <span className="text-primary">Updating…</span>}
      </div>

      {isLoading ? (
        <JobSkeletons />
      ) : error && !data ? (
        <ErrorBanner error={error} onRetry={() => void refetch()} />
      ) : jobs.length === 0 ? (
        <EmptyState
          title="No remote jobs match these filters"
          description="Try a broader keyword, another role, a different experience level, or “Any country”. Listings are never invented to fill the page."
        />
      ) : (
        <div className="space-y-3" aria-busy={busy}>
          {error ? <ErrorBanner error={error} onRetry={() => void refetch()} /> : null}
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
          {data?.match_method && <p className="text-[11px] text-muted-foreground">{data.match_method}</p>}
          {totalPages > 1 && (
            <nav aria-label="Job listing pages" className="flex items-center justify-between border-t pt-3 text-xs">
              <Button size="sm" variant="outline" disabled={filters.page <= 1 || isFetching} onClick={() => goToPage(filters.page - 1)} className="gap-1">
                <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" /> Previous
              </Button>
              <span className="text-muted-foreground">
                Page {filters.page} of {totalPages}
              </span>
              <Button size="sm" variant="outline" disabled={filters.page >= totalPages || isFetching} onClick={() => goToPage(filters.page + 1)} className="gap-1">
                Next <ChevronRight className="h-3.5 w-3.5" aria-hidden="true" />
              </Button>
            </nav>
          )}
        </div>
      )}

      <p className="pt-2 text-center text-[11px] text-muted-foreground">
        Job data provided by{" "}
        <a href="https://himalayas.app" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">
          Himalayas
        </a>
        .
      </p>
    </section>
  );
}
