"use client";

import React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import {
  Sparkles,
  User,
  Send,
  CheckCircle,
  FileCheck,
  MapPin,
  Briefcase,
  ChevronRight,
  BrainCircuit,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

interface ChatBubble {
  id: string;
  sender: "ai" | "user";
  content: string;
}

const interviewSteps = [
  {
    key: "intro",
    question: "Welcome to CareerOS Discovery! 🚀 I'm your onboarding assistant. Let's start with a brief overview. Tell me a bit about yourself—what are your main interests?",
    suggestions: ["I'm a CS major passionate about UI/UX.", "I'm a self-taught coder wanting to transition to tech.", "I love building AI tools and backend architectures."],
  },
  {
    key: "education",
    question: "Got it! What about your education? What is your major, college, and expected graduation year?",
    suggestions: ["BS in Computer Science, Stanford (2027)", "BE in Information Technology (2026)", "Self-Taught / Boot camp Graduate"],
  },
  {
    key: "skills",
    question: "Excellent. What core technical skill areas do you focus on?",
    suggestions: ["Frontend Development", "Backend Systems", "Full-Stack Development", "AI / Machine Learning"],
  },
  {
    key: "languages",
    question: "What programming languages are you most comfortable with?",
    suggestions: ["TypeScript, JavaScript, Python", "Python, Go, Java", "C++, Rust, Python"],
  },
  {
    key: "frameworks",
    question: "Which web frameworks do you build applications with?",
    suggestions: ["Next.js, React, Node.js", "Vue.js, Django, Fast API", "Spring Boot, Express, Angular"],
  },
  {
    key: "projects",
    question: "Tell me about a key project you've worked on. What did it solve?",
    suggestions: ["Built an AI SaaS generator using React 19.", "Created a real-time collaborative code editor.", "Designed a distributed cloud log analyzer."],
  },
  {
    key: "certifications",
    question: "Do you hold any professional certifications?",
    suggestions: ["AWS Cloud Practitioner", "Google UX Design Professional Certificate", "None, focused on project builds"],
  },
  {
    key: "experience",
    question: "What work or internship experience do you have?",
    suggestions: ["Summer Frontend Internship at a local startup", "Full-stack Freelance projects for 1 year", "No formal experience yet, seeking first internship"],
  },
  {
    key: "career_goal",
    question: "What is your primary career goal? What target role are you after?",
    suggestions: ["Frontend Engineer", "Full-Stack Engineer", "AI/ML Application Engineer", "Product Manager"],
  },
  {
    key: "pref_company",
    question: "What are your preferred or dream companies to join?",
    suggestions: ["Stripe, Vercel, Linear", "Google, Apple, Microsoft", "Early-stage AI Startups"],
  },
  {
    key: "pref_location",
    question: "Where is your preferred job location? Are you open to remote positions?",
    suggestions: ["Remote Only", "San Francisco / Bay Area", "New York / Hybrid", "London / Bangalore"],
  },
  {
    key: "expected_salary",
    question: "What is your expected starting annual salary range?",
    suggestions: ["$90,000 - $110,000", "$110,000 - $140,000", "$70,000 - $90,000"],
  },
  {
    key: "pref_domain",
    question: "Finally, what industry domains excite you the most?",
    suggestions: ["Developer Tools & Platforms", "Fintech & Payments", "Generative AI & LLMs", "SaaS Dashboards"],
  },
];

export default function CareerDiscovery() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=discovery");
    }
  }, [pathname, router]);

  const [stepIndex, setStepIndex] = React.useState(0);
  const [messages, setMessages] = React.useState<ChatBubble[]>([
    {
      id: "init",
      sender: "ai",
      content: interviewSteps[0].question,
    },
  ]);
  const [input, setInput] = React.useState("");
  const [isTyping, setIsTyping] = React.useState(false);
  const [responses, setResponses] = React.useState<Record<string, string>>({});
  const [isOnboardingCompleted, setIsOnboardingCompleted] = React.useState(false);

  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const handleNextStep = async (userAnswer: string) => {
    if (!userAnswer.trim()) return;

    // Save answer
    const currentStep = interviewSteps[stepIndex];
    const updatedResponses = { ...responses, [currentStep.key]: userAnswer };
    setResponses(updatedResponses);

    // Append user message
    const userMsg: ChatBubble = {
      id: `user-${Date.now()}`,
      sender: "user",
      content: userAnswer,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    // Check if finished
    if (stepIndex >= interviewSteps.length - 1) {
      setIsTyping(true);
      await new Promise((resolve) => setTimeout(resolve, 2000));
      setIsTyping(false);
      setIsOnboardingCompleted(true);
      return;
    }

    // Advance step
    const nextIndex = stepIndex + 1;
    setStepIndex(nextIndex);

    // AI Typing simulation
    setIsTyping(true);
    await new Promise((resolve) => setTimeout(resolve, 1200));
    setIsTyping(false);

    // Append AI next question
    const aiMsg: ChatBubble = {
      id: `ai-${Date.now()}`,
      sender: "ai",
      content: interviewSteps[nextIndex].question,
    };
    setMessages((prev) => [...prev, aiMsg]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleNextStep(input);
    }
  };

  const progressPercentage = Math.round((stepIndex / (interviewSteps.length - 1)) * 100);

  if (isOnboardingCompleted) {
    return (
      <div className="space-y-8 text-left max-w-3xl mx-auto">
        <div className="flex flex-col items-center text-center space-y-3 mb-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full animate-bounce">
            <CheckCircle className="h-6 w-6" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">Onboarding Profile Generated!</h1>
          <p className="text-sm text-muted-foreground max-w-md">
            Our career engine analyzed your conversation to build a dynamic mapping of target goals and skills.
          </p>
        </div>

        {/* Profile Card Summary Screen */}
        <Card className="border border-indigo-500/20 bg-slate-950/40 shadow-xl overflow-hidden relative">
          <div className="absolute top-0 inset-x-0 h-[1.5px] bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent" />
          <CardHeader className="bg-muted/30 border-b border-border p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center space-x-3.5">
                <div className="h-12 w-12 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center font-bold text-lg border border-indigo-500/20">
                  <BrainCircuit className="h-6 w-6" />
                </div>
                <div className="text-left">
                  <h2 className="text-lg font-bold text-slate-100">AI Profile Summary</h2>
                  <p className="text-xs text-muted-foreground font-medium capitalize">Persona Type: {responses.career_goal || "Frontend Developer"}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={() => (window.location.href = "/student")} className="cursor-pointer">
                  Sync to Dashboard
                </Button>
                <Button size="sm" variant="outline" onClick={() => (window.location.href = "/profile")} className="cursor-pointer">
                  Edit Profile
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6 space-y-6">
            {/* Summary */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Professional Overview</span>
              <p className="text-xs text-slate-300 leading-relaxed font-medium">
                {responses.intro || "Dedicated junior computer science major aiming to build slick frontend dashboards and systems."}
              </p>
            </div>

            {/* Grid details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Academic Background</span>
                  <p className="text-xs font-semibold text-slate-200">{responses.education || "BS in CS, Stanford"}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Languages & Core Stack</span>
                  <p className="text-xs font-semibold text-slate-200">{responses.languages || "TypeScript, JavaScript"} / {responses.frameworks || "React, Next.js"}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Core Projects</span>
                  <p className="text-xs font-semibold text-slate-200">{responses.projects || "AI SaaS Application generator."}</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Target Goals</span>
                  <p className="text-xs font-semibold text-slate-200 flex items-center gap-1.5"><Briefcase className="h-3.5 w-3.5" /> {responses.career_goal || "Frontend Developer"} at {responses.pref_company || "Stripe"}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Preferences</span>
                  <p className="text-xs font-semibold text-slate-200 flex items-center gap-1.5"><MapPin className="h-3.5 w-3.5" /> {responses.pref_location || "Remote"} • Expecting {responses.expected_salary || "$90k - $120k"}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Domain / Industry Preference</span>
                  <p className="text-xs font-semibold text-slate-200">{responses.pref_domain || "DevTools, Fintech"}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ATS Warning Callout */}
        <div className="p-4 border border-indigo-500/10 bg-indigo-500/5 rounded-xl flex gap-3.5">
          <FileCheck className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
          <div className="text-left text-xs leading-relaxed">
            <p className="font-semibold text-slate-200">Recommended Next: ATS Resume Alignment</p>
            <p className="text-muted-foreground mt-0.5">
              Based on your target of joining **{responses.pref_company || "Stripe"}** as a **{responses.career_goal || "Frontend Engineer"}**, we recommend uploading your resume to our ATS Analyzer to check if you have the necessary keywords.
            </p>
            <Button size="sm" variant="link" onClick={() => (window.location.href = "/resume")} className="p-0 h-auto text-xs text-primary font-bold hover:underline mt-1.5">
              Go to Resume Center <ChevronRight className="inline h-3 w-3" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] text-left max-w-3xl mx-auto">
      {/* Onboarding Header */}
      <div className="mb-6 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h1 className="text-lg font-bold">Career Discovery Chat</h1>
          </div>
          <span className="text-xs text-muted-foreground font-medium">Onboarding On Track: {progressPercentage}%</span>
        </div>
        <Progress value={progressPercentage} indicatorClassName="bg-primary" className="h-1.5" />
      </div>

      {/* Chat Thread Area */}
      <div className="flex-1 overflow-y-auto border border-border bg-card/40 dark:bg-slate-950/20 rounded-xl p-4 space-y-4 mb-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex gap-3 max-w-[85%] text-xs leading-relaxed",
              msg.sender === "ai" ? "self-start text-left" : "self-end flex-row-reverse text-left"
            )}
            style={{ marginLeft: msg.sender === "user" ? "auto" : "0" }}
          >
            {/* Avatar */}
            <div
              className={cn(
                "h-8 w-8 rounded-full flex items-center justify-center font-bold border shrink-0",
                msg.sender === "ai"
                  ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/20"
                  : "bg-primary text-white border-primary"
              )}
            >
              {msg.sender === "ai" ? <Sparkles className="h-4 w-4" /> : <User className="h-4 w-4" />}
            </div>

            {/* Bubble */}
            <div
              className={cn(
                "rounded-xl p-3 border",
                msg.sender === "ai"
                  ? "bg-muted text-foreground border-muted/50 rounded-tl-none"
                  : "bg-primary/10 text-slate-100 border-primary/25 rounded-tr-none"
              )}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Typing Dots */}
        {isTyping && (
          <div className="flex gap-3 text-xs leading-relaxed self-start">
            <div className="h-8 w-8 rounded-full flex items-center justify-center font-bold border bg-indigo-500/10 text-indigo-400 border-indigo-500/20 shrink-0">
              <Sparkles className="h-4 w-4" />
            </div>
            <div className="bg-muted border border-muted/50 text-foreground rounded-xl rounded-tl-none p-3.5 flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Suggested Quick Replies Panel */}
      {!isTyping && interviewSteps[stepIndex] && (
        <div className="mb-4">
          <div className="flex flex-wrap gap-2 justify-start">
            {interviewSteps[stepIndex].suggestions.map((option) => (
              <button
                key={option}
                onClick={() => handleNextStep(option)}
                className="px-3 py-1.5 text-[11px] rounded-full border border-muted bg-muted/40 hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-all cursor-pointer font-medium leading-normal"
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input bar */}
      <div className="flex items-center gap-2 border border-border rounded-xl bg-card p-2 overflow-hidden focus-within:ring-1 focus-within:ring-ring dark:bg-slate-950/30">
        <input
          type="text"
          placeholder="Type your response here..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-transparent px-3 py-2 text-xs outline-hidden placeholder:text-muted-foreground"
        />
        <Button
          onClick={() => handleNextStep(input)}
          disabled={!input.trim()}
          size="sm"
          className="h-8 cursor-pointer"
        >
          <Send className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
