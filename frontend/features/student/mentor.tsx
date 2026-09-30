"use client";

import React from "react";
import { Bot, Plus, Send } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { useMentorStore } from "@/store/useMentorStore";
import { cn } from "@/lib/utils";

export function MentorWorkspaceView() {
  const { messages, isTyping, isLoadingHistory, error, suggestedPrompts, loadHistory, sendMessage, newConversation } =
    useMentorStore();
  const [input, setInput] = React.useState("");
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

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput("");
    await sendMessage(text);
  };

  return (
    <div className="space-y-6 text-left">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Bot className="h-7 w-7 text-primary" /> AI Career Mentor
          </h1>
          <p className="text-sm text-muted-foreground">Your conversations are saved to your account.</p>
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
          <div className="h-[420px] overflow-y-auto flex flex-col gap-3 rounded-xl bg-muted/30 p-4">
            {isLoadingHistory && <LoadingBlock label="Loading conversation…" />}
            {!isLoadingHistory && messages.length === 0 && (
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">Start the conversation with one of these, or type your own:</p>
                <div className="flex flex-wrap gap-2">
                  {suggestedPrompts.map((p) => (
                    <Button key={p} size="sm" variant="outline" onClick={() => void sendMessage(p)} disabled={isTyping}>
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
                  "max-w-[80%] rounded-xl p-3 text-sm whitespace-pre-wrap",
                  m.sender === "ai" ? "self-start bg-card border border-border" : "self-end bg-primary text-primary-foreground"
                )}
              >
                {m.content}
              </div>
            ))}
            {isTyping && <p className="text-xs text-muted-foreground self-start">Mentor is thinking…</p>}
            <div ref={endRef} />
          </div>
          <ErrorBanner error={error} />
          <form onSubmit={submit} className="flex items-center gap-2">
            <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask your mentor…" />
            <Button type="submit" size="icon" disabled={!input.trim() || isTyping} aria-label="Send message">
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
