import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi, type MockInstance } from "vitest";
import { RecommendedJobsBoard, safeApplyUrl } from "../recommended-jobs";
import { api, ApiError, RecommendedJobItem, RecommendedJobsResponse } from "@/lib/api";

const job = (over: Partial<RecommendedJobItem> = {}): RecommendedJobItem => ({
  id: "https://himalayas.app/companies/acme/jobs/python-dev",
  title: "Python Developer",
  company: "Acme",
  company_slug: "acme",
  company_logo: null,
  location: "Remote",
  remote: true,
  eligible_countries: ["India"],
  employment_type: "Full Time",
  seniority: ["Entry-level"],
  salary_min: 40000,
  salary_max: 60000,
  salary_currency: "USD",
  salary_period: "annual",
  description: "Build APIs with Python <script>alert(1)</script>",
  posted_at: "2026-10-01T00:00:00+00:00",
  expires_at: null,
  apply_url: "https://himalayas.app/companies/acme/jobs/python-dev?utm_source=api",
  source: "Himalayas",
  match: { score: 67, matched_skills: ["Python", "SQL"], reason: "Matches your Python and SQL skills." },
  ...over,
});

const response = (jobs: RecommendedJobItem[], over: Partial<RecommendedJobsResponse> = {}): RecommendedJobsResponse => ({
  success: true,
  source: "Himalayas",
  attribution: { name: "Himalayas", url: "https://himalayas.app" },
  filters: {
    query: "software developer",
    country: "IN",
    page: 1,
    seniority: null,
    employment_type: null,
    worldwide: null,
    exclude_worldwide: null,
  },
  total: jobs.length,
  page: 1,
  page_size: 20,
  total_pages: jobs.length ? 1 : 0,
  match_method: "Estimate: keyword overlap, not a hiring probability.",
  jobs,
  ...over,
});

function renderBoard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <RecommendedJobsBoard />
    </QueryClientProvider>
  );
}

describe("RecommendedJobsBoard", () => {
  let spy: MockInstance<typeof api.recommendedJobs>;
  beforeEach(() => {
    spy = vi.spyOn(api, "recommendedJobs");
  });
  afterEach(() => vi.restoreAllMocks());

  it("shows skeletons, then job cards with a safe Apply Now link and attribution", async () => {
    spy.mockResolvedValue(response([job()]));
    renderBoard();
    expect(screen.getAllByTestId("job-skeleton").length).toBeGreaterThan(0);

    expect(await screen.findByRole("heading", { name: "Python Developer" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Recommended IT Jobs" })).toBeInTheDocument();
    expect(screen.getByText("Acme")).toBeInTheDocument();
    expect(screen.getByText("Remote")).toBeInTheDocument();
    expect(screen.getByText("40,000 – 60,000 USD / annual")).toBeInTheDocument();
    expect(screen.getByTestId("job-match")).toHaveTextContent("Matches your Python and SQL skills.");
    expect(screen.getByTestId("job-match")).toHaveTextContent("Skill match estimate: 67%");

    const apply = screen.getByRole("link", { name: /Apply now for Python Developer/i });
    expect(apply).toHaveAttribute("href", "https://himalayas.app/companies/acme/jobs/python-dev?utm_source=api");
    expect(apply).toHaveAttribute("target", "_blank");
    expect(apply.getAttribute("rel")).toContain("noopener");
    expect(apply.getAttribute("rel")).toContain("noreferrer");

    // Upstream text is rendered as text, never as HTML.
    expect(document.querySelector("script")).toBeNull();
    expect(screen.getAllByRole("link", { name: "Himalayas" })[0]).toHaveAttribute("href", "https://himalayas.app");
    expect(screen.getByText(/not that the job is in Chennai/i)).toBeInTheDocument();
  });

  it("omits salary and match when the source does not provide them", async () => {
    spy.mockResolvedValue(
      response([
        job({ salary_min: null, salary_max: null, match: null, employment_type: null, seniority: [], posted_at: null }),
      ])
    );
    renderBoard();
    await screen.findByRole("heading", { name: "Python Developer" });
    expect(screen.queryByText(/USD/)).toBeNull();
    expect(screen.queryByTestId("job-match")).toBeNull();
  });

  it("does not render a link for an unsafe apply URL", async () => {
    spy.mockResolvedValue(response([job({ apply_url: "javascript:alert(1)" })]));
    renderBoard();
    await screen.findByRole("heading", { name: "Python Developer" });
    expect(screen.queryByRole("link", { name: /Apply now/i })).toBeNull();
    expect(safeApplyUrl("https://evil.com/x")).toBeNull();
    expect(safeApplyUrl("http://himalayas.app/x")).toBeNull();
    expect(safeApplyUrl("https://himalayas.app.evil.com/x")).toBeNull();
  });

  it("shows an empty state without inventing jobs", async () => {
    spy.mockResolvedValue(response([]));
    renderBoard();
    expect(await screen.findByText("No remote jobs match these filters")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Apply now/i })).toBeNull();
  });

  it("shows an error with a working retry", async () => {
    spy.mockRejectedValueOnce(new ApiError("The job source is rate limiting requests.", 429));
    spy.mockResolvedValue(response([job()]));
    renderBoard();
    expect(await screen.findByRole("alert")).toHaveTextContent("rate limiting");
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(await screen.findByRole("heading", { name: "Python Developer" })).toBeInTheDocument();
  });

  it("searches by keyword, filters by role/level/location, and paginates", async () => {
    spy.mockImplementation(async (p) => response([job()], { page: p?.page ?? 1, total: 45, total_pages: 3 }));
    renderBoard();
    await screen.findByRole("heading", { name: "Python Developer" });
    expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ q: "software developer", country: "IN", page: 1 }));

    const box = screen.getByLabelText("Job title or keyword");
    await userEvent.clear(box);
    await userEvent.type(box, "react");
    await userEvent.click(screen.getByRole("button", { name: "Search jobs" }));
    await waitFor(() => expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ q: "react", page: 1 })));

    await userEvent.selectOptions(screen.getByLabelText("Role"), "Data Analyst");
    await waitFor(() => expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ q: "Data Analyst" })));

    await userEvent.selectOptions(screen.getByLabelText("Experience level"), "entry-level");
    await waitFor(() =>
      expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ seniority: "entry-level", page: 1 }))
    );

    await userEvent.click(screen.getByRole("button", { name: /next/i }));
    await waitFor(() => expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 })));
    expect(await screen.findByText("Page 2 of 3")).toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Candidate location"), "WORLDWIDE");
    await waitFor(() =>
      expect(spy).toHaveBeenLastCalledWith(expect.objectContaining({ worldwide: true, country: undefined, page: 1 }))
    );
  });
});
