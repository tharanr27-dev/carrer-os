"use client";

import * as React from "react";
import { useMentorStore, ChatMessage } from "@/store/useMentorStore";
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Mic,
  MicOff,
  Paperclip,
  Trash2,
  Minimize2,
  CornerDownLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

export function FloatingMentor() {
  const {
    isOpen,
    messages,
    isTyping,
    suggestedPrompts,
    toggleOpen,
    sendMessage,
    clearHistory,
  } = useMentorStore();

  const [input, setInput] = React.useState("");
  const [isListening, setIsListening] = React.useState(false);
  const [attachedFiles, setAttachedFiles] = React.useState<{ name: string; size: string; type: string }[]>([]);
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Auto scroll to bottom
  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() && attachedFiles.length === 0) return;

    const messageText = input;
    const attachments = attachedFiles;
    
    setInput("");
    setAttachedFiles([]);
    
    await sendMessage(messageText, attachments.length > 0 ? attachments : undefined);
  };

  const handlePromptClick = async (prompt: string) => {
    await sendMessage(prompt);
  };

  const handleFileAttach = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
      setAttachedFiles([
        ...attachedFiles,
        {
          name: file.name,
          size: `${sizeMb} MB`,
          type: file.type || "application/octet-stream",
        },
      ]);
    }
  };

  const toggleMic = () => {
    setIsListening(!isListening);
    if (!isListening) {
      // Mock typing speech text
      setTimeout(() => {
        setInput("How do I clear technical screen interviews?");
        setIsListening(false);
      }, 3000);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Pane */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 50 }}
            className="w-96 h-[500px] border border-border bg-card/95 backdrop-blur-md rounded-2xl shadow-2xl flex flex-col overflow-hidden mb-4 glass dark:bg-slate-950/95 dark:border-slate-900"
          >
            {/* Header */}
            <div className="p-4 border-b border-border bg-muted/50 dark:bg-slate-900/50 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 bg-gradient-to-tr from-indigo-500 to-violet-500 rounded-lg text-white">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold leading-none">CareerOS AI Mentor</h3>
                  <span className="text-[10px] text-muted-foreground flex items-center gap-1 mt-0.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" /> Always Active
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={clearHistory}
                  title="Clear chat history"
                  className="p-1 rounded-md text-muted-foreground hover:bg-muted hover:text-destructive transition-colors cursor-pointer"
                >
                  <Trash2 className="h-3.5 w-3.5" />
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

            {/* Chat History Panel */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
                  <div className="font-semibold text-[10px] mb-1 opacity-70">
                    {msg.sender === "ai" ? "AI Mentor" : "You"}
                  </div>
                  <div>{msg.content}</div>

                  {/* Render attachments */}
                  {msg.attachments && msg.attachments.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {msg.attachments.map((file) => (
                        <div
                          key={file.name}
                          className="flex items-center gap-1.5 p-1 bg-black/10 dark:bg-black/20 rounded-md text-[10px] border border-black/10"
                        >
                          <Paperclip className="h-3 w-3 text-indigo-400" />
                          <span className="truncate max-w-[120px] font-medium">{file.name}</span>
                          <span className="opacity-60 text-[9px]">({file.size})</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {/* Typing Dot Animation */}
              {isTyping && (
                <div className="bg-muted text-foreground self-start rounded-lg rounded-tl-none p-3 max-w-[80%] flex items-center space-x-1.5 border border-muted/50 dark:bg-slate-900/40">
                  <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              )}
              <div ref={scrollRef} />
            </div>

            {/* Suggested prompts footer wrapper */}
            {messages.length === 1 && (
              <div className="p-3 border-t border-border bg-card space-y-2">
                <span className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">
                  Suggested Prompts
                </span>
                <div className="flex flex-col gap-1.5 max-h-24 overflow-y-auto">
                  {suggestedPrompts.map((p) => (
                    <button
                      key={p}
                      onClick={() => handlePromptClick(p)}
                      className="text-left text-[10px] px-2.5 py-1.5 rounded-md border border-muted bg-muted/40 hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-all cursor-pointer leading-tight truncate"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input Form */}
            <form onSubmit={handleSend} className="p-3 border-t border-border bg-muted/40 dark:bg-slate-950/20">
              {/* Attached file previews */}
              {attachedFiles.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {attachedFiles.map((file, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-1 px-1.5 py-0.5 bg-indigo-500/10 border border-indigo-500/30 rounded-md text-[10px] text-indigo-400"
                    >
                      <Paperclip className="h-2.5 w-2.5" />
                      <span className="truncate max-w-[100px]">{file.name}</span>
                      <button
                        type="button"
                        onClick={() => setAttachedFiles(attachedFiles.filter((_, i) => i !== idx))}
                        className="hover:text-destructive ml-1"
                      >
                        <X className="h-2.5 w-2.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex items-center border border-border rounded-xl bg-card overflow-hidden focus-within:ring-1 focus-within:ring-ring dark:bg-slate-950/50">
                <input
                  type="text"
                  placeholder={isListening ? "Listening..." : "Message CareerOS AI..."}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={isListening}
                  className="flex-1 bg-transparent px-3 py-2 text-xs outline-hidden placeholder:text-muted-foreground"
                />

                {/* Voice/Mic button */}
                <button
                  type="button"
                  onClick={toggleMic}
                  className={cn(
                    "p-1.5 rounded-md text-muted-foreground hover:text-foreground transition-all cursor-pointer",
                    isListening && "text-red-500 animate-pulse bg-red-500/10"
                  )}
                  title="Speech-to-text"
                >
                  {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
                </button>

                {/* Attachment button */}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-1.5 rounded-md text-muted-foreground hover:text-foreground transition-all cursor-pointer"
                  title="Attach file"
                >
                  <Paperclip className="h-4 w-4" />
                </button>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileAttach}
                  className="hidden"
                  accept=".pdf,.docx,.doc,.txt"
                />

                {/* Send button */}
                <button
                  type="submit"
                  disabled={!input.trim() && attachedFiles.length === 0}
                  className="p-2 bg-primary text-white disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Action Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={toggleOpen}
        className="p-4 bg-gradient-to-tr from-indigo-500 to-violet-500 text-white rounded-full shadow-xl hover:shadow-indigo-500/20 border-0 flex items-center justify-center cursor-pointer relative group overflow-hidden"
        style={{ width: "56px", height: "56px" }}
      >
        {/* Glow pulsing ring overlay */}
        <span className="absolute inset-0 bg-white/20 scale-100 group-hover:scale-150 transition-transform duration-500" />
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.div
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <X className="h-6 w-6" />
            </motion.div>
          ) : (
            <motion.div
              key="message"
              initial={{ rotate: 90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: -90, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="relative"
            >
              <MessageSquare className="h-6 w-6" />
              {/* Sparkles highlight inside button */}
              <Sparkles className="h-3.5 w-3.5 absolute -top-1.5 -right-1.5 text-indigo-200 animate-bounce" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
