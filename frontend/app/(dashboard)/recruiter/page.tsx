"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Users,
  Search,
  Briefcase,
  FileCheck,
  Building,
  UserCheck,
  ChevronRight,
  Filter,
} from "lucide-react";

const applicantPool = [
  { name: "Alex Morgan", major: "Computer Science", match: 94, role: "Software Engineer Intern", status: "Tech Screen Scheduled" },
  { name: "Jessica Smith", major: "Data Science", match: 89, role: "Data Engineer Associate", status: "Resume Approved" },
  { name: "Ryan Thompson", major: "Electrical Engineering", match: 85, role: "Software Engineer Intern", status: "Applied" },
  { name: "Elena Rostova", major: "Information Technology", match: 81, role: "Frontend Developer", status: "Applied" },
];

export default function RecruiterDashboard() {
  const [query, setQuery] = React.useState("");

  const filteredApplicants = applicantPool.filter((a) =>
    a.name.toLowerCase().includes(query.toLowerCase()) ||
    a.role.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="space-y-8 text-left">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/40 p-6 rounded-2xl border border-border">
        <div>
          <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">Recruiter Workspace</span>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Stripe Recruitment Hub <Building className="h-5 w-5 text-indigo-400" />
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Manage student applications, placement drives, and interview screening schedules.
          </p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" className="cursor-pointer">Post New Opening</Button>
          <Button size="sm" variant="outline" className="cursor-pointer">Placement Analytics</Button>
        </div>
      </div>

      {/* Grid: Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Active Openings</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">8</span>
            <Briefcase className="h-5 w-5 text-indigo-400" />
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Total Applicants</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">142</span>
            <Users className="h-5 w-5 text-indigo-400" />
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Tech Screens</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">18</span>
            <UserCheck className="h-5 w-5 text-violet-400" />
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Offers Issued</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">4</span>
            <FileCheck className="h-5 w-5 text-emerald-400" />
          </CardContent>
        </Card>
      </div>

      {/* Candidate list segment */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Applicants List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base font-bold">Applicant Tracking Pipeline</CardTitle>
                <CardDescription className="text-xs">Candidates matched automatically by CareerOS AI profile metrics</CardDescription>
              </div>
              <div className="relative">
                <Input
                  type="text"
                  placeholder="Filter by name..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="pl-8 h-9 text-xs"
                />
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {filteredApplicants.map((app) => (
              <div
                key={app.name}
                className="flex items-center justify-between p-3.5 bg-muted/40 border border-muted rounded-xl hover:border-muted-foreground/20 transition-all text-xs"
              >
                <div className="text-left space-y-0.5">
                  <p className="font-semibold text-slate-200">{app.name}</p>
                  <p className="text-[10px] text-muted-foreground">{app.major} • {app.role}</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="font-bold text-indigo-400">{app.match}% match</span>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{app.status}</p>
                  </div>
                  <Button size="icon" variant="ghost" className="h-8 w-8 cursor-pointer">
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Quick Search Filtering */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Filter className="h-4 w-4 text-primary" /> Core Filter Rules
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            <div className="p-3 bg-muted/40 border border-muted rounded-xl text-left space-y-1.5">
              <p className="font-bold text-slate-200">AI Placement Filter</p>
              <p className="text-muted-foreground text-[10px]">Filter candidate matches to above **85%** to bypass initial resume screenings.</p>
            </div>
            <div className="p-3 bg-muted/40 border border-muted rounded-xl text-left space-y-1.5">
              <p className="font-bold text-slate-200">University Affiliation</p>
              <p className="text-muted-foreground text-[10px]">Active Partner Drive: Stanford Engineering, MIT CS Labs, Berkeley EECS.</p>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
