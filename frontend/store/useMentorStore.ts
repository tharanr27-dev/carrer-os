import { create } from "zustand";
import { api, ApiError, errorMessage, type MentorSuggestion } from "@/lib/api";

export interface ChatMessage {
  id: string;
  sender: "ai" | "user";
  content: string;
  timestamp: Date;
  /** True when the provider could not answer this message; it was not saved and can be retried. */
  failed?: boolean;
}

interface MentorState {
  isOpen: boolean;
  /** True while the full mentor page is shown; the floating widget would cover its controls. */
  widgetHidden: boolean;
  sessionId: string | null;
  messages: ChatMessage[];
  isTyping: boolean;
  isLoadingHistory: boolean;
  error: string | null;
  /** `null` until the server has been asked; `false` means no AI provider is configured. */
  aiAvailable: boolean | null;
  /** Next steps from the user's saved activity (separate from chat answers). */
  suggestions: MentorSuggestion[];
  suggestedPrompts: string[];
  toggleOpen: () => void;
  setOpen: (isOpen: boolean) => void;
  setWidgetHidden: (hidden: boolean) => void;
  /** Restores the latest conversation and server status (once per page load). */
  loadHistory: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  /** Re-sends the last message that failed, without duplicating it. */
  retryLast: () => Promise<void>;
  /** Starts a fresh backend conversation. */
  newConversation: () => Promise<void>;
}

const initialSuggestedPrompts = [
  "Explain the difference between a list and a tuple in Python.",
  "How should I prepare for a software developer interview?",
  "What should I put on a fresher resume?",
  "How do I start learning data structures and algorithms?",
];

let historyLoaded = false;

/** Test helper: forget that history was loaded and clear conversation state. */
export function resetMentorForTests() {
  historyLoaded = false;
  useMentorStore.setState({ sessionId: null, messages: [], isTyping: false, error: null, aiAvailable: null, suggestions: [] });
}

/** Maps API failures to short, honest messages (401/403/429/timeouts/provider outages). */
export function mentorErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return "Your session has expired. Please sign in again.";
    if (error.status === 403) return "You do not have access to this conversation. Start a new conversation to continue.";
    if (error.status === 0) return error.message;
    return error.message;
  }
  return errorMessage(error, "The mentor could not respond. Please try again.");
}

export const useMentorStore = create<MentorState>((set, get) => ({
  isOpen: false,
  widgetHidden: false,
  sessionId: null,
  messages: [],
  isTyping: false,
  isLoadingHistory: false,
  error: null,
  aiAvailable: null,
  suggestions: [],
  suggestedPrompts: initialSuggestedPrompts,

  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  setOpen: (isOpen) => set({ isOpen }),
  setWidgetHidden: (widgetHidden) => set({ widgetHidden }),

  loadHistory: async () => {
    if (historyLoaded) return;
    historyLoaded = true;
    set({ isLoadingHistory: true, error: null });
    try {
      const [session, status, suggestions] = await Promise.all([
        api.latestMentorSession(),
        api.mentorStatus().catch(() => null),
        api.mentorSuggestions().catch(() => [] as MentorSuggestion[]),
      ]);
      set({ aiAvailable: status ? status.ai_available : null, suggestions });
      if (session) {
        set({
          sessionId: session.id,
          messages: session.messages
            .filter((m) => m.role === "USER" || m.role === "AI")
            .map((m) => ({
              id: m.id,
              sender: m.role === "AI" ? "ai" : "user",
              content: m.content,
              timestamp: new Date(),
            })),
        });
      }
    } catch (error) {
      historyLoaded = false;
      set({ error: mentorErrorMessage(error) });
    } finally {
      set({ isLoadingHistory: false });
    }
  },

  sendMessage: async (content) => {
    const text = content.trim();
    if (!text || get().isTyping) return;

    const userMsg: ChatMessage = { id: `local-${Date.now()}`, sender: "user", content: text, timestamp: new Date() };
    set((state) => ({
      messages: [...state.messages.filter((m) => !m.failed), userMsg],
      isTyping: true,
      error: null,
    }));
    await deliver(text, userMsg.id, set, get);
  },

  retryLast: async () => {
    const failed = get().messages.find((m) => m.failed);
    if (!failed || get().isTyping) return;
    set((state) => ({
      messages: state.messages.map((m) => (m.id === failed.id ? { ...m, failed: false } : m)),
      isTyping: true,
      error: null,
    }));
    await deliver(failed.content, failed.id, set, get);
  },

  newConversation: async () => {
    set({ isTyping: true, error: null });
    try {
      const session = await api.createMentorSession();
      set({ sessionId: session.id, messages: [], isTyping: false });
    } catch (error) {
      set({ isTyping: false, error: mentorErrorMessage(error) });
    }
  },
}));

type Set = (partial: Partial<MentorState> | ((s: MentorState) => Partial<MentorState>)) => void;

async function deliver(text: string, userMsgId: string, set: Set, get: () => MentorState) {
  try {
    let sessionId = get().sessionId;
    if (!sessionId) {
      sessionId = (await api.createMentorSession()).id;
      set({ sessionId });
    }
    const reply = await api.sendMentorMessage(sessionId, text);
    set((state) => ({
      messages: [...state.messages, { id: reply.id, sender: "ai", content: reply.content, timestamp: new Date() }],
      isTyping: false,
      aiAvailable: true,
    }));
  } catch (error) {
    // Keep the user's message visible, mark it failed (nothing was saved server-side) and say why.
    const forbidden = error instanceof ApiError && (error.status === 403 || error.status === 404);
    set((state) => ({
      messages: state.messages.map((m) => (m.id === userMsgId ? { ...m, failed: true } : m)),
      isTyping: false,
      sessionId: forbidden ? null : state.sessionId,
      aiAvailable: error instanceof ApiError && error.status === 503 && /not set up/i.test(error.message) ? false : state.aiAvailable,
      error: mentorErrorMessage(error),
    }));
  }
}
