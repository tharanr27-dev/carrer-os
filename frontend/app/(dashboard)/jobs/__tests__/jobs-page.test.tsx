import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import JobsPage from "../page";
import { api } from "@/lib/api";

let tab = "recommended";
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams({ tab }),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/jobs",
}));

const renderPage = () =>
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <JobsPage />
    </QueryClientProvider>
  );

describe("Jobs page (regression guard)", () => {
  afterEach(() => vi.restoreAllMocks());

  it("keeps all five tabs, including Recommended IT Jobs next to the existing Job Board", async () => {
    vi.spyOn(api, "recommendedJobs").mockResolvedValue({
      success: true, source: "Himalayas", attribution: { name: "Himalayas", url: "https://himalayas.app" },
      filters: { query: null, country: null, page: 1, seniority: null, employment_type: null, worldwide: null, exclude_worldwide: null },
      total: 0, page: 1, page_size: 20, total_pages: 0, match_method: null, jobs: [],
    });
    renderPage();
    for (const name of ["Job Board", "Recommended IT Jobs", "Application Tracker", "Placement Drives", "Interview Preparation"]) {
      expect(await screen.findByRole("button", { name })).toBeInTheDocument();
    }
    expect(await screen.findByRole("heading", { name: "Recommended IT Jobs" })).toBeInTheDocument();
    expect(await screen.findByText("No remote jobs match these filters")).toBeInTheDocument();
  });

  it("still defaults the legacy ?tab=portal alias to the Job Board", async () => {
    tab = "portal";
    vi.spyOn(api, "openJobs").mockResolvedValue([]);
    vi.spyOn(api, "myApplications").mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText("No open jobs yet")).toBeInTheDocument();
    tab = "recommended";
  });
});
