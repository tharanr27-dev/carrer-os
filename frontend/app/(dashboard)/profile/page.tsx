"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorBanner, LoadingBlock, SuccessBanner } from "@/components/ui/feedback";
import { useAuthStore } from "@/store/useAuthStore";
import { api, ProfileResponse } from "@/lib/api";
import { Briefcase, Check, Edit2, Settings, Target, User, X } from "lucide-react";

type RoleData = { skills?: string[]; target_roles?: string; target_companies?: string; [key: string]: unknown };

function asStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
}

function formatRange(start?: string | null, end?: string | null, current?: boolean) {
  const fmt = (iso?: string | null) =>
    iso ? new Date(iso).toLocaleDateString(undefined, { month: "short", year: "numeric" }) : "";
  return `${fmt(start)} – ${current ? "Present" : fmt(end)}`;
}

export default function ProfilePage() {
  const { user, refreshUser } = useAuthStore();
  const queryClient = useQueryClient();
  const profileQuery = useQuery({ queryKey: ["profile"], queryFn: api.getProfile });

  const [editing, setEditing] = React.useState(false);
  const [form, setForm] = React.useState({ first: "", last: "", headline: "", bio: "" });
  const [newSkill, setNewSkill] = React.useState("");
  const [targets, setTargets] = React.useState({ roles: "", companies: "" });
  const [saved, setSaved] = React.useState<string | null>(null);

  const profile = profileQuery.data;
  const roleData = (profile?.role_specific_data ?? {}) as RoleData;
  const skills = asStringList(roleData.skills);

  React.useEffect(() => {
    if (!profile) return;
    setForm({
      first: profile.first_name ?? "",
      last: profile.last_name ?? "",
      headline: profile.headline ?? "",
      bio: profile.bio ?? "",
    });
    setTargets({
      roles: typeof roleData.target_roles === "string" ? roleData.target_roles : "",
      companies: typeof roleData.target_companies === "string" ? roleData.target_companies : "",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile]);

  const save = useMutation({
    mutationFn: (update: Parameters<typeof api.updateProfile>[0]) => api.updateProfile(update),
    onSuccess: async (next: ProfileResponse) => {
      queryClient.setQueryData(["profile"], next);
      await refreshUser();
      setSaved("Profile saved.");
      setTimeout(() => setSaved(null), 3000);
    },
  });

  // role_specific_data is replaced wholesale by the backend, so always send the merged object.
  const saveRoleData = (patch: Partial<RoleData>) =>
    save.mutate({ role_specific_data: { ...(profile?.role_specific_data ?? {}), ...patch } });

  const savePersonal = () => {
    if (!form.first.trim()) return;
    save.mutate(
      {
        first_name: form.first.trim(),
        last_name: form.last.trim(),
        headline: form.headline.trim(),
        bio: form.bio.trim(),
      },
      { onSuccess: () => setEditing(false) }
    );
  };

  const addSkill = (e: React.FormEvent) => {
    e.preventDefault();
    const skill = newSkill.trim();
    if (!skill || skills.includes(skill)) return;
    setNewSkill("");
    saveRoleData({ skills: [...skills, skill] });
  };

  if (!user) return null;
  if (profileQuery.isLoading) return <LoadingBlock label="Loading profile…" />;
  if (profileQuery.error) return <ErrorBanner error={profileQuery.error} onRetry={() => void profileQuery.refetch()} />;

  return (
    <div className="space-y-8 text-left max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Professional Profile</h1>
        <p className="text-sm text-muted-foreground">
          Keep your professional details updated for the AI recruiter matching engine.
        </p>
      </div>

      <SuccessBanner message={saved} />
      <ErrorBanner error={save.error} />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <User className="h-4.5 w-4.5 text-primary" /> Personal Information
                </CardTitle>
                <CardDescription className="text-xs">Your standard profile bio and details</CardDescription>
              </div>
              <Button
                size="sm"
                variant={editing ? "default" : "outline"}
                isLoading={save.isPending}
                onClick={editing ? savePersonal : () => setEditing(true)}
                className="h-8"
              >
                {editing ? (
                  <>
                    <Check className="h-3.5 w-3.5 mr-1" /> Save
                  </>
                ) : (
                  <>
                    <Edit2 className="h-3.5 w-3.5 mr-1" /> Edit
                  </>
                )}
              </Button>
            </CardHeader>
            <CardContent className="space-y-4 text-xs">
              {editing ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-[10px] font-semibold text-muted-foreground uppercase">First Name</label>
                      <Input value={form.first} onChange={(e) => setForm({ ...form, first: e.target.value })} />
                      {!form.first.trim() && <p className="text-[10px] text-destructive">First name is required.</p>}
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-semibold text-muted-foreground uppercase">Last Name</label>
                      <Input value={form.last} onChange={(e) => setForm({ ...form, last: e.target.value })} />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase">Headline</label>
                    <Input value={form.headline} onChange={(e) => setForm({ ...form, headline: e.target.value })} />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase">Bio</label>
                    <textarea
                      value={form.bio}
                      onChange={(e) => setForm({ ...form, bio: e.target.value })}
                      rows={4}
                      className="w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring"
                    />
                  </div>
                </div>
              ) : (
                <div className="flex flex-col sm:flex-row sm:items-center gap-6">
                  <div className="h-16 w-16 rounded-full overflow-hidden border border-border shrink-0 bg-primary/10 flex items-center justify-center text-lg font-bold text-primary">
                    {user.avatar ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={user.avatar} alt={user.name} className="h-full w-full object-cover" />
                    ) : (
                      user.name.charAt(0).toUpperCase()
                    )}
                  </div>
                  <div className="text-left space-y-1">
                    <h3 className="text-base font-bold">{user.name}</h3>
                    {user.title && <p className="text-xs text-indigo-400 font-medium">{user.title}</p>}
                    <p className="text-[10px] text-muted-foreground">{user.email}</p>
                    {profile?.bio && <p className="text-xs text-muted-foreground pt-1">{profile.bio}</p>}
                    <p className="text-[10px] text-muted-foreground">
                      Profile completion: <span className="font-semibold">{profile?.completion_percentage ?? 0}%</span>
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Briefcase className="h-4.5 w-4.5 text-primary" /> Work Experience
              </CardTitle>
              <CardDescription className="text-xs">Your employment history</CardDescription>
            </CardHeader>
            <CardContent>
              {profile?.experiences.length ? (
                <div className="relative pl-6 border-l border-border text-xs space-y-6">
                  {profile.experiences.map((exp) => (
                    <div key={exp.id} className="relative">
                      <span className="absolute -left-[30px] top-0.5 h-3 w-3 rounded-full bg-indigo-500" />
                      <div className="flex justify-between font-semibold">
                        <span>
                          {exp.title} — {exp.company}
                        </span>
                        <span className="text-muted-foreground font-normal">
                          {formatRange(exp.start_date, exp.end_date, exp.is_current)}
                        </span>
                      </div>
                      {exp.description && <p className="text-muted-foreground">{exp.description}</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground">No experience on file yet.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-4 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Settings className="h-4.5 w-4.5 text-primary" /> Technical Skills
              </CardTitle>
              <CardDescription className="text-xs">Tags for resume matching</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-left">
              <div className="flex flex-wrap gap-1.5">
                {skills.length === 0 && <p className="text-xs text-muted-foreground">No skills added yet.</p>}
                {skills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-[10px] text-indigo-400 font-semibold"
                  >
                    {skill}
                    <button
                      aria-label={`Remove ${skill}`}
                      onClick={() => saveRoleData({ skills: skills.filter((s) => s !== skill) })}
                      className="hover:text-destructive cursor-pointer"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
              <form onSubmit={addSkill} className="flex gap-2">
                <Input
                  type="text"
                  placeholder="Add skill..."
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  className="h-8 text-xs"
                />
                <Button type="submit" size="sm" variant="outline" className="h-8 shrink-0" disabled={save.isPending}>
                  Add
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Target className="h-4.5 w-4.5 text-primary" /> Career Target Goals
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-left">
              <div className="space-y-1">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase">Target Roles</label>
                <Input
                  value={targets.roles}
                  onChange={(e) => setTargets({ ...targets, roles: e.target.value })}
                  placeholder="e.g. Frontend Engineer"
                />
              </div>
              <div className="space-y-1">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase">Target Companies</label>
                <Input
                  value={targets.companies}
                  onChange={(e) => setTargets({ ...targets, companies: e.target.value })}
                  placeholder="e.g. Stripe, Vercel"
                />
              </div>
              <Button
                size="sm"
                variant="outline"
                isLoading={save.isPending}
                onClick={() => saveRoleData({ target_roles: targets.roles.trim(), target_companies: targets.companies.trim() })}
              >
                Save targets
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
