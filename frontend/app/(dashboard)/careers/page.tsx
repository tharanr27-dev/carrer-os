"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  TrendingUp,
  MapPin,
  Clock,
  ArrowRight,
  Building,
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { usePathname, useRouter } from "next/navigation";

const timelineMilestones = [
  {
    step: "01",
    role: "Junior Front-End Developer",
    timeline: "Years 0–1 (Current)",
    status: "Completed",
    skills: ["React & Next.js", "TypeScript Base", "Tailwind CSS"],
    description: "Focus on UI fidelity, responsive web layouts, and state management logic.",
  },
  {
    step: "02",
    role: "Full-Stack Software Engineer",
    timeline: "Years 1–3 (Target)",
    status: "Active Preparation",
    skills: ["Next.js 15 Server Actions", "Node.js API Architecture", "PostgreSQL/Redis"],
    description: "Take ownership of full-stack data routes, backend optimization, caching, and cloud deployments.",
  },
  {
    step: "03",
    role: "Lead Frontend Architect",
    timeline: "Years 3–5 (Long-Term)",
    status: "Future Goal",
    skills: ["System Design & Caching", "CI/CD & DevOps Architectures", "OAuth & Security Specs"],
    description: "Lead engineering projects, define structural layout standards, implement optimization scripts, and manage core platforms.",
  },
];

const targetSkills = [
  { name: "React 19 & Next.js 15", current: 80, target: 90, status: "Close Gap" },
  { name: "TypeScript", current: 75, target: 85, status: "Close Gap" },
  { name: "System Design", current: 40, target: 80, status: "Critical Gap" },
  { name: "Data Structures", current: 65, target: 85, status: "Close Gap" },
  { name: "CI/CD & Cloud Pipelines", current: 30, target: 70, status: "Critical Gap" },
];

const learningTracks = [
  {
    title: "Advanced Next.js Architecture",
    provider: "CareerOS Academy",
    duration: "6 hours",
    difficulty: "Advanced",
    skillsMatched: ["Server Actions", "Caching Router", "Streaming UI"],
  },
  {
    title: "System Design Fundamentals for Frontend Leads",
    provider: "Educative.io Partner",
    duration: "12 hours",
    difficulty: "Intermediate",
    skillsMatched: ["CDNs", "Client-Side Caching", "API Gateway Patterns"],
  },
  {
    title: "Docker & Kubernetes Deployments",
    provider: "AWS Developer Hub",
    duration: "8 hours",
    difficulty: "Advanced",
    skillsMatched: ["CI/CD", "AWS ECS", "Containerization"],
  },
];

export default function CareerDashboard() {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    if (pathname !== "/workspace") {
      router.replace("/workspace?tab=careers");
    }
  }, [pathname, router]);

  return (
    <div className="space-y-8 text-left">
      {/* Target Path Header Card */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 border border-indigo-500/20 bg-slate-950/40 rounded-2xl relative overflow-hidden"
      >
        <div className="absolute right-0 top-0 w-64 h-64 bg-violet-500/10 rounded-full blur-[80px]" />
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative z-10">
          <div className="space-y-1.5">
            <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Active Career Pathway</span>
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
              Lead Frontend Architect <Sparkles className="h-5 w-5 text-indigo-400 animate-pulse" />
            </h1>
            <p className="text-xs text-muted-foreground max-w-xl leading-relaxed">
              Based on your educational background and project history, you have a **92% compatibility index** with this pathway. Estimated timeline to goal: **3.5 years**.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-3 border border-slate-900 bg-slate-950/40 rounded-xl text-center shrink-0">
              <p className="text-[9px] text-muted-foreground font-semibold uppercase">Median Salary</p>
              <p className="text-base font-bold text-slate-100">$138,000 / yr</p>
            </div>
            <div className="p-3 border border-slate-900 bg-slate-950/40 rounded-xl text-center shrink-0">
              <p className="text-[9px] text-muted-foreground font-semibold uppercase">Hiring Index</p>
              <p className="text-base font-bold text-emerald-500 flex items-center justify-center gap-0.5"><TrendingUp className="h-3.5 w-3.5" /> High</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Tabs Segment */}
      <Tabs defaultValue="roadmap" className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="roadmap">Roadmap Timeline</TabsTrigger>
          <TabsTrigger value="skills">Hiring Trends & Skill Gaps</TabsTrigger>
          <TabsTrigger value="learning">Recommended Learning</TabsTrigger>
        </TabsList>

        {/* Tab 1: Roadmap Timeline */}
        <TabsContent value="roadmap">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Timeline Vertical Track */}
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold">Career Timeline Milestones</CardTitle>
                  <CardDescription className="text-xs">Your personalized blueprint with chronological achievements</CardDescription>
                </CardHeader>
                <CardContent className="relative pl-8 space-y-8 before:absolute before:left-[15px] before:top-2 before:bottom-2 before:w-[1.5px] before:bg-border">
                  {timelineMilestones.map((milestone) => (
                    <div key={milestone.step} className="relative text-left">
                      {/* Timeline Dot Indicator */}
                      <span className={cn(
                        "absolute -left-[28px] top-0 h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-bold border",
                        milestone.status === "Completed" && "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
                        milestone.status === "Active Preparation" && "bg-primary/20 text-primary border-primary animate-pulse",
                        milestone.status === "Future Goal" && "bg-muted text-muted-foreground border-muted-foreground/20"
                      )}>
                        {milestone.step}
                      </span>

                      <div className="space-y-1.5 pl-2">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                          <h4 className="text-sm font-bold text-slate-200">{milestone.role}</h4>
                          <span className={cn(
                            "text-[10px] font-semibold px-2 py-0.5 rounded-sm w-fit border",
                            milestone.status === "Completed" && "bg-emerald-500/5 text-emerald-400 border-emerald-500/20",
                            milestone.status === "Active Preparation" && "bg-indigo-500/5 text-indigo-400 border-indigo-500/20",
                            milestone.status === "Future Goal" && "bg-slate-950 text-muted-foreground border-slate-900"
                          )}>
                            {milestone.status}
                          </span>
                        </div>
                        <p className="text-[10px] font-medium text-muted-foreground flex items-center gap-1.5">
                          <Clock className="h-3 w-3" /> {milestone.timeline}
                        </p>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {milestone.description}
                        </p>
                        <div className="flex flex-wrap gap-1 pt-1">
                          {milestone.skills.map((skill) => (
                            <span key={skill} className="text-[9px] px-2 py-0.5 rounded-md bg-muted text-muted-foreground font-semibold">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Path predictions sidebar */}
            <div className="lg:col-span-1 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold">Career Prediction Diagnostics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-xs leading-relaxed">
                  <div className="p-3.5 bg-indigo-500/5 border border-indigo-500/10 rounded-xl">
                    <p className="font-semibold text-indigo-300">Estimated Target Year: 2029</p>
                    <p className="text-muted-foreground mt-0.5">Based on current course completion metrics and resume project additions.</p>
                  </div>
                  <div className="p-3.5 bg-violet-500/5 border border-violet-500/10 rounded-xl">
                    <p className="font-semibold text-violet-300">Alternate Path: Full-Stack Architect</p>
                    <p className="text-muted-foreground mt-0.5">If you add database normalization skills, you can expand compatibility into system structures by 14%.</p>
                  </div>
                </CardContent>
              </Card>
            </div>
            
          </div>
        </TabsContent>

        {/* Tab 2: Skills & Gaps */}
        <TabsContent value="skills">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Detailed list of skill gaps */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold">Skill Match Breakdowns</CardTitle>
                <CardDescription className="text-xs">Identified gaps for Lead Frontend Architect</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {targetSkills.map((skill) => (
                  <div key={skill.name} className="space-y-1.5 text-xs text-left">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-200">{skill.name}</span>
                      <span className={cn(
                        "text-[9px] px-1.5 py-0.5 rounded-sm font-semibold",
                        skill.status === "Critical Gap" ? "bg-red-500/10 text-red-400 border border-red-500/25 animate-pulse" : "bg-amber-500/10 text-amber-400 border border-amber-500/25"
                      )}>
                        {skill.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Progress value={skill.current} className="flex-1 h-1.5" indicatorClassName={skill.status === "Critical Gap" ? "bg-red-500" : "bg-primary"} />
                      <span className="text-[10px] font-semibold text-muted-foreground shrink-0 w-16 text-right">
                        {skill.current}% / {skill.target}%
                      </span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Hiring Trends info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold">Industry Demand Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 border border-slate-900 bg-slate-950/20 rounded-xl text-left">
                    <TrendingUp className="h-5 w-5 text-indigo-400 mb-2" />
                    <p className="text-[10px] font-semibold text-muted-foreground uppercase">Hiring Volume Growth</p>
                    <p className="text-lg font-bold text-slate-100 mt-0.5">+14.2%</p>
                    <p className="text-[9px] text-muted-foreground mt-1">Hiring demand index for Q3/Q4</p>
                  </div>
                  <div className="p-4 border border-slate-900 bg-slate-950/20 rounded-xl text-left">
                    <MapPin className="h-5 w-5 text-violet-400 mb-2" />
                    <p className="text-[10px] font-semibold text-muted-foreground uppercase">Top Locations</p>
                    <p className="text-lg font-bold text-slate-100 mt-0.5">Remote, SF, NY</p>
                    <p className="text-[9px] text-muted-foreground mt-1">High concentration of active leads</p>
                  </div>
                </div>

                <div className="p-4 border border-slate-900 bg-slate-950/20 rounded-xl text-left">
                  <span className="text-[10px] font-semibold text-indigo-400 tracking-wider uppercase">Preferred Corporate Partners</span>
                  <div className="flex flex-wrap gap-3 mt-3">
                    {["Stripe", "Vercel", "Linear", "Supabase", "OpenAI"].map((comp) => (
                      <div key={comp} className="flex items-center gap-1 text-xs text-slate-300 font-semibold bg-muted/40 px-2.5 py-1.5 rounded-lg border border-muted">
                        <Building className="h-3.5 w-3.5 text-muted-foreground" /> {comp}
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Tab 3: Recommended Learning */}
        <TabsContent value="learning">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {learningTracks.map((track) => (
              <Card key={track.title} hoverEffect className="flex flex-col h-full justify-between">
                <CardHeader>
                  <div className="flex justify-between items-start gap-2 mb-2">
                    <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-primary/20 text-primary uppercase">
                      {track.difficulty}
                    </span>
                    <span className="text-[10px] text-muted-foreground font-semibold flex items-center gap-1">
                      <Clock className="h-3 w-3" /> {track.duration}
                    </span>
                  </div>
                  <CardTitle className="text-sm font-bold text-slate-100 leading-snug">{track.title}</CardTitle>
                  <CardDescription className="text-[10px]">{track.provider}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 flex-1">
                  <p className="text-[10px] text-muted-foreground">Closes specific gaps in:</p>
                  <div className="flex flex-wrap gap-1">
                    {track.skillsMatched.map((s) => (
                      <span key={s} className="text-[9px] px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 font-semibold">
                        {s}
                      </span>
                    ))}
                  </div>
                </CardContent>
                <CardFooter className="pt-0">
                  <Button size="sm" variant="outline" className="w-full text-xs font-semibold cursor-pointer flex items-center justify-center gap-1.5">
                    Start Learning <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
