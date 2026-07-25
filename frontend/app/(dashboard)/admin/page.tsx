"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ShieldCheck,
  Activity,
  Database,
  Cpu,
  AlertTriangle,
  Terminal,
  Server,
  RefreshCw,
} from "lucide-react";

const auditLogs = [
  { action: "User session switch", user: "Dr. Robert Chen (Officer)", time: "2 mins ago", status: "Success" },
  { action: "Resume ATS scanned", user: "Alex Morgan (Student)", time: "10 mins ago", status: "Success" },
  { action: "New job posted", user: "Sarah Jenkins (Recruiter)", time: "1 hour ago", status: "Success" },
  { action: "Database backup", user: "System Cron", time: "4 hours ago", status: "Success" },
];

export default function AdminDashboard() {
  return (
    <div className="space-y-8 text-left">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/40 p-6 rounded-2xl border border-border">
        <div>
          <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">System Administration</span>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            CareerOS AI Operations Center <ShieldCheck className="h-5 w-5 text-indigo-400" />
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            Monitor model usage costs, vector indexes, active websocket connections, and audit trails.
          </p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" className="cursor-pointer flex gap-1.5"><RefreshCw className="h-3.5 w-3.5" /> Purge Cache</Button>
          <Button size="sm" variant="outline" className="cursor-pointer">Console Logs</Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">API Status</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold text-emerald-500">99.98%</span>
            <Server className="h-5 w-5 text-emerald-500" />
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Monthly Model Cost</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">$1,242.80</span>
            <Cpu className="h-5 w-5 text-indigo-400" />
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Vector Index Nodes</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">14,204</span>
            <Database className="h-5 w-5 text-violet-400" />
          </CardContent>
        </Card>

        <Card hoverEffect>
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-semibold uppercase">Active Connections</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-between items-center">
            <span className="text-2xl font-bold">382 / sec</span>
            <Activity className="h-5 w-5 text-emerald-400" />
          </CardContent>
        </Card>
      </div>

      {/* Audit Logs & Health Warnings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Logs */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Terminal className="h-4.5 w-4.5 text-primary" /> Live Audit Log Stream
            </CardTitle>
            <CardDescription className="text-xs">Security operations and database audit trails</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {auditLogs.map((log, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-muted/40 border border-muted rounded-xl text-xs"
              >
                <div className="text-left space-y-0.5">
                  <p className="font-semibold text-slate-200">{log.action}</p>
                  <p className="text-[10px] text-muted-foreground">{log.user}</p>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-emerald-400 font-semibold px-2 py-0.5 rounded-sm bg-emerald-500/5 border border-emerald-500/10">
                    {log.status}
                  </span>
                  <p className="text-[9px] text-muted-foreground mt-1">{log.time}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* System Warnings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <AlertTriangle className="h-4.5 w-4.5 text-amber-500" /> System Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-xs leading-relaxed text-left">
            <div className="p-3 bg-amber-500/5 border border-amber-500/10 rounded-xl space-y-1">
              <p className="font-semibold text-amber-400">Database Size Warning</p>
              <p className="text-muted-foreground text-[10px]">Read-replica shard C is approaching 85% disk storage capacity.</p>
            </div>
            <div className="p-3 bg-indigo-500/5 border border-indigo-500/10 rounded-xl space-y-1">
              <p className="font-semibold text-indigo-400">LLM Response Latency</p>
              <p className="text-muted-foreground text-[10px]">Average inference response latencies increased to **1,850ms** (+400ms).</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
