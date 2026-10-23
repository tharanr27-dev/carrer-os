import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ResumeCenterView } from "../resume-center";
import { api, ApiError, ResumeAnalysis } from "@/lib/api";

const RESUMES = [{ id: "r1", file_name: "cv.pdf", status: "COMPLETED", created_at: "2026-10-01T00:00:00Z" }];

const analysis = (keyword_analysis: Record<string, unknown>): ResumeAnalysis => ({
  id: "a1", ats_score: 88.1, grammar_score: 90, quality_score: 84.3, keyword_analysis,
  suggestions: [{ category: "Wording", suggestion_text: "Replace 'responsible for' with a stronger verb.", impact: "MEDIUM" }],
});

function renderView() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ResumeCenterView />
    </QueryClientProvider>
  );
}

describe("Resume Center honesty and download", () => {
  beforeEach(() => {
    vi.spyOn(api, "listResumes").mockResolvedValue(RESUMES as never);
  });
  afterEach(() => vi.restoreAllMocks());

  it("labels a real analysis as rule-based measurements, not AI", async () => {
    vi.spyOn(api, "resumeAnalysis").mockResolvedValue(
      analysis({ method: "rule_based_v1", warnings: ["Only the first 15 pages were analysed."] })
    );
    renderView();
    const note = await screen.findByTestId("analysis-note");
    expect(note).toHaveTextContent(/Rule-based measurements/);
    expect(note).toHaveTextContent(/not AI judgements/);
    expect(note).toHaveTextContent("Only the first 15 pages were analysed.");
    expect(screen.queryByTestId("analysis-legacy")).toBeNull();
    expect(screen.getByText("ATS readiness")).toBeInTheDocument();
    expect(screen.getByText("Writing mechanics")).toBeInTheDocument();
  });

  it("warns that an older analysis was simulated and is not based on the file", async () => {
    vi.spyOn(api, "resumeAnalysis").mockResolvedValue(analysis({ found: ["Python"], missing: ["Docker"] }));
    renderView();
    const warn = await screen.findByTestId("analysis-legacy");
    expect(warn).toHaveTextContent(/earlier simulated version/);
    expect(warn).toHaveTextContent(/NOT based on your file/);
    expect(screen.queryByTestId("analysis-note")).toBeNull();
  });

  it("downloads the stored file through the authenticated API (not a bare link)", async () => {
    vi.spyOn(api, "resumeAnalysis").mockResolvedValue(analysis({ method: "rule_based_v1" }));
    const dl = vi.spyOn(api, "resumeDownload").mockResolvedValue({ blob: new Blob(["%PDF-1.4"], { type: "application/pdf" }), filename: "cv.pdf" });
    const createUrl = vi.fn(() => "blob:fake");
    const revoke = vi.fn();
    Object.assign(URL, { createObjectURL: createUrl, revokeObjectURL: revoke });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: "Download cv.pdf" }));
    await waitFor(() => expect(dl).toHaveBeenCalledWith("r1"));
    expect(createUrl).toHaveBeenCalled();
    expect(click).toHaveBeenCalled();
  });

  it("shows a clear message when the original file is not available", async () => {
    vi.spyOn(api, "resumeAnalysis").mockResolvedValue(analysis({ method: "rule_based_v1" }));
    vi.spyOn(api, "resumeDownload").mockRejectedValue(
      new ApiError("The original file is not available (it was uploaded before file storage was enabled).", 404)
    );
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: "Download cv.pdf" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/not available/);
  });
});
