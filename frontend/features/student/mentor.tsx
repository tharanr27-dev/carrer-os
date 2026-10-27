"use client";

import React from "react";
import { Bot, Plus } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingBlock } from "@/components/ui/feedback";
import { MentorComposer, MentorError, MentorSetupNotice, MentorSuggestions } from "@/features/mentor/components/mentor-chat-parts";
import { useMentorStore } from "@/store/useMentorStore";
import { cn } from "@/lib/utils";

export function MentorWorkspaceView() {
  const { messages, isTyping, isLoadingHistory, aiAvailable, suggestedPrompts, loadHistory, sendMessage, newConversation } =
    useMentorStore();
  const endRef = React.useRef<HTMLDivElement>(null);

  const setWidgetHidden = useMentorStore((s) => s.setWidgetHidden);

  // The floating widget shares this conversation and would overlap the composer, so hide it here.
  React.useEffect(() => {
    setWidgetHidden(true);
    return () => setWidgetHidden(false);
  }, [setWidgetHidden]);

  React.useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  React.useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  return (
    <div className="space-y-6 text-left">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Bot className="h-7 w-7 text-primary" /> AI Career Mentor
          </h1>
          <p className="text-sm text-muted-foreground">Your conversations are saved to your account. Answers come from an AI model and can be wrong; double-check important facts.</p>
        </div>
        <Button variant="outline" onClick={() => void newConversation()} disabled={isTyping} className="gap-1">
          <Plus className="h-4 w-4" /> New conversation
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Conversation</CardTitle>
          <CardDescription className="text-xs">Ask about skills, your resume, interviews, or jobs.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div role="log" aria-live="polite" aria-label="Conversation with the AI Mentor" className="h-[420px] overflow-y-auto flex flex-col gap-3 rounded-xl bg-muted/30 p-4">
            {isLoadingHistory && <LoadingBlock label="Loading conversation…" />}
            {!isLoadingHistory && messages.length === 0 && (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">Ask me anything about programming, interviews, resumes or your career. Try one of these, or type your own:</p>
                <div className="flex flex-wrap gap-2">
                  {suggestedPrompts.map((p) => (
                    <Button key={p} size="sm" variant="outline" onClick={() => void sendMessage(p)} disabled={isTyping || aiAvailable === false}>
                      {p}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            {messages.map((m) => (
              <div
                key={m.id}
                className={cn(
                  "max-w-[80%] rounded-xl p-3 text-sm whitespace-pre-wrap break-words",
                  m.sender === "ai" ? "self-start bg-card border border-border" : "self-end bg-primary text-primary-foreground"
                )}
              >
                {m.content}
              </div>
            ))}
            {isTyping && <p role="status" className="text-xs text-muted-foreground self-start">Mentor is thinking…</p>}
            <div ref={endRef} />
          </div>
          <MentorSetupNotice />
          <MentorError />
          <MentorComposer />
          <MentorSuggestions />
        </CardContent>
      </Card>
    </div>
  );
}
