"use client";

import * as React from "react";
import { useMentorStore } from "@/store/useMentorStore";
import { MessageSquare, X, Sparkles, Plus, Minimize2 } from "lucide-react";
import { MentorComposer, MentorError, MentorSetupNotice, MentorSuggestions } from "./mentor-chat-parts";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

export function FloatingMentor() {
  const {
    isOpen,
    widgetHidden,
    messages,
    isTyping,
    isLoadingHistory,
    aiAvailable,
    suggestedPrompts,
    toggleOpen,
    loadHistory,
    sendMessage,
    newConversation,
  } = useMentorStore();

  const scrollRef = React.useRef<HTMLDivElement>(null);

  // Restore the conversation the first time the panel opens.
  React.useEffect(() => {
    if (isOpen) void loadHistory();
  }, [isOpen, loadHistory]);

  React.useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  if (widgetHidden) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 50 }}
            className="w-96 h-[500px] border border-border bg-card/95 backdrop-blur-md rounded-2xl shadow-2xl flex flex-col overflow-hidden mb-4 glass dark:bg-slate-950/95 dark:border-slate-900"
          >
            <div className="p-4 border-b border-border bg-muted/50 dark:bg-slate-900/50 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 bg-gradient-to-tr from-indigo-500 to-violet-500 rounded-lg text-white">
                  <Sparkles className="h-4 w-4" />
                </div>
                <h3 className="text-sm font-semibold leading-none">CareerOS AI Mentor</h3>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => void newConversation()}
                  title="Start a new conversation"
                  className="p-1 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
                >
                  <Plus className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={toggleOpen}
                  title="Minimize"
                  className="p-1 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
                >
                  <Minimize2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <div role="log" aria-live="polite" aria-label="Conversation with the AI Mentor" className="flex-1 overflow-y-auto p-4 space-y-4 flex flex-col">
              {isLoadingHistory && <p className="text-xs text-muted-foreground">Loading conversation…</p>}
              {!isLoadingHistory && messages.length === 0 && (
                <p className="text-xs text-muted-foreground">
                  Hi, I&apos;m your CareerOS AI Mentor. Ask me about programming, interviews, your resume, or your career path.
                </p>
              )}
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex flex-col max-w-[80%] rounded-lg p-3 text-xs leading-relaxed",
                    msg.sender === "ai"
                      ? "bg-muted text-foreground self-start rounded-tl-none border border-muted/50 dark:bg-slate-900/40 dark:border-slate-800/80"
                      : "bg-primary text-primary-foreground self-end rounded-tr-none"
                  )}
                >
                  <div className="font-semibold text-[10px] mb-1 opacity-70">{msg.sender === "ai" ? "AI Mentor" : "You"}</div>
                  <div className="whitespace-pre-wrap break-words">{msg.content}</div>
                  {msg.failed && <div className="mt-1 text-[10px] text-destructive">Not answered</div>}
                </div>
              ))}

              {isTyping && (
                <div className="bg-muted text-foreground self-start rounded-lg rounded-tl-none p-3 max-w-[80%] flex items-center space-x-1.5 border border-muted/50 dark:bg-slate-900/40">
                  <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              )}
              <MentorSetupNotice compact />
              <MentorError compact />
              <div ref={scrollRef} />
            </div>

            {messages.length === 0 && !isLoadingHistory && (
              <div className="p-3 border-t border-border bg-card space-y-2">
                <MentorSuggestions compact />
                <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">Example questions</span>
                <div className="flex flex-col gap-1.5 max-h-24 overflow-y-auto">
                  {suggestedPrompts.map((p) => (
                    <button
                      key={p}
                      onClick={() => void sendMessage(p)}
                      disabled={aiAvailable === false || isTyping}
                      className="text-left text-[10px] px-2.5 py-1.5 rounded-md border border-muted bg-muted/40 hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-all cursor-pointer leading-tight truncate"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="p-3 border-t border-border bg-muted/40 dark:bg-slate-950/20">
              <MentorComposer compact />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={toggleOpen}
        aria-label={isOpen ? "Close mentor" : "Open mentor"}
        className="p-4 bg-gradient-to-tr from-indigo-500 to-violet-500 text-white rounded-full shadow-xl hover:shadow-indigo-500/20 border-0 flex items-center justify-center cursor-pointer relative group overflow-hidden"
        style={{ width: "56px", height: "56px" }}
      >
        <span className="absolute inset-0 bg-white/20 scale-100 group-hover:scale-150 transition-transform duration-500" />
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.div key="close" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.2 }}>
              <X className="h-6 w-6" />
            </motion.div>
          ) : (
            <motion.div key="message" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.2 }} className="relative">
              <MessageSquare className="h-6 w-6" />
              <Sparkles className="h-3.5 w-3.5 absolute -top-1.5 -right-1.5 text-indigo-200 animate-bounce" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
