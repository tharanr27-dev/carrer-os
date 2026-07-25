"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  GraduationCap,
  Users,
  TrendingUp,
  FileCheck,
  Calendar,
  Building,
} from "lucide-react";

export default function OfficerDashboard() {
  const activeDrives = [
    { company: "Google", date: "Jul 10, 2026", type: "Placement Drive", registered: 45 },
    { company: "Stripe", date: "Jul 15, 2026", type: "Placement Drive", registered: 32 },
    { company: "Vercel", date: "Jul 22, 2026", type: "Internship Drive", registered: 28 },
  ];

  return (
    <div className="space-y-8 text-left">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/40 p-6 rounded-2xl border border-border">
        <div>
          <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">Placement Officer Workspace</span>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Stanford School of Engineering Placement Hub <GraduationCap className="h-5 w-5 text-indigo-400" />
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Monitor batch-wide readiness scores, active hiring drives, and industry partnerships.
          </p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" className="cursor-pointer">Announce New Drive</Button>
          <Button size="sm" variant="outline" className="cursor-pointer">Download Report</Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Enrolled Students</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">342</span>
            <Users className="h-5 w-5 text-indigo-400" />
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Placed Ratio</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">64.2%</span>
            <FileCheck className="h-5 w-5 text-indigo-400" />
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Average Readiness</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">76.4%</span>
            <TrendingUp className="h-5 w-5 text-violet-400" />
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Hiring Partners</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">24</span>
            <Building className="h-5 w-5 text-emerald-400" />
          </CardContent>
        </Card>
      </div>

      {/* Row 3: Drives and student monitoring */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Placement Drives List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base font-bold">Upcoming Recruitment Drives</CardTitle>
            <CardDescription className="text-xs">Active scheduling for Stripe, Google, and key partner portals</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeDrives.map((d) => (
              <div
                key={d.company}
                className="flex items-center justify-between p-3.5 bg-muted/40 border border-muted rounded-xl text-xs"
              >
                <div className="flex items-center gap-3">
                  <Calendar className="h-4.5 w-4.5 text-indigo-400 shrink-0" />
                  <div className="text-left space-y-0.5">
                    <p className="font-semibold text-slate-200">{d.company} {d.type}</p>
                    <p className="text-[10px] text-muted-foreground">{d.date}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="font-bold text-slate-200">{d.registered} registered</span>
                  <p className="text-[10px] text-muted-foreground mt-0.5">Sync complete</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Analytics Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Placement Action Items</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-xs leading-relaxed">
            <div className="p-3 bg-muted/40 border border-muted rounded-xl text-left space-y-1">
              <p className="font-semibold text-slate-200">System Design Skill Gaps</p>
              <p className="text-muted-foreground text-[10px]">Over 40% of CS seniors lack system design targets. We recommend announcing a workshop.</p>
            </div>
            <div className="p-3 bg-muted/40 border border-muted rounded-xl text-left space-y-1">
              <p className="font-semibold text-slate-200">Resume Review Checklist</p>
              <p className="text-muted-foreground text-[10px]">12 pending resumes require manual coordinator approval for drive submissions.</p>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
