import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { InterviewPreparationView } from "../interview-prep";
import { api, ApiError, TrainingAttempt, TrainingItem, TrainingMeta, TrainingProgress } from "@/lib/api";

const META: TrainingMeta = {
  rounds: (["aptitude", "technical", "coding", "communication", "hr", "resume", "managerial"] as const).map((key, i) => ({
    key,
    label: key[0].toUpperCase() + key.slice(1),
    stage: i + 1,
    groups: [{ name: "Group", topics: [{ slug: `${key}-topic`, label: `${key} topic`, questions: 4 }] }],
  })),
  target_roles: ["Python Developer"],
  levels: ["fresher"],
  difficulties: ["easy", "medium", "hard"],
  ai_available: false,
  ai_note: "AI generation is off (no AI provider is configured).",
  labels: [],
  disclaimer: "No question is guaranteed to appear in any real interview.",
};

const emptyRound = (label: string, stage: number) => ({
  label, stage, attempted: 0, objective_pct: null, estimated_pct: null, self_assessed_pct: null,
  combined_pct: null, avg_time_sec: null, status: "not_started" as const, last_practised: null,
});

const PROGRESS = (over: Partial<TrainingProgress> = {}): TrainingProgress => ({
  overall_pct: null,
  total_scored_answers: 0,
  rounds: {
    aptitude: emptyRound("Aptitude", 1), technical: emptyRound("Technical", 2), coding: emptyRound("Coding", 3),
    communication: emptyRound("Communication", 4), hr: emptyRound("HR", 5), resume: emptyRound("Resume", 6),
    managerial: emptyRound("Managerial", 7),
  },
  current_stage: { round: "aptitude", label: "Aptitude", status: "not_started" },
  weakest_topics: [], strongest_topics: [], completion_rate: null, attempts_total: 0, attempts_completed: 0,
  trend: [], improvement_pct_points: null, recent_attempts: [],
  recommendations: [{
    rule: "no_activity", title: "Start with an aptitude warm-up", reason: "You have no saved practice yet.",
    action: { type: "practice", round: "aptitude", topic: null, difficulty: "easy", mode: "practice" },
  }],
  scoring_rules: ["Aptitude scores are objective."],
  resume_attempt: null,
  profile: { target_role: null, level: "fresher", language: "en", resume_data: { projects: [], skills: [], degree: null, source: "profile" } },
  ...over,
});

const mcqItem = (over: Partial<TrainingItem> = {}): TrainingItem => ({
  id: "i1", position: 1, round: "aptitude", topic: "percentages", topic_label: "Percentages", difficulty: "easy",
  qtype: "mcq", prompt: "What is 15% of 240?", options: ["32", "36", "38", "40"], label: "foundational",
  source: "curated", review_status: "reviewed", is_follow_up: false, coding: null, answered: false, answer: null,
  time_taken_sec: null, result: null, ...over,
});

const ATTEMPT = (over: Partial<TrainingAttempt> = {}): TrainingAttempt => ({
  id: "a1", mode: "practice", round: "aptitude", topic: "percentages", difficulty: null, status: "IN_PROGRESS",
  config: { notices: [] }, time_limit_sec: null, started_at: "2026-10-22T00:00:00Z", deadline: null, ended_at: null,
  summary: null, items: [mcqItem(), mcqItem({ id: "i2", position: 2, prompt: "A price rises 20% then falls 20%. Net change?", options: ["None", "4% down", "4% up", "2% down"] })],
  ai_available: false, ...over,
});

function renderView(tab = "roadmap") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onTab = vi.fn();
  const utils = render(
    <QueryClientProvider client={client}>
      <InterviewPreparationView tab={tab} onTabChange={onTab} />
    </QueryClientProvider>
  );
  return { ...utils, onTab };
}

describe("Interview Preparation", () => {
  beforeEach(() => {
    vi.spyOn(api, "trainingMeta").mockResolvedValue(META);
    vi.spyOn(api, "trainingProgress").mockResolvedValue(PROGRESS());
  });
  afterEach(() => vi.restoreAllMocks());

  it("shows loading skeletons, then an honest empty state with no invented scores", async () => {
    renderView();
    expect(screen.getAllByTestId("prep-skeleton").length).toBeGreaterThan(0);
    expect(await screen.findByText(/No practice saved yet/i)).toBeInTheDocument();
    expect(screen.getByLabelText("Overall preparation score")).toHaveTextContent("—");
    expect(screen.getByText("Start with an aptitude warm-up")).toBeInTheDocument();
    expect(screen.getAllByText("Not started").length).toBe(7);
    expect(screen.getByRole("heading", { name: "My Training Roadmap" })).toBeInTheDocument();
    expect(screen.getByText(/AI generation is off/)).toBeInTheDocument();
  });

  it("renders real saved progress", async () => {
    vi.spyOn(api, "trainingProgress").mockResolvedValue(PROGRESS({
      overall_pct: 72.5, total_scored_answers: 14, attempts_total: 2, attempts_completed: 1,
      rounds: { ...PROGRESS().rounds, aptitude: { ...emptyRound("Aptitude", 1), attempted: 14, objective_pct: 72.5, combined_pct: 72.5, status: "on_track" } },
      weakest_topics: [{ round: "aptitude", topic: "interest", label: "Simple and Compound Interest", attempted: 4, score_pct: 25 }],
    }));
    renderView();
    expect(await screen.findByLabelText("Overall preparation score")).toHaveTextContent("73%");
    expect(screen.getByText("Simple and Compound Interest")).toBeInTheDocument();
    expect(screen.getByText("On track")).toBeInTheDocument();
  });

  it("shows an error with a working retry", async () => {
    const spy = vi.spyOn(api, "trainingProgress");
    spy.mockRejectedValueOnce(new ApiError("Server unavailable", 500));
    spy.mockResolvedValue(PROGRESS());
    renderView();
    expect(await screen.findByRole("alert")).toHaveTextContent("Server unavailable");
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(await screen.findByText(/No practice saved yet/i)).toBeInTheDocument();
  });

  it("starts a recommended session from the roadmap", async () => {
    const start = vi.spyOn(api, "trainingStart").mockResolvedValue(ATTEMPT());
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /^Start/ }));
    await waitFor(() => expect(start).toHaveBeenCalledWith(expect.objectContaining({ mode: "practice", round: "aptitude", difficulty: "easy" })));
    expect(await screen.findByText("What is 15% of 240?")).toBeInTheDocument();
  });

  it("practice flow: answer hidden until submitted, then feedback, then results", async () => {
    vi.spyOn(api, "trainingStart").mockResolvedValue(ATTEMPT());
    const answered = mcqItem({
      answered: true, answer: { index: 0 },
      result: { is_correct: false, correct_index: 1, explanation: "15% of 240 = 0.15 × 240 = 36.", model_answer: null, score: 0, score_kind: "objective", evaluation: null },
    });
    const ans = vi.spyOn(api, "trainingAnswer").mockResolvedValue({ saved: true, item: answered });
    const done = ATTEMPT({
      status: "COMPLETED", items: [answered, mcqItem({ id: "i2", position: 2 })],
      summary: {
        total_questions: 2, answered: 1, skipped: 1, correct: 0, objective_total: 1, objective_pct: 0, estimated_pct: null,
        self_assessed_pct: null, overall_pct: 0, total_time_sec: 4, avg_time_sec: 4, by_topic: [{ round: "aptitude", topic: "percentages", label: "Percentages", attempted: 1, score_pct: 0 }],
        by_round: {}, strengths: [], weak_areas: ["Percentages"], change_vs_previous: null, previous_overall_pct: null,
        suggestions: [{ title: "Review Percentages", reason: "You scored 0% here.", action: { type: "practice", round: "aptitude", topic: "percentages", difficulty: "easy", mode: "practice" } }],
        score_notes: "Objective = exact-match MCQ.",
      },
    });
    const fin = vi.spyOn(api, "trainingFinish").mockResolvedValue(done);
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /^Start/ }));
    await screen.findByText("What is 15% of 240?");
    expect(screen.queryByText(/Explanation/)).toBeNull(); // nothing revealed before answering
    expect(screen.getByRole("button", { name: "Submit answer" })).toBeDisabled();

    await userEvent.click(screen.getByLabelText("32"));
    await userEvent.click(screen.getByRole("button", { name: "Submit answer" }));
    expect(ans).toHaveBeenCalledWith("a1", expect.objectContaining({ item_id: "i1", index: 0 }));
    const fb = await screen.findByRole("region", { name: "Feedback" });
    expect(within(fb).getByText("Not quite")).toBeInTheDocument();
    expect(within(fb).getByText(/15% of 240 = 0.15/)).toBeInTheDocument();
    expect(within(fb).getByText("Objective score")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Finish & see results" }));
    await waitFor(() => expect(fin).toHaveBeenCalled());
    expect(await screen.findByRole("heading", { name: /Results/ })).toBeInTheDocument();
    expect(screen.getAllByText("Percentages").length).toBeGreaterThan(1); // topic bar + weak-area summary
    expect(screen.getByRole("button", { name: "Practise" })).toBeInTheDocument();
  });

  it("exam flow: saving an answer never reveals correctness; shows a countdown", async () => {
    const deadline = new Date(Date.now() + 5 * 60_000).toISOString();
    vi.spyOn(api, "trainingStart").mockResolvedValue(ATTEMPT({ mode: "exam", time_limit_sec: 300, deadline }));
    vi.spyOn(api, "trainingAnswer").mockResolvedValue({ saved: true, item_id: "i1" });
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /^Start/ }));
    await screen.findByText("What is 15% of 240?");
    expect(screen.getByRole("timer")).toHaveTextContent(/0[45]:\d\d/);
    await userEvent.click(screen.getByLabelText("36"));
    await userEvent.click(screen.getByRole("button", { name: "Save answer" }));
    await waitFor(() => expect(screen.getByText(/1 answered/)).toBeInTheDocument());
    expect(screen.queryByRole("region", { name: "Feedback" })).toBeNull();
    expect(screen.getByRole("button", { name: "Submit exam" })).toBeInTheDocument();
  });

  it("mock interview: no skipping ahead and no going back", async () => {
    vi.spyOn(api, "trainingStart").mockResolvedValue(ATTEMPT({ mode: "mock", round: "mock", topic: null }));
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /^Start/ }));
    await screen.findByText("What is 15% of 240?");
    expect(screen.queryByRole("button", { name: /^Next/ })).toBeNull();
    expect(screen.getByRole("button", { name: /Previous/ })).toBeDisabled();
  });

  it("shows server errors when a session cannot be started", async () => {
    vi.spyOn(api, "trainingStart").mockRejectedValue(new ApiError("No questions are available for this selection yet.", 404));
    renderView("aptitude");
    await userEvent.click(await screen.findByRole("button", { name: "Start practice" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No questions are available");
  });

  it("round picker: sends the chosen topic/difficulty and explains why AI generation is disabled", async () => {
    const start = vi.spyOn(api, "trainingStart").mockResolvedValue(ATTEMPT());
    renderView("aptitude");
    await userEvent.click(await screen.findByRole("button", { name: /aptitude topic/ }));
    await userEvent.selectOptions(screen.getByLabelText("Difficulty"), "hard");
    expect(screen.getByRole("checkbox", { name: /AI-generated questions/ })).toBeDisabled();
    expect(screen.getAllByText(/no AI provider is configured/i).length).toBeGreaterThan(0);
    await userEvent.click(screen.getByRole("button", { name: "Start practice" }));
    await waitFor(() => expect(start).toHaveBeenCalledWith(expect.objectContaining({ mode: "practice", round: "aptitude", topic: "aptitude-topic", difficulty: "hard", generate: false })));
  });

  it("coding questions state that code is not executed", async () => {
    const coding = mcqItem({
      id: "c1", round: "coding", topic: "hashing", qtype: "code", options: null, prompt: "Two Sum\n\nFind two numbers.",
      coding: { title: "Two Sum", input_format: "ints", output_format: "indices", constraints: [], examples: [{ input: "2 7\n9", output: "0 1" }], hints: ["Use a hash map"], tests: [{ input: "2 7\n9", output: "0 1" }], time_complexity: "O(n)", space_complexity: "O(n)", concepts: ["hash map"] },
    });
    vi.spyOn(api, "trainingStart").mockResolvedValue(ATTEMPT({ round: "coding", items: [coding] }));
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /^Start/ }));
    expect(await screen.findByText(/It is not executed/)).toBeInTheDocument();
    expect(screen.getByText(/does not run your code/i)).toBeInTheDocument();
    expect(screen.queryByText("Use a hash map")).toBeNull(); // hints hidden until requested
    await userEvent.click(screen.getByRole("button", { name: /Show hints/ }));
    expect(screen.getByText("Use a hash map")).toBeInTheDocument();
  });

  it("resume tab: cannot start without data, and states nothing is invented", async () => {
    vi.spyOn(api, "trainingProfile").mockResolvedValue(PROGRESS().profile);
    renderView("resume");
    expect(await screen.findByRole("button", { name: "Start project interview" })).toBeDisabled();
    expect(screen.getByText(/nothing is invented/i)).toBeInTheDocument();
  });
});
