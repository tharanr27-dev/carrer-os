import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MentorWorkspaceView } from "@/features/student/mentor";
import { FloatingMentor } from "../components/floating-mentor";
import { api, ApiError, API_BASE_URL } from "@/lib/api";
import { resetMentorForTests, useMentorStore } from "@/store/useMentorStore";

const SESSION = { id: "s1", title: "t", status: "ACTIVE", messages: [] };
const STEPS = [{ title: "Upload your résumé for analysis", reason: "No résumé has been analysed yet." }];

function mockServer({ ai = true, session = SESSION as typeof SESSION | null } = {}) {
  vi.spyOn(api, "latestMentorSession").mockResolvedValue(session as never);
  vi.spyOn(api, "mentorStatus").mockResolvedValue({ ai_available: ai });
  vi.spyOn(api, "mentorSuggestions").mockResolvedValue(STEPS);
  vi.spyOn(api, "createMentorSession").mockResolvedValue(SESSION as never);
}

describe("AI Mentor chat", () => {
  beforeEach(() => {
    resetMentorForTests();
    Element.prototype.scrollIntoView = vi.fn(); // not implemented in jsdom
  });
  afterEach(() => vi.restoreAllMocks());

  it("shows a real answer from the backend and keeps suggestions separate", async () => {
    mockServer();
    const send = vi.spyOn(api, "sendMentorMessage").mockResolvedValue({ id: "m2", role: "AI", content: "A tuple is immutable.\nA list is not." });
    render(<MentorWorkspaceView />);
    expect(await screen.findByTestId("mentor-suggestions")).toHaveTextContent("Upload your résumé for analysis");
    await userEvent.type(screen.getByLabelText("Message the AI Mentor"), "List vs tuple?{Enter}");
    expect(send).toHaveBeenCalledWith("s1", "List vs tuple?");
    const answer = await screen.findByText(/A tuple is immutable/);
    expect(answer).toHaveTextContent("A list is not.");
    expect(screen.getByText("List vs tuple?")).toBeInTheDocument();
    expect(screen.getByTestId("mentor-suggestions")).not.toContainElement(answer); // not mixed into the answer
    expect(screen.queryByTestId("mentor-setup-notice")).toBeNull();
  });

  it("Shift+Enter adds a new line instead of sending; empty input cannot be sent", async () => {
    mockServer();
    const send = vi.spyOn(api, "sendMentorMessage").mockResolvedValue({ id: "m", role: "AI", content: "ok" });
    render(<MentorWorkspaceView />);
    const box = await screen.findByLabelText("Message the AI Mentor");
    const button = screen.getByRole("button", { name: "Send message" });
    expect(button).toBeDisabled();
    await userEvent.type(box, "line one{Shift>}{Enter}{/Shift}line two");
    expect(send).not.toHaveBeenCalled();
    expect(box).toHaveValue("line one\nline two");
    expect(button).toBeEnabled();
  });

  it("shows a loading indicator while waiting and disables sending", async () => {
    mockServer();
    let resolve!: (v: { id: string; role: string; content: string }) => void;
    vi.spyOn(api, "sendMentorMessage").mockReturnValue(new Promise((r) => (resolve = r)));
    render(<MentorWorkspaceView />);
    await userEvent.type(await screen.findByLabelText("Message the AI Mentor"), "Hi{Enter}");
    expect(await screen.findByText("Mentor is thinking…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send message" })).toBeDisabled();
    resolve({ id: "m", role: "AI", content: "Hello!" });
    expect(await screen.findByText("Hello!")).toBeInTheDocument();
    expect(screen.queryByText("Mentor is thinking…")).toBeNull();
  });

  it("shows the server's error, keeps the question, and Retry re-sends it without duplicating", async () => {
    mockServer();
    const send = vi
      .spyOn(api, "sendMentorMessage")
      .mockRejectedValueOnce(new ApiError("The AI Mentor took too long to answer. Please try again.", 504))
      .mockResolvedValueOnce({ id: "m9", role: "AI", content: "Joins combine tables." });
    render(<MentorWorkspaceView />);
    await userEvent.type(await screen.findByLabelText("Message the AI Mentor"), "Explain joins{Enter}");
    expect(await screen.findByRole("alert")).toHaveTextContent("took too long");
    expect(screen.getAllByText("Explain joins")).toHaveLength(1);
    await userEvent.click(screen.getByRole("button", { name: /Retry/ }));
    expect(await screen.findByText("Joins combine tables.")).toBeInTheDocument();
    expect(send).toHaveBeenCalledTimes(2);
    expect(send).toHaveBeenLastCalledWith("s1", "Explain joins");
    expect(screen.getAllByText("Explain joins")).toHaveLength(1);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it.each([
    [401, "Your session has expired"],
    [403, "do not have access"],
    [429, "too quickly"],
    [503, "temporarily overloaded"],
  ])("handles HTTP %i honestly", async (status, text) => {
    mockServer();
    vi.spyOn(api, "sendMentorMessage").mockRejectedValue(
      new ApiError(status === 429 ? "You are sending messages too quickly." : status === 503 ? "The AI provider is temporarily overloaded." : "x", status)
    );
    render(<MentorWorkspaceView />);
    await userEvent.type(await screen.findByLabelText("Message the AI Mentor"), "Hi{Enter}");
    expect(await screen.findByRole("alert")).toHaveTextContent(text);
  });

  it("explains the setup instead of pretending to chat when no AI provider is configured", async () => {
    mockServer({ ai: false });
    const send = vi.spyOn(api, "sendMentorMessage");
    render(<MentorWorkspaceView />);
    expect(await screen.findByTestId("mentor-setup-notice")).toHaveTextContent("GROQ_API_KEY");
    expect(screen.getByLabelText("Message the AI Mentor")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Send message" })).toBeDisabled();
    expect(send).not.toHaveBeenCalled();
    expect(await screen.findByTestId("mentor-suggestions")).toBeInTheDocument(); // real next steps still shown
  });

  it("restores saved history from the backend", async () => {
    mockServer({
      session: { ...SESSION, messages: [{ id: "a", role: "USER", content: "Earlier question" }, { id: "b", role: "AI", content: "Earlier answer" }] } as never,
    });
    render(<MentorWorkspaceView />);
    expect(await screen.findByText("Earlier answer")).toBeInTheDocument();
    expect(screen.getByText("Earlier question")).toBeInTheDocument();
  });

  it("the floating widget uses the same composer and sends to the real endpoint path", async () => {
    mockServer();
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ success: true, data: { id: "m1", role: "AI", content: "Hi there" } }), { status: 200, headers: { "Content-Type": "application/json" } })
    );
    render(<FloatingMentor />);
    await userEvent.click(screen.getByRole("button", { name: "Open mentor" }));
    await userEvent.type(await screen.findByLabelText("Message the AI Mentor"), "Hello{Enter}");
    expect(await screen.findByText("Hi there")).toBeInTheDocument();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(String(url)).toBe(`${API_BASE_URL}/mentor/sessions/s1/message`);
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({ content: "Hello" });
    await waitFor(() => expect(useMentorStore.getState().messages).toHaveLength(2));
  });
});
