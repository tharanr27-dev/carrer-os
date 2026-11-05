"use client";

import * as React from "react";
import { RotateCcw, Send } from "lucide-react";
import { useMentorStore } from "@/store/useMentorStore";
import { cn } from "@/lib/utils";

/** Shown instead of a pretend conversation when the server has no AI provider configured. */
export function MentorSetupNotice({ compact = false }: { compact?: boolean }) {
  const aiAvailable = useMentorStore((s) => s.aiAvailable);
  if (aiAvailable !== false) return null;
  return (
    <div
      role="status"
      data-testid="mentor-setup-notice"
      className={cn("rounded-lg border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300", compact ? "p-2 text-[11px]" : "p-3 text-sm")}
    >
      <p className="font-semibold">AI Mentor is not set up on this server yet.</p>
      <p className="mt-1">
        I can&apos;t answer questions until an administrator sets <code>GROQ_API_KEY</code> in the backend environment and
        restarts the server. Your suggested next steps below still work.
      </p>
    </div>
  );
}

/** Error banner with a Retry button when the last message could not be answered. */
export function MentorError({ compact = false }: { compact?: boolean }) {
  const error = useMentorStore((s) => s.error);
  const hasFailed = useMentorStore((s) => s.messages.some((m) => m.failed));
  const isTyping = useMentorStore((s) => s.isTyping);
  const retryLast = useMentorStore((s) => s.retryLast);
  if (!error) return null;
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start justify-between gap-2 rounded-lg border border-destructive/20 bg-destructive/10 text-destructive",
        compact ? "p-2 text-[11px]" : "p-3 text-sm"
      )}
    >
      <span>{error}</span>
      {hasFailed && (
        <button
          type="button"
          onClick={() => void retryLast()}
          disabled={isTyping}
          className="inline-flex shrink-0 items-center gap-1 font-semibold underline-offset-2 hover:underline disabled:opacity-50"
        >
          <RotateCcw className="h-3 w-3" aria-hidden /> Retry
        </button>
      )}
    </div>
  );
}

/** Next steps from the user's saved activity. Deliberately separate from the chat answers. */
export function MentorSuggestions({ compact = false }: { compact?: boolean }) {
  const suggestions = useMentorStore((s) => s.suggestions);
  if (suggestions.length === 0) return null;
  return (
    <section aria-label="Suggested next steps from your saved activity" data-testid="mentor-suggestions" className="space-y-1">
      <h4 className={cn("font-semibold uppercase tracking-wider text-muted-foreground", compact ? "text-[10px]" : "text-xs")}>
        Suggested next steps (from your saved activity)
      </h4>
      <ul className={cn("space-y-1", compact ? "text-[11px]" : "text-sm")}>
        {suggestions.slice(0, compact ? 2 : 4).map((s) => (
          <li key={s.title} className="rounded-md border border-border bg-muted/40 px-2 py-1">
            <span className="font-medium">{s.title}</span>
            <span className="text-muted-foreground"> — {s.reason}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Multi-line composer: Enter sends, Shift+Enter inserts a new line. */
export function MentorComposer({ compact = false }: { compact?: boolean }) {
  const isTyping = useMentorStore((s) => s.isTyping);
  const aiAvailable = useMentorStore((s) => s.aiAvailable);
  const sendMessage = useMentorStore((s) => s.sendMessage);
  const [input, setInput] = React.useState("");
  const blocked = aiAvailable === false;

  const submit = async () => {
    const text = input.trim();
    if (!text || isTyping || blocked) return;
    setInput("");
    await sendMessage(text);
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void submit();
      }}
      className="flex items-end gap-2"
    >
      <textarea
        aria-label="Message the AI Mentor"
        rows={compact ? 1 : 2}
        maxLength={4000}
        value={input}
        disabled={blocked}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            void submit();
          }
        }}
        placeholder={blocked ? "AI Mentor is not set up yet" : "Ask a question… (Enter to send, Shift+Enter for a new line)"}
        className={cn(
          "min-h-9 max-h-32 flex-1 resize-none rounded-xl border border-border bg-card px-3 py-2 outline-hidden placeholder:text-muted-foreground focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-60",
          compact ? "text-xs" : "text-sm"
        )}
      />
      <button
        type="submit"
        disabled={!input.trim() || isTyping || blocked}
        aria-label="Send message"
        className="rounded-xl bg-primary p-2.5 text-primary-foreground disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Send className="h-4 w-4" aria-hidden />
      </button>
    </form>
  );
}
