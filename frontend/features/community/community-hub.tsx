"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Heart, MessageCircle, Search, Users } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState, ErrorBanner, LoadingBlock } from "@/components/ui/feedback";
import { api, Post } from "@/lib/api";

const CATEGORIES = ["General", "Career Advice", "Interview Prep", "Resume", "Jobs", "Learning"];

function PostCard({ post }: { post: Post }) {
  const queryClient = useQueryClient();
  const [open, setOpen] = React.useState(false);
  const [comment, setComment] = React.useState("");
  const [validation, setValidation] = React.useState<string | null>(null);

  // Opening a post loads its detail (GET /community/posts/{id}), which also records a view.
  const detail = useQuery({
    queryKey: ["post", post.id],
    queryFn: () => api.getPost(post.id),
    enabled: open,
    staleTime: 0,
  });

  const comments = useQuery({
    queryKey: ["comments", post.id],
    queryFn: () => api.getComments(post.id),
    enabled: open,
  });

  const like = useMutation({
    mutationFn: () => api.react("post", post.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["feed"] }),
  });

  const addComment = useMutation({
    mutationFn: () => api.addComment(post.id, comment.trim()),
    onSuccess: async () => {
      setComment("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["comments", post.id] }),
        queryClient.invalidateQueries({ queryKey: ["feed"] }),
      ]);
    },
  });

  const submitComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!comment.trim()) {
      setValidation("Write a comment first.");
      return;
    }
    setValidation(null);
    addComment.mutate();
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-bold">{post.title}</CardTitle>
        <CardDescription className="text-[11px]">
          {post.category} • {new Date(post.created_at).toLocaleString()}
          {post.status !== "published" && post.status !== "PUBLISHED" ? ` • ${post.status}` : ""}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-xs">
        <p className="whitespace-pre-wrap text-muted-foreground">{post.content}</p>
        {post.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {post.tags.map((t) => (
              <span key={t.id} className="px-2 py-0.5 rounded-md bg-primary/10 text-primary text-[10px] font-semibold">
                #{t.name}
              </span>
            ))}
          </div>
        )}
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" className="gap-1" aria-label="Like post" disabled={like.isPending} onClick={() => like.mutate()}>
            <Heart className="h-3.5 w-3.5" /> {post.reactions_count}
          </Button>
          <Button size="sm" variant="ghost" className="gap-1" aria-label="Show comments" onClick={() => setOpen(!open)}>
            <MessageCircle className="h-3.5 w-3.5" /> {post.comments_count}
          </Button>
        </div>
        <ErrorBanner error={like.error} />
        {open && (
          <div className="space-y-2 border-t border-border pt-3">
            {detail.data && <p className="text-[10px] text-muted-foreground">{detail.data.views_count} views</p>}
            <ErrorBanner error={detail.error} onRetry={() => void detail.refetch()} />
            {comments.isLoading ? (
              <LoadingBlock label="" className="py-2" />
            ) : comments.error ? (
              <ErrorBanner error={comments.error} onRetry={() => void comments.refetch()} />
            ) : comments.data?.length ? (
              comments.data.map((c) => (
                <div key={c.id} className="rounded-lg bg-muted/40 p-2">
                  {c.content}
                </div>
              ))
            ) : (
              <p className="text-muted-foreground">No comments yet.</p>
            )}
            <form onSubmit={submitComment} className="flex gap-2">
              <Input value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Add a comment…" />
              <Button type="submit" size="sm" isLoading={addComment.isPending}>
                Post
              </Button>
            </form>
            <ErrorBanner error={validation ?? addComment.error} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function PostList({ posts, isLoading, error, onRetry, emptyTitle }: { posts?: Post[]; isLoading: boolean; error: unknown; onRetry: () => void; emptyTitle: string }) {
  if (isLoading) return <LoadingBlock label="Loading posts…" />;
  if (error) return <ErrorBanner error={error} onRetry={onRetry} />;
  if (!posts?.length) return <EmptyState title={emptyTitle} />;
  return (
    <div className="space-y-4">
      {posts.map((p) => (
        <PostCard key={p.id} post={p} />
      ))}
    </div>
  );
}

export function CommunityHubView() {
  const queryClient = useQueryClient();
  const [tab, setTab] = React.useState("latest");
  const [search, setSearch] = React.useState("");
  const [activeSearch, setActiveSearch] = React.useState("");

  const [form, setForm] = React.useState({ title: "", content: "", category: CATEGORIES[0], tags: "" });
  const [validation, setValidation] = React.useState<string | null>(null);

  const latest = useQuery({ queryKey: ["feed", "latest"], queryFn: () => api.latestFeed() });
  const trending = useQuery({ queryKey: ["feed", "trending"], queryFn: () => api.trendingFeed() });
  const results = useQuery({
    queryKey: ["feed", "search", activeSearch],
    queryFn: () => api.searchPosts(activeSearch),
    enabled: activeSearch.length > 0,
  });

  const create = useMutation({
    mutationFn: () =>
      api.createPost({
        title: form.title.trim(),
        content: form.content.trim(),
        category: form.category,
        tags: form.tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
      }),
    onSuccess: async () => {
      setForm({ title: "", content: "", category: CATEGORIES[0], tags: "" });
      await queryClient.invalidateQueries({ queryKey: ["feed"] });
    },
  });

  const submitPost = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim()) {
      setValidation("A post needs a title and some content.");
      return;
    }
    setValidation(null);
    create.mutate();
  };

  return (
    <div className="space-y-6 text-left">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
          <Users className="h-7 w-7 text-primary" /> Community
        </h1>
        <p className="text-sm text-muted-foreground">Share experiences, ask questions, and learn from other candidates.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              setActiveSearch(search.trim());
              if (search.trim()) setTab("search");
            }}
            className="flex gap-2"
          >
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input className="pl-9" placeholder="Search posts…" value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <Button type="submit" variant="outline">
              Search
            </Button>
          </form>

          <Tabs value={tab} onValueChange={setTab}>
            <TabsList className="mb-4 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30">
              <TabsTrigger value="latest" className="text-xs">Latest</TabsTrigger>
              <TabsTrigger value="trending" className="text-xs">Trending</TabsTrigger>
              {activeSearch && <TabsTrigger value="search" className="text-xs">Results for “{activeSearch}”</TabsTrigger>}
            </TabsList>
            <TabsContent value="latest">
              <PostList posts={latest.data?.map((f) => f.post)} isLoading={latest.isLoading} error={latest.error} onRetry={() => void latest.refetch()} emptyTitle="No posts yet, be the first to share." />
            </TabsContent>
            <TabsContent value="trending">
              <PostList posts={trending.data?.map((f) => f.post)} isLoading={trending.isLoading} error={trending.error} onRetry={() => void trending.refetch()} emptyTitle="Nothing trending yet." />
            </TabsContent>
            <TabsContent value="search">
              <PostList posts={results.data} isLoading={results.isLoading} error={results.error} onRetry={() => void results.refetch()} emptyTitle="No posts match your search." />
            </TabsContent>
          </Tabs>
        </div>

        <Card className="lg:col-span-4 self-start">
          <CardHeader>
            <CardTitle className="text-base font-bold">Share something</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={submitPost} className="space-y-3">
              <ErrorBanner error={validation ?? create.error} />
              <Input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              <textarea
                rows={4}
                placeholder="What would you like to discuss?"
                value={form.content}
                onChange={(e) => setForm({ ...form, content: e.target.value })}
                className="w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
              />
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {CATEGORIES.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
              <Input placeholder="Tags (comma separated)" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
              <Button type="submit" className="w-full" isLoading={create.isPending}>
                Publish post
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
