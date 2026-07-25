import { create } from "zustand";

export interface ChatMessage {
  id: string;
  sender: "ai" | "user";
  content: string;
  timestamp: Date;
  attachments?: { name: string; size: string; type: string }[];
}

export interface QuickAction {
  label: string;
  prompt: string;
}

interface MentorState {
  isOpen: boolean;
  messages: ChatMessage[];
  isTyping: boolean;
  suggestedPrompts: string[];
  toggleOpen: () => void;
  setOpen: (isOpen: boolean) => void;
  sendMessage: (content: string, attachments?: { name: string; size: string; type: string }[]) => Promise<void>;
  clearHistory: () => void;
}

const defaultWelcomeMessage: ChatMessage = {
  id: "msg-welcome",
  sender: "ai",
  content: "Hi, I'm your CareerOS AI Mentor! 🚀 I can help you prepare for technical interviews, check your resume against ATS tracking systems, explore career pathways, or recommend target skills. What is on your mind today?",
  timestamp: new Date(),
};

const initialSuggestedPrompts = [
  "How do I improve my resume for frontend roles?",
  "What is the skill gap for becoming a Solutions Architect?",
  "Tell me about latest trends in AI Engineering.",
  "Mock interview me for a React Developer position.",
];

export const useMentorStore = create<MentorState>((set, get) => ({
  isOpen: false,
  messages: [defaultWelcomeMessage],
  isTyping: false,
  suggestedPrompts: initialSuggestedPrompts,

  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  setOpen: (isOpen) => set({ isOpen }),

  sendMessage: async (content, attachments) => {
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: "user",
      content,
      timestamp: new Date(),
      attachments,
    };

    set((state) => ({
      messages: [...state.messages, userMsg],
      isTyping: true,
    }));

    // Simulate AI response logic
    await new Promise((resolve) => setTimeout(resolve, 1500));

    let responseContent = "";
    const lowerContent = content.toLowerCase();

    if (lowerContent.includes("resume") || lowerContent.includes("ats")) {
      responseContent = "I can definitely help with your resume! In CareerOS AI, head over to the **Resume Center** dashboard. There, you can upload your resume, get an ATS score, identify missing keywords for your target roles, and get actionable improvement recommendations.";
    } else if (lowerContent.includes("skill") || lowerContent.includes("gap") || lowerContent.includes("architect")) {
      responseContent = "Exploring skill gaps is highly recommended! If you visit the **Career Dashboard**, you'll see a radial readiness gauge and a Skill Gap Analysis. Currently, to transition towards a Solutions Architect, you should build skills in System Design (caching, CDNs), Cloud Architecture (AWS/GCP), and Security protocols.";
    } else if (lowerContent.includes("interview") || lowerContent.includes("mock") || lowerContent.includes("react")) {
      responseContent = "Let's do a quick mock run! I'll ask you a React 19 question: *What is the purpose of the new 'use' hook in React 19, and how does it differ from traditional hooks with respect to conditional execution?* Reply to this, and I'll grade your answer!";
    } else if (lowerContent.includes("trend") || lowerContent.includes("ai")) {
      responseContent = "AI Engineering is booming! Core requirements include knowledge of Large Language Models (LLMs), prompt orchestration frameworks (LangChain, LlamaIndex), vectors databases (Pinecone, Chroma), and agentic workflows. We have recommended learning tracks for these in your Career Dashboard.";
    } else {
      responseContent = "That's a great question. In CareerOS, we map your education and skills to jobs in real-time. I suggest visiting the **Career Discovery** page to run our interactive conversational onboarding, which will fine-tune my guidance specifically for your targets!";
    }

    const aiMsg: ChatMessage = {
      id: `msg-${Date.now() + 1}`,
      sender: "ai",
      content: responseContent,
      timestamp: new Date(),
    };

    set((state) => ({
      messages: [...state.messages, aiMsg],
      isTyping: false,
    }));
  },

  clearHistory: () => {
    set({
      messages: [
        {
          id: `msg-${Date.now()}`,
          sender: "ai",
          content: "Chat history cleared. How can I help you excel in your career today?",
          timestamp: new Date(),
        },
      ],
    });
  },
}));
