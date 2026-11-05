import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RoleTraining } from "../interview-prep/role-training";
import { api, ApiError, API_BASE_URL, RoleItem, RoleResult, RoleReview, RoleSession, RoleSummary } from "@/lib/api";

const result = (over: Partial<RoleResult> = {}): RoleResult => ({
  status: "correct", status_label: "Correct", marks: 1, max_marks: 1, score: 1, method: "objective", disclaimer: null,
  explanation: "A sound level meter measures decibels.", got_right: ["You chose the correct option: A sound level meter"], missing: [],
  suggestion: "Good. Try a harder question on this topic.", your_answer: { index: 0 }, correct_index: 0, correct_answer: "A sound level meter", ...over,
});

const item = (over: Partial<RoleItem> = {}): RoleItem => ({
  id: "i1", position: 1, topic: "cybersecurity", topic_label: "Cybersecurity Fundamentals", difficulty: "easy", qtype: "mcq", kind: "foundational",
  source: "curated", review_status: "reviewed", prompt: "What does the CIA triad stand for?",
  options: ["Confidentiality, Integrity, Availability", "Control, Identity, Access", "Cryptography, Identification, Authorization", "Compliance, Inspection, Audit"],
  max_marks: 1, answered: false, is_repeat: false, is_workplace: false, result: null, ...over,
});

const textItem = (over: Partial<RoleItem> = {}): RoleItem =>
  item({ id: "i2", position: 2, qtype: "text", options: null, max_marks: 2, prompt: "Describe how you would respond to a security incident.", ...over });

const session = (over: Partial<RoleSession> = {}): RoleSession => ({
  id: "s1", status: "IN_PROGRESS",
  role: { title: "Cybersecurity Analyst", key: "analyst-cybersecurity", matched_title: "Cybersecurity Analyst", mapped: true, topics: [{ slug: "cybersecurity", label: "Cybersecurity Fundamentals" }] },
  level: "fresher", difficulty: "easy", focus: "mixed", requested: null,
  plan: { notes: ["3 of 3 questions are new to you."], allocation: [{ topic: "cybersecurity", label: "Cybersecurity Fundamentals", count: 3, reason: "not practised for this role yet" }], fresh: 3, repeats: 0, workplace: 0, generation: { requested: 0, accepted: 0, rejected: 0, used: false } },
  notices: [], started_at: "2026-10-27T00:00:00Z", ended_at: null, total_questions: 2, answered: 0, next_position: 1,
  items: [item(), textItem()], summary: null, ai_available: false, scoring_rules: [], ...over,
});

const SUMMARY: RoleSummary = {
  role_title: "Cybersecurity Analyst", difficulty: "easy", level: "fresher", topics: ["Cybersecurity Fundamentals"],
  total_questions: 2, answered: 1, unanswered: 1, correct: 1, partial: 0, incorrect: 0, manual_review: 0,
  marks_earned: 1, marks_available: 3, percentage: 33.3,
  by_topic: [{ topic: "cybersecurity", label: "Cybersecurity Fundamentals", questions: 2, answered: 1, earned: 1, available: 3, pct: 33.3 }],
  strong_topics: [], weak_topics: ["Cybersecurity Fundamentals"],
  revision: [{ topic: "cybersecurity", label: "Cybersecurity Fundamentals", reason: "You scored 33.3% here (1 of 3 marks)." }],
  next: { improve_weak_available: true, weak_labels: ["Cybersecurity Fundamentals"] },
  scoring_rules: ["Unanswered questions earn 0 marks and are included in the total."],
};

const completed = (): RoleSession =>
  session({
    status: "COMPLETED", answered: 1, summary: SUMMARY, ended_at: "2026-10-27T00:10:00Z",
    items: [item({ answered: true, result: result() }), textItem({ result: result({ status: "unanswered", marks: 0, max_marks: 2, your_answer: null, correct_answer: null, correct_index: undefined, expected_concepts: ["Contain"], model_answer: "Contain, eradicate, recover." }) })],
  });

const review = (filter: RoleReview["filter"] = "all"): RoleReview => {
  const s = completed();
  const items = filter === "all" ? s.items : s.items.filter((i) => (i.result?.status ?? "unanswered") === filter);
  return { id: "s1", filter, counts: { all: 2, correct: 1, partial: 0, incorrect: 0, unanswered: 1, manual_review: 0 }, summary: SUMMARY, items };
};

const ROLES = {
  roles: [{ title: "Cybersecurity Analyst", family: "Cloud & Security", aliases: [], topics: [{ slug: "cybersecurity", label: "Cybersecurity Fundamentals" }], available_questions: 12 }],
  query: "", exact_match: false, custom_allowed: true, recent: [], ai_available: false,
};
const RESOLVED = (over = {}) => ({
  title: "Cybersecurity Analyst", key: "analyst-cybersecurity", match: "catalog" as const, matched_title: "Cybersecurity Analyst", family: "Cloud & Security",
  mapped: true, level_hint: null, notes: [], topics: [{ slug: "cybersecurity", label: "Cybersecurity Fundamentals", available: 6 }],
  available_questions: 12, unseen_questions: 12, ai_available: false, can_start: true, message: null, ...over,
});

function renderView() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><RoleTraining /></QueryClientProvider>);
}

describe("Role training", () => {
  beforeEach(() => {
    vi.spyOn(api, "roleSearch").mockResolvedValue(ROLES);
    vi.spyOn(api, "roleSessions").mockResolvedValue({ page: 1, size: 8, total: 0, items: [] });
    vi.spyOn(api, "roleResolve").mockResolvedValue(RESOLVED());
  });
  afterEach(() => vi.restoreAllMocks());

  it("searches roles, selects one and starts a session with the chosen options", async () => {
    const start = vi.spyOn(api, "roleSessionStart").mockResolvedValue(session());
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /Cybersecurity Analyst/ }));
    expect(await screen.findByText(/12 reviewed questions match this role/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Cybersecurity Fundamentals" }));
    await userEvent.selectOptions(screen.getByLabelText("Difficulty"), "hard");
    await userEvent.selectOptions(screen.getByLabelText("Number of questions"), "15");
    await userEvent.click(screen.getByRole("button", { name: /Start practice/ }));
    await waitFor(() => expect(start).toHaveBeenCalledWith({
      role_title: "Cybersecurity Analyst", level: null, difficulty: "hard", topics: ["cybersecurity"], count: 15, generate: false,
    }));
    expect(await screen.findByText(/Question 1 of 2/)).toBeInTheDocument();
  });

  it("offers a custom title when the typed role is not in the list and says what is unavailable", async () => {
    vi.spyOn(api, "roleSearch").mockResolvedValue({ ...ROLES, roles: [], query: "Sound Engineer", exact_match: false });
    vi.spyOn(api, "roleResolve").mockResolvedValue(RESOLVED({
      title: "Sound Engineer", key: "engineer-sound", match: "none", matched_title: null, mapped: false, topics: [], available_questions: 0, unseen_questions: 0,
      can_start: false, message: "There are no reviewed questions for this job title yet and AI question generation is not configured, so a role-specific session cannot be built. Pick a related role from the list instead.",
    }));
    renderView();
    await userEvent.type(screen.getByLabelText("Job role"), "Sound Engineer");
    await userEvent.click(await screen.findByRole("button", { name: /Use custom title/ }));
    expect(await screen.findByText(/custom role/)).toBeInTheDocument();
    expect(screen.getByText(/AI question generation is not configured/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Start practice/ })).toBeDisabled();
    expect(screen.getByText(/Not available: no AI provider is configured/)).toBeInTheDocument();
  });

  it("shows the server's error when a session cannot be started", async () => {
    vi.spyOn(api, "roleSessionStart").mockRejectedValue(new ApiError("No role-specific questions are available for 'X' right now.", 422));
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /Cybersecurity Analyst/ }));
    await userEvent.click(await screen.findByRole("button", { name: /Start practice/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No role-specific questions are available");
  });

  it("gives instant feedback after Submit Answer: status, marks, correct answer, explanation, then Next Question", async () => {
    vi.spyOn(api, "roleSessionStart").mockResolvedValue(session());
    const answer = vi.spyOn(api, "roleSessionAnswer").mockResolvedValue({
      saved: true, already_answered: false,
      item: item({ answered: true, result: result({ status: "incorrect", marks: 0, got_right: [], missing: ['You chose "Control, Identity, Access". The correct answer is "Confidentiality, Integrity, Availability".'], correct_answer: "Confidentiality, Integrity, Availability", your_answer: { index: 1 }, explanation: "The CIA triad is Confidentiality, Integrity and Availability." }) }),
    });
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /Cybersecurity Analyst/ }));
    await userEvent.click(await screen.findByRole("button", { name: /Start practice/ }));
    const submit = await screen.findByRole("button", { name: "Submit Answer" });
    expect(submit).toBeDisabled(); // nothing chosen yet
    expect(screen.queryByTestId("role-feedback")).toBeNull(); // answer not revealed before submission
    await userEvent.click(screen.getByLabelText("Control, Identity, Access"));
    await userEvent.click(submit);
    const fb = await screen.findByTestId("role-feedback");
    expect(answer).toHaveBeenCalledWith("s1", expect.objectContaining({ item_id: "i1", index: 1 }));
    expect(fb).toHaveTextContent("Incorrect");
    expect(fb).toHaveTextContent("0 / 1 marks");
    expect(fb).toHaveTextContent("Correct answer: Confidentiality, Integrity, Availability");
    expect(fb).toHaveTextContent("The CIA triad is Confidentiality, Integrity and Availability.");
    expect(fb).toHaveTextContent("What was missing or incorrect");
    await userEvent.click(screen.getByRole("button", { name: /Next Question/ }));
    expect(await screen.findByText(/Question 2 of 2/)).toBeInTheDocument();
    expect(screen.getByLabelText("Your answer")).toBeInTheDocument(); // text question uses a textarea
  });

  it("submits written answers and shows partial credit with expected concepts and a disclaimer", async () => {
    vi.spyOn(api, "roleSessionStart").mockResolvedValue(session({ items: [textItem({ position: 1 })] , total_questions: 1 }));
    vi.spyOn(api, "roleSessionAnswer").mockResolvedValue({
      saved: true, already_answered: false,
      item: textItem({ position: 1, answered: true, result: result({ status: "partial", status_label: "Partially Correct", marks: 1, max_marks: 2, method: "keyword_estimate", disclaimer: "Rule-based estimate: it checks which ideas appear.", got_right: ["Covered: Contain"], missing: ["Missing: Evidence"], expected_concepts: ["Contain", "Evidence"], model_answer: "Contain the device, preserve evidence.", correct_answer: null, correct_index: undefined, your_answer: { text: "I would contain it." } }) }),
    });
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /Cybersecurity Analyst/ }));
    await userEvent.click(await screen.findByRole("button", { name: /Start practice/ }));
    await userEvent.type(await screen.findByLabelText("Your answer"), "I would contain it.");
    await userEvent.click(screen.getByRole("button", { name: "Submit Answer" }));
    const fb = await screen.findByTestId("role-feedback");
    expect(fb).toHaveTextContent("Partially Correct");
    expect(fb).toHaveTextContent("1 / 2 marks");
    expect(fb).toHaveTextContent("Expected concepts: Contain, Evidence");
    expect(fb).toHaveTextContent("Rule-based estimate");
    expect(screen.getByRole("button", { name: "Finish assessment" })).toBeInTheDocument();
  });

  it("shows the answer error without losing the draft", async () => {
    vi.spyOn(api, "roleSessionStart").mockResolvedValue(session({ items: [textItem({ position: 1 })], total_questions: 1 }));
    vi.spyOn(api, "roleSessionAnswer").mockRejectedValue(new ApiError("Cannot reach the server. Check your connection and try again.", 0));
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /Cybersecurity Analyst/ }));
    await userEvent.click(await screen.findByRole("button", { name: /Start practice/ }));
    const box = await screen.findByLabelText("Your answer");
    await userEvent.type(box, "My draft answer");
    await userEvent.click(screen.getByRole("button", { name: "Submit Answer" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Cannot reach the server");
    expect(box).toHaveValue("My draft answer");
  });

  it("finishes into a review whose score comes from the server, with filters, unanswered items and next-step buttons", async () => {
    vi.spyOn(api, "roleSessionStart").mockResolvedValue(session());
    vi.spyOn(api, "roleSessionFinish").mockResolvedValue(completed());
    const rev = vi.spyOn(api, "roleSessionReview").mockImplementation(async (_id, f = "all") => review(f));
    const again = vi.spyOn(api, "roleSessionAgain").mockResolvedValue(session({ id: "s2" }));
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /Cybersecurity Analyst/ }));
    await userEvent.click(await screen.findByRole("button", { name: /Start practice/ }));
    await userEvent.click(await screen.findByRole("button", { name: /Finish now/ }));
    expect(await screen.findByTestId("role-score")).toHaveTextContent("33%");
    expect(screen.getByText("1 of 3 marks")).toBeInTheDocument();
    expect(screen.getByText(/Suggested topics for revision/)).toBeInTheDocument();
    expect(await screen.findAllByTestId("review-item")).toHaveLength(2);
    // filters
    for (const name of ["All (2)", "Correct (1)", "Partially Correct (0)", "Incorrect (0)", "Unanswered (1)"]) {
      expect(screen.getByRole("tab", { name })).toBeInTheDocument();
    }
    await userEvent.click(screen.getByRole("tab", { name: "Unanswered (1)" }));
    await waitFor(() => expect(rev).toHaveBeenCalledWith("s1", "unanswered"));
    await waitFor(() => expect(screen.getAllByTestId("review-item")).toHaveLength(1));
    const only = screen.getAllByTestId("review-item");
    expect(within(only[0]).getByText("— not answered")).toBeInTheDocument();
    expect(only[0]).toHaveTextContent("Expected concepts: Contain");
    // next steps
    await userEvent.click(screen.getByRole("button", { name: /Improve Weak Areas/ }));
    await waitFor(() => expect(again).toHaveBeenCalledWith("s1", "weak"));
    expect(await screen.findByText(/Question 1 of 2/)).toBeInTheDocument(); // a new session opened
  });

  it("Practise Again requests a mixed session", async () => {
    vi.spyOn(api, "roleSessions").mockResolvedValue({ page: 1, size: 8, total: 1, items: [{ id: "s1", role_title: "Cybersecurity Analyst", status: "COMPLETED", difficulty: "easy", started_at: "x", ended_at: "y", total_questions: 2, answered: 1, percentage: 33.3 }] });
    vi.spyOn(api, "roleSession").mockResolvedValue(completed());
    vi.spyOn(api, "roleSessionReview").mockResolvedValue(review());
    const again = vi.spyOn(api, "roleSessionAgain").mockResolvedValue(session({ id: "s3" }));
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: "Open review" }));
    await userEvent.click(await screen.findByRole("button", { name: /Practise Again/ }));
    await waitFor(() => expect(again).toHaveBeenCalledWith("s1", "mixed"));
  });

  it("states repeats and AI-generated questions honestly", async () => {
    vi.spyOn(api, "roleSessionStart").mockResolvedValue(session({
      notices: ["2 question(s) repeat earlier practice on purpose: the stored bank for this role has no more unseen questions. They are marked 'Seen before'."],
      items: [item({ is_repeat: true }), textItem({ source: "generated", review_status: "unreviewed" })],
    }));
    renderView();
    await userEvent.click(await screen.findByRole("button", { name: /Cybersecurity Analyst/ }));
    await userEvent.click(await screen.findByRole("button", { name: /Start practice/ }));
    expect(await screen.findByText(/repeat earlier practice on purpose/)).toBeInTheDocument();
    expect(screen.getByText("Seen before")).toBeInTheDocument();
  });

  it("matches the backend routes and request bodies", async () => {
    vi.restoreAllMocks(); // use the real client methods here; only the network is stubbed
    const calls: { url: string; init: RequestInit }[] = [];
    vi.spyOn(globalThis, "fetch").mockImplementation(async (url, init) => {
      calls.push({ url: String(url), init: (init ?? {}) as RequestInit });
      return new Response(JSON.stringify({ success: true, data: {} }), { status: 200, headers: { "Content-Type": "application/json" } });
    });
    await api.roleSearch("cloud");
    await api.roleResolve("Cloud Engineer");
    await api.roleProgress("Cloud Engineer");
    await api.roleSessionStart({ role_title: "Cloud Engineer", count: 5 });
    await api.roleSessionAnswer("s1", { item_id: "i1", index: 2 });
    await api.roleSessionFinish("s1");
    await api.roleSessionReview("s1", "partial");
    await api.roleSessionAgain("s1", "weak", 6);
    const seen = calls.map((c) => `${c.init.method ?? "GET"} ${c.url.replace(API_BASE_URL, "").split("?")[0]}`);
    expect(seen).toEqual([
      "GET /training/roles", "POST /training/roles/resolve", "GET /training/roles/progress", "POST /training/role-sessions",
      "POST /training/role-sessions/s1/answer", "POST /training/role-sessions/s1/finish", "GET /training/role-sessions/s1/review",
      "POST /training/role-sessions/s1/again",
    ]);
    expect(calls[2].url).toContain("title=Cloud+Engineer");
    expect(calls[6].url).toContain("status=partial");
    expect(JSON.parse(String(calls[4].init.body))).toEqual({ item_id: "i1", index: 2 });
    expect(JSON.parse(String(calls[7].init.body))).toEqual({ focus: "weak", count: 6 });
  });
});
