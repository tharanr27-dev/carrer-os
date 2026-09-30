import { create } from "zustand";
import { api, errorMessage } from "@/lib/api";

export interface ChatMessage {
  id: string;
  sender: "ai" | "user";
  content: string;
  timestamp: Date;
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
  suggestedPrompts: string[];
  toggleOpen: () => void;
  setOpen: (isOpen: boolean) => void;
  setWidgetHidden: (hidden: boolean) => void;
  /** Restores the latest conversation from the backend (once per page load). */
  loadHistory: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  /** Starts a fresh backend conversation. */
  newConversation: () => Promise<void>;
}

const initialSuggestedPrompts = [
  "How do I improve my resume for frontend roles?",
  "What is the skill gap for becoming a Solutions Architect?",
  "Tell me about latest trends in AI Engineering.",
  "Mock interview me for a React Developer position.",
];

let historyLoaded = false;

export const useMentorStore = create<MentorState>((set, get) => ({
  isOpen: false,
  widgetHidden: false,
  sessionId: null,
  messages: [],
  isTyping: false,
  isLoadingHistory: false,
  error: null,
  suggestedPrompts: initialSuggestedPrompts,

  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  setOpen: (isOpen) => set({ isOpen }),
  setWidgetHidden: (widgetHidden) => set({ widgetHidden }),

  loadHistory: async () => {
    if (historyLoaded) return;
    historyLoaded = true;
    set({ isLoadingHistory: true, error: null });
    try {
      const session = await api.latestMentorSession();
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
      set({ error: errorMessage(error) });
    } finally {
      set({ isLoadingHistory: false });
    }
  },

  sendMessage: async (content) => {
    const text = content.trim();
    if (!text || get().isTyping) return;

    const userMsg: ChatMessage = { id: `local-${Date.now()}`, sender: "user", content: text, timestamp: new Date() };
    set((state) => ({ messages: [...state.messages, userMsg], isTyping: true, error: null }));

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
      }));
    } catch (error) {
      // Keep the user's message visible and surface why no reply arrived.
      set({ isTyping: false, error: errorMessage(error, "The mentor could not respond. Please try again.") });
    }
  },

  newConversation: async () => {
    set({ isTyping: true, error: null });
    try {
      const session = await api.createMentorSession();
      set({ sessionId: session.id, messages: [], isTyping: false });
    } catch (error) {
      set({ isTyping: false, error: errorMessage(error) });
    }
  },
}));
