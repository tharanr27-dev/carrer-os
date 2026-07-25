"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/useAuthStore";
import {
  User,
  GraduationCap,
  Briefcase,
  Award,
  Globe,
  Settings,
  Edit2,
  Check,
  Plus,
  X,
  Target,
} from "lucide-react";
import { motion } from "framer-motion";

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore();
  const [isEditingPersonal, setIsEditingPersonal] = React.useState(false);
  const [name, setName] = React.useState(user?.name || "Alex Morgan");
  const [title, setTitle] = React.useState(user?.title || "Computer Science Junior");
  
  // Skills list state
  const [skills, setSkills] = React.useState(["TypeScript", "React", "Next.js", "Zustand", "Framer Motion", "Tailwind CSS"]);
  const [newSkill, setNewSkill] = React.useState("");

  const handleSavePersonal = async () => {
    await updateUser({ name, title });
    setIsEditingPersonal(false);
  };

  const addSkill = (e: React.FormEvent) => {
    e.preventDefault();
    if (newSkill.trim() && !skills.includes(newSkill.trim())) {
      setSkills([...skills, newSkill.trim()]);
      setNewSkill("");
    }
  };

  const removeSkill = (skill: string) => {
    setSkills(skills.filter((s) => s !== skill));
  };

  if (!user) return null;

  return (
    <div className="space-y-8 text-left max-w-4xl mx-auto">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Professional Profile</h1>
        <p className="text-sm text-muted-foreground">
          Keep your professional details updated for the AI recruiter matching engine.
        </p>
      </div>

      {/* Grid: 2 columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Personal info & Skills */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Card 1: Personal Information */}
          <Card className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <User className="h-4.5 w-4.5 text-primary" /> Personal Information
                </CardTitle>
                <CardDescription className="text-xs">Your standard profile bio and details</CardDescription>
              </div>
              <Button
                size="sm"
                variant={isEditingPersonal ? "default" : "outline"}
                onClick={isEditingPersonal ? handleSavePersonal : () => setIsEditingPersonal(true)}
                className="cursor-pointer h-8"
              >
                {isEditingPersonal ? <><Check className="h-3.5 w-3.5 mr-1" /> Save</> : <><Edit2 className="h-3.5 w-3.5 mr-1" /> Edit</>}
              </Button>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              {isEditingPersonal ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-[10px] font-semibold text-muted-foreground uppercase">Full Name</label>
                      <Input value={name} onChange={(e) => setName(e.target.value)} />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-semibold text-muted-foreground uppercase">Headline</label>
                      <Input value={title} onChange={(e) => setTitle(e.target.value)} />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col sm:flex-row sm:items-center gap-6">
                  <div className="h-16 w-16 rounded-full overflow-hidden border border-border shrink-0">
                    <img src={user.avatar} alt={user.name} className="h-full w-full object-cover" />
                  </div>
                  <div className="text-left space-y-1">
                    <h3 className="text-base font-bold text-slate-100">{user.name}</h3>
                    <p className="text-xs text-indigo-400 font-medium">{user.title}</p>
                    <p className="text-[10px] text-muted-foreground">San Francisco, CA • {user.email}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Card 2: Work Experience */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Briefcase className="h-4.5 w-4.5 text-primary" /> Work Experience
                </CardTitle>
                <CardDescription className="text-xs">Your employment history</CardDescription>
              </div>
              <Button size="sm" variant="outline" className="h-8 cursor-pointer"><Plus className="h-3.5 w-3.5 mr-1" /> Add</Button>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="relative pl-6 border-l border-border text-xs text-left space-y-6">
                
                {/* Job 1 */}
                <div className="relative">
                  <span className="absolute -left-[30px] top-0.5 h-3 w-3 rounded-full bg-indigo-500 border border-slate-950" />
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-200">Frontend Engineer Intern — Linear</span>
                      <span className="text-muted-foreground font-normal">Jun 2025 – Sep 2025</span>
                    </div>
                    <p className="text-muted-foreground">Designed and built responsive settings layout modules using React 19, improving page load speeds by 15%.</p>
                  </div>
                </div>

                {/* Job 2 */}
                <div className="relative">
                  <span className="absolute -left-[30px] top-0.5 h-3 w-3 rounded-full bg-slate-700 border border-slate-950" />
                  <div className="space-y-1">
                    <div className="flex justify-between font-semibold">
                      <span className="text-slate-200">Software Engineering Intern — Local Startup</span>
                      <span className="text-muted-foreground font-normal">Jan 2025 – Apr 2025</span>
                    </div>
                    <p className="text-muted-foreground">Integrated RESTful APIs using Node.js/Express, accelerating internal administration lookup queries.</p>
                  </div>
                </div>

              </div>
            </CardContent>
          </Card>

          {/* Card 3: Education */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <GraduationCap className="h-4.5 w-4.5 text-primary" /> Education
                </CardTitle>
                <CardDescription className="text-xs">Degrees and institutions</CardDescription>
              </div>
              <Button size="sm" variant="outline" className="h-8 cursor-pointer"><Plus className="h-3.5 w-3.5 mr-1" /> Add</Button>
            </CardHeader>
            <CardContent className="space-y-4 text-xs text-left">
              <div className="flex justify-between items-start border-b border-border/40 pb-4">
                <div className="space-y-1">
                  <p className="font-bold text-slate-200">Stanford University</p>
                  <p className="text-muted-foreground">BS in Computer Science — GPA: 3.82 / 4.00</p>
                </div>
                <span className="text-muted-foreground">Expected Jun 2027</span>
              </div>
            </CardContent>
          </Card>

        </div>

        {/* Right Column: Skills, Languages, Career Target */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Card 4: Technical Skills Tags */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Settings className="h-4.5 w-4.5 text-primary" /> Technical Skills
              </CardTitle>
              <CardDescription className="text-xs">Tags for resume matching</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-left">
              <div className="flex flex-wrap gap-1.5">
                {skills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-[10px] text-indigo-400 font-semibold"
                  >
                    {skill}
                    <button onClick={() => removeSkill(skill)} className="hover:text-destructive cursor-pointer">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>

              {/* Add skill form */}
              <form onSubmit={addSkill} className="flex gap-2">
                <Input
                  type="text"
                  placeholder="Add skill..."
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  className="h-8 text-xs"
                />
                <Button type="submit" size="sm" variant="outline" className="h-8 shrink-0 cursor-pointer">
                  Add
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Card 5: Certifications */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Award className="h-4.5 w-4.5 text-primary" /> Certifications
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3.5 text-xs text-left">
              <div className="flex items-center gap-2.5 p-2 bg-muted/40 border border-muted rounded-xl">
                <Award className="h-5 w-5 text-indigo-400 shrink-0" />
                <div>
                  <p className="font-bold text-slate-200">AWS Cloud Practitioner</p>
                  <p className="text-[10px] text-muted-foreground">Issued Dec 2025 • Active</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Card 6: Languages */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Globe className="h-4.5 w-4.5 text-primary" /> Languages
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-left">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-slate-200">English</span>
                <span className="text-muted-foreground">Native or Bilingual</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="font-semibold text-slate-200">Spanish</span>
                <span className="text-muted-foreground">Professional Working</span>
              </div>
            </CardContent>
          </Card>

          {/* Card 7: Career Target Goals */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Target className="h-4.5 w-4.5 text-primary" /> Career Target Goals
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-xs text-left">
              <div className="space-y-1">
                <span className="text-[10px] font-semibold text-muted-foreground uppercase">Target Roles</span>
                <p className="font-bold text-slate-200">Frontend Engineer, Full-Stack Engineer</p>
              </div>
              <div className="space-y-1 border-t border-border/40 pt-3">
                <span className="text-[10px] font-semibold text-muted-foreground uppercase">Target Companies</span>
                <p className="font-bold text-slate-200">Stripe, Vercel, Linear, Supabase</p>
              </div>
            </CardContent>
          </Card>

        </div>

      </div>
    </div>
  );
}
