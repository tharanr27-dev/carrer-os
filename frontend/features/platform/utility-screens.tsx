"use client";

import React from "react";
import NextLink from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Bell, Briefcase, Search } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EmptyState, ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { api } from "@/lib/api";
import { NotificationCategory, useNotificationStore } from "@/store/useNotificationStore";
import { cn } from "@/lib/utils";

/** Searches community posts (server-side) and open jobs (filtered from the job board). */
export function GlobalSearchView() {
  const [input, setInput] = React.useState("");
  const [term, setTerm] = React.useState("");

  const posts = useQuery({ queryKey: ["feed", "search", term], queryFn: () => api.searchPosts(term), enabled: term.length > 0 });
  const jobs = useQuery({ queryKey: ["open-jobs"], queryFn: api.openJobs, enabled: term.length > 0 });

  const t = term.toLowerCase();
  const matchedJobs = (jobs.data ?? []).filter(
    (j) => j.title.toLowerCase().includes(t) || (j.company_name ?? "").toLowerCase().includes(t) || (j.location ?? "").toLowerCase().includes(t)
  );

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Global Search</h1>
        <p className="text-sm text-muted-foreground">Find community posts and open jobs.</p>
      </div>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          setTerm(input.trim());
        }}
      >
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input className="pl-9" placeholder="Search…" value={input} onChange={(e) => setInput(e.target.value)} />
        </div>
        <Button type="submit">Search</Button>
      </form>

      {!term ? (
        <EmptyState title="Type something to search" />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">Community posts</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {posts.isLoading ? (
                <LoadingBlock />
              ) : posts.error ? (
                <ErrorBanner error={posts.error} onRetry={() => void posts.refetch()} />
              ) : !posts.data?.length ? (
                <p className="text-xs text-muted-foreground">No matching posts.</p>
              ) : (
                posts.data.map((p) => (
                  <NextLink key={p.id} href="/community" className="block p-3 rounded-xl border border-border hover:border-primary/40">
                    <p className="text-sm font-semibold">{p.title}</p>
                    <p className="text-xs text-muted-foreground line-clamp-2">{p.content}</p>
                  </NextLink>
                ))
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold">Jobs</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {jobs.isLoading ? (
                <LoadingBlock />
              ) : jobs.error ? (
                <ErrorBanner error={jobs.error} onRetry={() => void jobs.refetch()} />
              ) : !matchedJobs.length ? (
                <p className="text-xs text-muted-foreground">No matching jobs.</p>
              ) : (
                matchedJobs.map((j) => (
                  <NextLink key={j.id} href="/jobs" className="flex items-center gap-2 p-3 rounded-xl border border-border hover:border-primary/40">
                    <Briefcase className="h-4 w-4 text-primary" />
                    <div>
                      <p className="text-sm font-semibold">{j.title}</p>
                      <p className="text-xs text-muted-foreground">{j.company_name}</p>
                    </div>
                  </NextLink>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

const CATEGORIES: ("all" | NotificationCategory)[] = ["all", "jobs", "interviews", "learning", "community", "system"];

export function NotificationCenterView() {
  const { notifications, markAsRead, markAllAsRead, clearAll } = useNotificationStore();
  const [filter, setFilter] = React.useState<"all" | NotificationCategory>("all");
  const visible = notifications.filter((n) => filter === "all" || n.category === filter);

  return (
    <div className="space-y-6 text-left">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
            <Bell className="h-7 w-7 text-primary" /> Notification Center
          </h1>
          <p className="text-sm text-muted-foreground">Platform announcements and updates from your activity.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={markAllAsRead} disabled={!notifications.some((n) => !n.isRead)}>
            Mark all read
          </Button>
          <Button variant="ghost" size="sm" onClick={clearAll} disabled={!notifications.length}>
            Clear
          </Button>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => setFilter(c)}
            className={cn("px-3 py-1 rounded-full text-xs font-semibold capitalize border", filter === c ? "bg-primary text-primary-foreground border-primary" : "border-border")}
          >
            {c}
          </button>
        ))}
      </div>
      {visible.length === 0 ? (
        <EmptyState title="No notifications" description="Announcements and activity updates will show up here." />
      ) : (
        <div className="space-y-3">
          {visible.map((n) => (
            <Card key={n.id} className={n.isRead ? "opacity-70" : ""}>
              <CardContent className="pt-6 flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <p className="text-[10px] uppercase font-semibold text-muted-foreground">
                    {n.category} • {n.time}
                  </p>
                  <p className="text-sm font-semibold">{n.title}</p>
                  <p className="text-xs text-muted-foreground">{n.description}</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  {n.link && (
                    <NextLink href={n.link} onClick={() => markAsRead(n.id)}>
                      <Button size="sm" variant="outline">Open</Button>
                    </NextLink>
                  )}
                  {!n.isRead && (
                    <Button size="sm" variant="ghost" onClick={() => markAsRead(n.id)}>
                      Mark read
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
