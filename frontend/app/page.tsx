"use client";

import React from "react";
import { Sparkles, FileCheck, BrainCircuit, ChevronRight, Target, Sun, Moon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "@/contexts/ThemeContext";

export default function LandingPage() {
  const { resolvedTheme, toggleTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <div className="relative min-h-screen w-full flex flex-col justify-between overflow-x-hidden bg-background text-foreground transition-colors duration-500">
      {/* Premium background overlays — adapt to theme */}
      <div
        className="absolute inset-0 transition-opacity duration-700"
        style={{
          background: isDark
            ? "radial-gradient(ellipse 80% 80% at 50% -20%, rgba(120,119,198,0.15), rgba(255,255,255,0))"
            : "radial-gradient(ellipse 80% 80% at 50% -20%, rgba(120,119,198,0.08), rgba(255,255,255,0))",
        }}
      />
      <div
        className="absolute inset-0 transition-opacity duration-700"
        style={{
          backgroundImage: isDark
            ? "linear-gradient(rgba(255,255,255,0.005) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.005) 1px, transparent 1px)"
            : "linear-gradient(rgba(0,0,0,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0,0,0,0.02) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
          maskImage: "radial-gradient(ellipse 60% 50% at 50% 50%, #000 70%, transparent 100%)",
        }}
      />

      {/* Floating Animated Gradient Blobs */}
      <div
        className={`absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full blur-[80px] animate-pulse-slow transition-colors duration-700 ${
          isDark ? "bg-indigo-500/10" : "bg-indigo-400/15"
        }`}
      />
      <div
        className={`absolute bottom-1/3 right-1/4 translate-x-1/2 translate-y-1/2 w-[450px] h-[450px] rounded-full blur-[100px] animate-pulse-slow transition-colors duration-700 ${
          isDark ? "bg-violet-500/10" : "bg-violet-400/12"
        }`}
        style={{ animationDelay: "2s" }}
      />

      {/* Header bar */}
      <header className="w-full max-w-7xl mx-auto px-6 h-20 flex items-center justify-between z-10 relative">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-gradient-to-tr from-indigo-500 to-violet-500 rounded-lg text-white shadow-lg shadow-indigo-500/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <span className="font-bold text-lg bg-gradient-to-r from-indigo-500 to-violet-500 bg-clip-text text-transparent">
            CareerOS AI
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className={`relative p-2.5 rounded-xl border transition-all duration-300 cursor-pointer group ${
              isDark
                ? "border-slate-700/60 bg-slate-900/60 hover:bg-slate-800/80 hover:border-slate-600"
                : "border-slate-200 bg-white/80 hover:bg-slate-50 hover:border-slate-300 shadow-sm"
            }`}
            aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
          >
            <AnimatePresence mode="wait" initial={false}>
              {isDark ? (
                <motion.div
                  key="moon"
                  initial={{ rotate: -90, scale: 0, opacity: 0 }}
                  animate={{ rotate: 0, scale: 1, opacity: 1 }}
                  exit={{ rotate: 90, scale: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: "easeInOut" }}
                >
                  <Moon className="h-4.5 w-4.5 text-indigo-400" />
                </motion.div>
              ) : (
                <motion.div
                  key="sun"
                  initial={{ rotate: 90, scale: 0, opacity: 0 }}
                  animate={{ rotate: 0, scale: 1, opacity: 1 }}
                  exit={{ rotate: -90, scale: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: "easeInOut" }}
                >
                  <Sun className="h-4.5 w-4.5 text-amber-500" />
                </motion.div>
              )}
            </AnimatePresence>
            {/* Glow effect on hover */}
            <div
              className={`absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10 ${
                isDark
                  ? "shadow-[0_0_15px_rgba(99,102,241,0.2)]"
                  : "shadow-[0_0_15px_rgba(245,158,11,0.15)]"
              }`}
            />
          </button>

          <a href="/login">
            <button
              className={`px-4 py-2 text-xs font-semibold rounded-lg border transition-all cursor-pointer ${
                isDark
                  ? "border-slate-800 bg-slate-950/40 hover:bg-slate-900/50 hover:text-white text-slate-300"
                  : "border-slate-200 bg-white/80 hover:bg-slate-50 text-slate-700 hover:text-slate-900 shadow-sm"
              }`}
            >
              Sign In
            </button>
          </a>
        </div>
      </header>

      {/* Hero section */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 max-w-5xl mx-auto z-10 relative py-16">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-6"
        >
          {/* Badge */}
          <div
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold mx-auto transition-colors duration-300 ${
              isDark
                ? "bg-indigo-500/10 border border-indigo-500/20 text-indigo-400"
                : "bg-indigo-50 border border-indigo-200 text-indigo-600"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" /> Next-Generation Career Steering
          </div>

          {/* Heading */}
          <h1
            className={`text-4xl sm:text-6xl font-black tracking-tight leading-[1.1] max-w-3xl mx-auto transition-colors duration-300 ${
              isDark ? "text-white" : "text-slate-900"
            }`}
          >
            Your Complete AI{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-500 bg-clip-text text-transparent">
              Career Command Center
            </span>
          </h1>

          {/* Subheading */}
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl mx-auto leading-relaxed transition-colors duration-300">
            Verify resume ATS matches, chart skill roadmaps, clear mock screens, and sync credentials with recruiters. Production-ready, role-based, and AI-driven.
          </p>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <a href="/student" className="w-full sm:w-auto">
              <button className="w-full sm:w-auto inline-flex items-center justify-center h-12 px-6 rounded-xl bg-primary text-primary-foreground font-semibold shadow-xl shadow-indigo-500/10 hover:bg-primary/90 transition-all cursor-pointer">
                Enter Student Dashboard <ChevronRight className="ml-1 h-4 w-4" />
              </button>
            </a>
            <a href="/login" className="w-full sm:w-auto">
              <button
                className={`w-full sm:w-auto inline-flex items-center justify-center h-12 px-6 rounded-xl border font-semibold transition-all cursor-pointer ${
                  isDark
                    ? "border-slate-800 bg-slate-950/40 hover:bg-slate-900/50 text-slate-200"
                    : "border-slate-200 bg-white hover:bg-slate-50 text-slate-700 shadow-sm"
                }`}
              >
                Sign In Options
              </button>
            </a>
          </div>
        </motion.div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 w-full text-left">
          {/* Card 1 — ATS Resume Scanner */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className={`p-6 border backdrop-blur-md rounded-2xl space-y-3 relative overflow-hidden transition-all duration-300 group hover:scale-[1.02] ${
              isDark
                ? "border-slate-800/60 bg-slate-950/30 hover:border-indigo-500/30"
                : "border-slate-200 bg-white/70 shadow-sm hover:shadow-md hover:border-indigo-300"
            }`}
          >
            <div
              className={`p-2.5 rounded-xl w-fit transition-colors duration-300 ${
                isDark
                  ? "bg-indigo-500/10 border border-indigo-500/20 text-indigo-400"
                  : "bg-indigo-50 border border-indigo-200 text-indigo-600"
              }`}
            >
              <FileCheck className="h-5 w-5" />
            </div>
            <h3
              className={`text-sm font-bold transition-colors duration-300 ${
                isDark ? "text-slate-100" : "text-slate-800"
              }`}
            >
              ATS Resume Scanner
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed transition-colors duration-300">
              Scan resume versions, identify missing recruiter keyword nodes, and get quantifiable metrics.
            </p>
          </motion.div>

          {/* Card 2 — Conversational Onboarding */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.35 }}
            className={`p-6 border backdrop-blur-md rounded-2xl space-y-3 relative overflow-hidden transition-all duration-300 group hover:scale-[1.02] ${
              isDark
                ? "border-slate-800/60 bg-slate-950/30 hover:border-violet-500/30"
                : "border-slate-200 bg-white/70 shadow-sm hover:shadow-md hover:border-violet-300"
            }`}
          >
            <div
              className={`p-2.5 rounded-xl w-fit transition-colors duration-300 ${
                isDark
                  ? "bg-violet-500/10 border border-violet-500/20 text-violet-400"
                  : "bg-violet-50 border border-violet-200 text-violet-600"
              }`}
            >
              <BrainCircuit className="h-5 w-5" />
            </div>
            <h3
              className={`text-sm font-bold transition-colors duration-300 ${
                isDark ? "text-slate-100" : "text-slate-800"
              }`}
            >
              Conversational Onboarding
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed transition-colors duration-300">
              Complete an interactive chat interview with AI to map targeted domains, salaries, and roadmaps.
            </p>
          </motion.div>

          {/* Card 3 — Role-Based Gateways */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className={`p-6 border backdrop-blur-md rounded-2xl space-y-3 relative overflow-hidden transition-all duration-300 group hover:scale-[1.02] ${
              isDark
                ? "border-slate-800/60 bg-slate-950/30 hover:border-sky-500/30"
                : "border-slate-200 bg-white/70 shadow-sm hover:shadow-md hover:border-sky-300"
            }`}
          >
            <div
              className={`p-2.5 rounded-xl w-fit transition-colors duration-300 ${
                isDark
                  ? "bg-sky-500/10 border border-sky-500/20 text-sky-400"
                  : "bg-sky-50 border border-sky-200 text-sky-600"
              }`}
            >
              <Target className="h-5 w-5" />
            </div>
            <h3
              className={`text-sm font-bold transition-colors duration-300 ${
                isDark ? "text-slate-100" : "text-slate-800"
              }`}
            >
              Role-Based Gateways
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed transition-colors duration-300">
              Tailored workspaces for Candidates, Talent leads, Placement Directors, and System Operators.
            </p>
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <footer
        className={`w-full border-t py-6 text-center text-[10px] text-muted-foreground z-10 relative transition-colors duration-300 ${
          isDark ? "border-slate-900/50" : "border-slate-200"
        }`}
      >
        <p>© 2026 CareerOS AI. Built using Next.js 15, React 19, and Tailwind CSS v4.</p>
      </footer>
    </div>
  );
}
