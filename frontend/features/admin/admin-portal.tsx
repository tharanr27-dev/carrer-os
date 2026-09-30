"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from "@/components/ui/feedback";
import { JsonView } from "@/components/ui/json-view";
import { api } from "@/lib/api";

const selectClass = "flex h-9 rounded-md border border-input bg-background px-2 text-xs";
const USER_STATUSES = ["ACTIVE", "INACTIVE", "SUSPENDED", "LOCKED", "PENDING_VERIFICATION", "DELETED"];
const DECISIONS = ["approve", "reject", "suspend", "restore", "escalate", "delete"];

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-[10px] font-semibold uppercase text-muted-foreground">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}

function Overview() {
  const summary = useQuery({ queryKey: ["admin-summary"], queryFn: api.admin.summary });
  const health = useQuery({ queryKey: ["admin-health"], queryFn: api.admin.health });
  const snapshots = useQuery({ queryKey: ["admin-health-snapshots"], queryFn: api.admin.healthSnapshots });

  return (
    <div className="space-y-6">
      <ErrorBanner error={summary.error} onRetry={() => void summary.refetch()} />
      {summary.isLoading ? (
        <LoadingBlock />
      ) : summary.data ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Stat label="Total users" value={summary.data.total_users} />
          <Stat label="Active users" value={summary.data.active_users} />
          <Stat label="Pending moderation" value={summary.data.pending_moderation_count} />
          <Stat label="System status" value={summary.data.system_status} />
          <Stat label="Unresolved reports" value={summary.data.unresolved_reports} />
          <Stat label="AI tokens today" value={summary.data.ai_daily_token_usage.toLocaleString()} />
          <Stat label="AI cost this month" value={`$${summary.data.ai_monthly_cost_usd.toFixed(2)}`} />
        </div>
      ) : null}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <Activity className="h-4 w-4 text-primary" /> System health
          </CardTitle>
          <Button size="sm" variant="outline" onClick={() => void health.refetch()} isLoading={health.isFetching}>
            Re-check
          </Button>
        </CardHeader>
        <CardContent>
          <ErrorBanner error={health.error} />
          {health.data && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
              {(
                [
                  ["Database", health.data.database_ok],
                  ["Redis", health.data.redis_ok],
                  ["Celery", health.data.celery_ok],
                  ["Storage", health.data.storage_ok],
                ] as const
              ).map(([label, ok]) => (
                <div key={label} className="rounded-xl border border-border p-3 flex items-center justify-between">
                  {label}
                  <span className={ok ? "text-emerald-500 font-semibold" : "text-rose-500 font-semibold"}>{ok ? "OK" : "Down"}</span>
                </div>
              ))}
            </div>
          )}
          <div className="mt-3 text-[11px] text-muted-foreground">
            {snapshots.isLoading ? "Loading last recorded snapshot…" : snapshots.error ? "Snapshot history unavailable." : snapshots.data ? "A health snapshot has been recorded." : "No health snapshot recorded yet."}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Users() {
  const queryClient = useQueryClient();
  const users = useQuery({ queryKey: ["admin-users"], queryFn: api.admin.users });
  const roles = useQuery({ queryKey: ["admin-roles"], queryFn: api.admin.roles });
  const permissions = useQuery({ queryKey: ["admin-permissions"], queryFn: api.admin.permissions });
  const [notice, setNotice] = React.useState<string | null>(null);

  const setStatus = useMutation({
    mutationFn: (v: { id: string; status: string }) => api.admin.setUserStatus(v.id, v.status),
    onSuccess: async () => {
      setNotice("User status updated.");
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });
  const assign = useMutation({
    mutationFn: (v: { id: string; role: string }) => api.admin.assignRole(v.id, v.role),
    onSuccess: async () => {
      setNotice("Role assigned.");
      await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  if (users.isLoading) return <LoadingBlock />;
  if (users.error) return <ErrorBanner error={users.error} onRetry={() => void users.refetch()} />;

  return (
    <div className="space-y-3">
      <SuccessBanner message={notice} />
      <ErrorBanner error={setStatus.error ?? assign.error ?? roles.error} />
      {!users.data?.length ? (
        <EmptyState title="No users" />
      ) : (
        users.data.map((u) => (
          <Card key={u.id}>
            <CardContent className="pt-6 flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{u.email}</p>
                <p className="text-xs text-muted-foreground">
                  Roles: {u.roles.length ? u.roles.join(", ") : "none"} • joined {new Date(u.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex gap-2">
                <select
                  className={selectClass}
                  value={u.status}
                  aria-label={`Status for ${u.email}`}
                  disabled={setStatus.isPending}
                  onChange={(e) => setStatus.mutate({ id: u.id, status: e.target.value })}
                >
                  {USER_STATUSES.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
                <select
                  className={selectClass}
                  value=""
                  aria-label={`Assign role to ${u.email}`}
                  disabled={assign.isPending || !roles.data?.length}
                  onChange={(e) => e.target.value && assign.mutate({ id: u.id, role: e.target.value })}
                >
                  <option value="">Assign role…</option>
                  {roles.data?.map((r) => (
                    <option key={r.id} value={r.name}>
                      {r.name}
                    </option>
                  ))}
                </select>
              </div>
            </CardContent>
          </Card>
        ))
      )}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Roles &amp; permissions</CardTitle>
          <CardDescription className="text-xs">Roles you can assign and the permission catalog they draw from.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-xs">
          <p>
            <span className="font-semibold">Roles:</span> {roles.data?.map((r) => r.name).join(", ") || "none defined"}
          </p>
          <p>
            <span className="font-semibold">Permissions:</span> {permissions.data?.map((p) => p.name).join(", ") || "none defined"}
          </p>
          <ErrorBanner error={permissions.error} />
        </CardContent>
      </Card>
    </div>
  );
}

function Moderation() {
  const queryClient = useQueryClient();
  const queue = useQuery({ queryKey: ["admin-moderation"], queryFn: () => api.admin.moderationQueue("pending") });
  const [reasons, setReasons] = React.useState<Record<string, string>>({});
  const decide = useMutation({
    mutationFn: (v: { id: string; decision: string }) => api.admin.moderationDecision(v.id, v.decision, reasons[v.id]?.trim() || undefined),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-moderation"] });
      await queryClient.invalidateQueries({ queryKey: ["admin-summary"] });
    },
  });

  if (queue.isLoading) return <LoadingBlock />;
  if (queue.error) return <ErrorBanner error={queue.error} onRetry={() => void queue.refetch()} />;

  return (
    <div className="space-y-3">
      <ErrorBanner error={decide.error} />
      {!queue.data?.length ? (
        <EmptyState title="Queue is clear" description="No items are waiting for moderation." />
      ) : (
        queue.data.map((item) => (
          <Card key={item.id}>
            <CardContent className="pt-6 space-y-3">
              <div>
                <p className="text-sm font-semibold capitalize">{item.entity_type}</p>
                <p className="text-xs text-muted-foreground">
                  {item.reason ?? "No reason given"} • {new Date(item.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex gap-2">
                <Input
                  className="h-9 text-xs"
                  placeholder="Decision note (optional)"
                  value={reasons[item.id] ?? ""}
                  onChange={(e) => setReasons({ ...reasons, [item.id]: e.target.value })}
                />
                {DECISIONS.slice(0, 3).map((d) => (
                  <Button key={d} size="sm" variant="outline" className="capitalize" disabled={decide.isPending} onClick={() => decide.mutate({ id: item.id, decision: d })}>
                    {d}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}

function Configuration() {
  const queryClient = useQueryClient();
  const flags = useQuery({ queryKey: ["admin-flags"], queryFn: api.admin.flags });
  const settings = useQuery({ queryKey: ["admin-settings"], queryFn: api.admin.settings });
  const [flagForm, setFlagForm] = React.useState({ key: "", description: "" });
  const [settingForm, setSettingForm] = React.useState({ key: "", value: "" });
  const [values, setValues] = React.useState<Record<string, string>>({});
  const [validation, setValidation] = React.useState<string | null>(null);

  const createFlag = useMutation({
    mutationFn: () => api.admin.createFlag({ key: flagForm.key.trim(), description: flagForm.description.trim() || undefined }),
    onSuccess: async () => {
      setFlagForm({ key: "", description: "" });
      await queryClient.invalidateQueries({ queryKey: ["admin-flags"] });
    },
  });
  const toggleFlag = useMutation({
    mutationFn: (v: { id: string; enabled: boolean }) => api.admin.updateFlag(v.id, { is_enabled: v.enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-flags"] }),
  });
  const createSetting = useMutation({
    mutationFn: () => api.admin.createSetting({ key: settingForm.key.trim(), value: settingForm.value }),
    onSuccess: async () => {
      setSettingForm({ key: "", value: "" });
      await queryClient.invalidateQueries({ queryKey: ["admin-settings"] });
    },
  });
  const updateSetting = useMutation({
    mutationFn: (v: { key: string; value: string }) => api.admin.updateSetting(v.key, v.value),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-settings"] }),
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Feature flags</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <ErrorBanner error={validation ?? flags.error ?? createFlag.error ?? toggleFlag.error} />
          {flags.isLoading ? (
            <LoadingBlock />
          ) : !flags.data?.length ? (
            <p className="text-xs text-muted-foreground">No flags yet.</p>
          ) : (
            flags.data.map((f) => (
              <div key={f.id} className="flex items-center justify-between rounded-xl border border-border p-3 text-xs">
                <div>
                  <p className="font-semibold">{f.key}</p>
                  {f.description && <p className="text-muted-foreground">{f.description}</p>}
                </div>
                <Button size="sm" variant={f.is_enabled ? "default" : "outline"} disabled={toggleFlag.isPending} onClick={() => toggleFlag.mutate({ id: f.id, enabled: !f.is_enabled })}>
                  {f.is_enabled ? "Enabled" : "Disabled"}
                </Button>
              </div>
            ))
          )}
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!flagForm.key.trim()) return setValidation("A flag needs a key.");
              setValidation(null);
              createFlag.mutate();
            }}
          >
            <Input className="h-9 text-xs" placeholder="flag_key" value={flagForm.key} onChange={(e) => setFlagForm({ ...flagForm, key: e.target.value })} />
            <Input className="h-9 text-xs" placeholder="Description" value={flagForm.description} onChange={(e) => setFlagForm({ ...flagForm, description: e.target.value })} />
            <Button type="submit" size="sm" isLoading={createFlag.isPending}>
              Add
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Platform settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <ErrorBanner error={settings.error ?? createSetting.error ?? updateSetting.error} />
          {settings.isLoading ? (
            <LoadingBlock />
          ) : !settings.data?.length ? (
            <p className="text-xs text-muted-foreground">No settings yet.</p>
          ) : (
            settings.data.map((s) => (
              <div key={s.id} className="flex items-center gap-2 text-xs">
                <span className="w-1/3 font-semibold truncate" title={s.key}>
                  {s.key}
                </span>
                <Input className="h-9 text-xs" value={values[s.key] ?? s.value ?? ""} onChange={(e) => setValues({ ...values, [s.key]: e.target.value })} />
                <Button size="sm" variant="outline" disabled={updateSetting.isPending || values[s.key] === undefined} onClick={() => updateSetting.mutate({ key: s.key, value: values[s.key] })}>
                  Save
                </Button>
              </div>
            ))
          )}
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!settingForm.key.trim()) return setValidation("A setting needs a key.");
              setValidation(null);
              createSetting.mutate();
            }}
          >
            <Input className="h-9 text-xs" placeholder="key" value={settingForm.key} onChange={(e) => setSettingForm({ ...settingForm, key: e.target.value })} />
            <Input className="h-9 text-xs" placeholder="value" value={settingForm.value} onChange={(e) => setSettingForm({ ...settingForm, value: e.target.value })} />
            <Button type="submit" size="sm" isLoading={createSetting.isPending}>
              Add
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function Announcements() {
  const queryClient = useQueryClient();
  const active = useQuery({ queryKey: ["announcements"], queryFn: api.admin.activeAnnouncements });
  const [ann, setAnn] = React.useState({ title: "", content: "", severity: "info" });
  const [bc, setBc] = React.useState({ title: "", content: "", recipient_type: "all" });
  const [validation, setValidation] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => api.admin.createAnnouncement({ title: ann.title.trim(), content: ann.content.trim(), severity: ann.severity }),
    onSuccess: async () => {
      setNotice("Announcement published.");
      setAnn({ title: "", content: "", severity: "info" });
      await queryClient.invalidateQueries({ queryKey: ["announcements"] });
    },
  });
  const broadcast = useMutation({
    mutationFn: () => api.admin.broadcast({ title: bc.title.trim(), content: bc.content.trim(), recipient_type: bc.recipient_type }),
    onSuccess: () => {
      setNotice("Broadcast sent.");
      setBc({ title: "", content: "", recipient_type: "all" });
    },
  });

  const check = (title: string, content: string) => {
    if (!title.trim() || !content.trim()) {
      setValidation("Title and content are required.");
      return false;
    }
    setValidation(null);
    setNotice(null);
    return true;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-6">
        <SuccessBanner message={notice} />
        <ErrorBanner error={validation ?? create.error ?? broadcast.error} />
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Publish announcement</CardTitle>
            <CardDescription className="text-xs">Shown in every user&apos;s notification bell.</CardDescription>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-3"
              onSubmit={(e) => {
                e.preventDefault();
                if (check(ann.title, ann.content)) create.mutate();
              }}
            >
              <Input placeholder="Title" value={ann.title} onChange={(e) => setAnn({ ...ann, title: e.target.value })} />
              <Input placeholder="Content" value={ann.content} onChange={(e) => setAnn({ ...ann, content: e.target.value })} />
              <select className={`${selectClass} h-10 w-full`} value={ann.severity} onChange={(e) => setAnn({ ...ann, severity: e.target.value })}>
                {["info", "warning", "critical"].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
              <Button type="submit" isLoading={create.isPending}>
                Publish
              </Button>
            </form>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-bold">Broadcast notification</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="space-y-3"
              onSubmit={(e) => {
                e.preventDefault();
                if (check(bc.title, bc.content)) broadcast.mutate();
              }}
            >
              <Input placeholder="Title" value={bc.title} onChange={(e) => setBc({ ...bc, title: e.target.value })} />
              <Input placeholder="Content" value={bc.content} onChange={(e) => setBc({ ...bc, content: e.target.value })} />
              <select className={`${selectClass} h-10 w-full`} value={bc.recipient_type} onChange={(e) => setBc({ ...bc, recipient_type: e.target.value })}>
                {["all", "students", "recruiters", "officers"].map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
              <Button type="submit" isLoading={broadcast.isPending}>
                Send
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
      <Card className="self-start">
        <CardHeader>
          <CardTitle className="text-base font-bold">Active announcements</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {active.isLoading ? (
            <LoadingBlock />
          ) : active.error ? (
            <ErrorBanner error={active.error} onRetry={() => void active.refetch()} />
          ) : !active.data?.length ? (
            <p className="text-xs text-muted-foreground">Nothing active.</p>
          ) : (
            active.data.map((a) => (
              <div key={a.id} className="rounded-xl border border-border p-3 text-xs">
                <p className="font-semibold">
                  {a.title} <span className="text-muted-foreground font-normal">({a.severity})</span>
                </p>
                <p className="text-muted-foreground">{a.content}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function AiConfig() {
  const queryClient = useQueryClient();
  const providers = useQuery({ queryKey: ["admin-providers"], queryFn: api.admin.providers });
  const models = useQuery({ queryKey: ["admin-models"], queryFn: api.admin.models });
  const [prov, setProv] = React.useState({ name: "" });
  const [model, setModel] = React.useState({ provider_name: "", model_name: "" });
  const [prompt, setPrompt] = React.useState({ module: "", version: "", prompt_text: "" });
  const [versionsFor, setVersionsFor] = React.useState("");
  const [test, setTest] = React.useState({ provider_name: "", model_name: "", prompt_text: "" });
  const [validation, setValidation] = React.useState<string | null>(null);

  const versions = useQuery({
    queryKey: ["admin-prompt-versions", versionsFor],
    queryFn: () => api.admin.promptVersions(versionsFor),
    enabled: versionsFor.length > 0,
  });

  const createProvider = useMutation({
    mutationFn: () => api.admin.createProvider({ name: prov.name.trim() }),
    onSuccess: async () => {
      setProv({ name: "" });
      await queryClient.invalidateQueries({ queryKey: ["admin-providers"] });
    },
  });
  const toggleProvider = useMutation({
    mutationFn: (v: { name: string; active: boolean }) => api.admin.updateProvider(v.name, { is_active: v.active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-providers"] }),
  });
  const createModel = useMutation({
    mutationFn: () => api.admin.createModel({ provider_name: model.provider_name.trim(), model_name: model.model_name.trim() }),
    onSuccess: async () => {
      setModel({ provider_name: "", model_name: "" });
      await queryClient.invalidateQueries({ queryKey: ["admin-models"] });
    },
  });
  const toggleModel = useMutation({
    mutationFn: (v: { name: string; active: boolean }) => api.admin.updateModel(v.name, { is_active: v.active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-models"] }),
  });
  const createPrompt = useMutation({
    mutationFn: async () => {
      await api.admin.createPromptTemplate({ module: prompt.module.trim() }).catch(() => undefined); // template may already exist
      return api.admin.createPromptVersion({ module: prompt.module.trim(), version: prompt.version.trim(), prompt_text: prompt.prompt_text });
    },
    onSuccess: async () => {
      setVersionsFor(prompt.module.trim());
      setPrompt({ module: "", version: "", prompt_text: "" });
      await queryClient.invalidateQueries({ queryKey: ["admin-prompt-versions"] });
    },
  });
  const rollback = useMutation({
    mutationFn: (v: { module: string; version: string }) => api.admin.rollbackPrompt(v.module, v.version, v.version),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-prompt-versions"] }),
  });
  const runTest = useMutation({ mutationFn: () => api.admin.testProvider(test) });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <ErrorBanner
        className="lg:col-span-2"
        error={validation ?? providers.error ?? models.error ?? createProvider.error ?? toggleProvider.error ?? createModel.error ?? toggleModel.error ?? createPrompt.error ?? rollback.error ?? runTest.error}
      />
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">LLM providers</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {providers.isLoading ? (
            <LoadingBlock />
          ) : !providers.data?.length ? (
            <p className="text-xs text-muted-foreground">No providers configured.</p>
          ) : (
            providers.data.map((p) => (
              <div key={p.id} className="flex items-center justify-between rounded-xl border border-border p-3 text-xs">
                <span className="font-semibold">
                  {p.name} <span className="text-muted-foreground font-normal">priority {p.priority} • {p.provider_status}</span>
                </span>
                <Button size="sm" variant={p.is_active ? "default" : "outline"} disabled={toggleProvider.isPending} onClick={() => toggleProvider.mutate({ name: p.name, active: !p.is_active })}>
                  {p.is_active ? "Active" : "Inactive"}
                </Button>
              </div>
            ))
          )}
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!prov.name.trim()) return setValidation("Provider name is required.");
              setValidation(null);
              createProvider.mutate();
            }}
          >
            <Input className="h-9 text-xs" placeholder="Provider name" value={prov.name} onChange={(e) => setProv({ name: e.target.value })} />
            <Button type="submit" size="sm" isLoading={createProvider.isPending}>
              Add
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Model configurations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {models.isLoading ? (
            <LoadingBlock />
          ) : !models.data?.length ? (
            <p className="text-xs text-muted-foreground">No models configured.</p>
          ) : (
            models.data.map((m) => (
              <div key={m.id} className="flex items-center justify-between rounded-xl border border-border p-3 text-xs">
                <span className="font-semibold">
                  {m.model_name} <span className="text-muted-foreground font-normal">({m.provider_name}) temp {m.temperature}</span>
                </span>
                <Button size="sm" variant={m.is_active ? "default" : "outline"} disabled={toggleModel.isPending} onClick={() => toggleModel.mutate({ name: m.model_name, active: !m.is_active })}>
                  {m.is_active ? "Active" : "Inactive"}
                </Button>
              </div>
            ))
          )}
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!model.provider_name.trim() || !model.model_name.trim()) return setValidation("Provider and model name are required.");
              setValidation(null);
              createModel.mutate();
            }}
          >
            <Input className="h-9 text-xs" placeholder="Provider" value={model.provider_name} onChange={(e) => setModel({ ...model, provider_name: e.target.value })} />
            <Input className="h-9 text-xs" placeholder="Model" value={model.model_name} onChange={(e) => setModel({ ...model, model_name: e.target.value })} />
            <Button type="submit" size="sm" isLoading={createModel.isPending}>
              Add
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Prompt versions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <form
            className="space-y-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!prompt.module.trim() || !prompt.version.trim() || !prompt.prompt_text.trim()) return setValidation("Module, version and prompt text are required.");
              setValidation(null);
              createPrompt.mutate();
            }}
          >
            <div className="flex gap-2">
              <Input className="h-9 text-xs" placeholder="Module (e.g. mentor)" value={prompt.module} onChange={(e) => setPrompt({ ...prompt, module: e.target.value })} />
              <Input className="h-9 text-xs w-28" placeholder="Version" value={prompt.version} onChange={(e) => setPrompt({ ...prompt, version: e.target.value })} />
            </div>
            <textarea rows={3} className="w-full rounded-md border border-input bg-background/50 px-3 py-2 text-xs" placeholder="Prompt text" value={prompt.prompt_text} onChange={(e) => setPrompt({ ...prompt, prompt_text: e.target.value })} />
            <Button type="submit" size="sm" isLoading={createPrompt.isPending}>
              Save version
            </Button>
          </form>
          <div className="flex gap-2 border-t border-border pt-3">
            <Input className="h-9 text-xs" placeholder="Module to inspect" value={versionsFor} onChange={(e) => setVersionsFor(e.target.value.trim())} />
          </div>
          {versionsFor && (versions.isLoading ? <LoadingBlock /> : versions.error ? <ErrorBanner error={versions.error} /> : !versions.data?.length ? (
            <p className="text-xs text-muted-foreground">No versions for this module.</p>
          ) : (
            versions.data.map((v) => (
              <div key={v.id} className="flex items-center justify-between rounded-xl border border-border p-3 text-xs">
                <span>
                  v{v.version} {v.is_active && <span className="text-emerald-500 font-semibold">(active)</span>}
                </span>
                {!v.is_active && (
                  <Button size="sm" variant="outline" disabled={rollback.isPending} onClick={() => rollback.mutate({ module: v.module, version: v.version })}>
                    Roll back to this
                  </Button>
                )}
              </div>
            ))
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Test a provider</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <form
            className="space-y-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!test.provider_name.trim() || !test.model_name.trim() || !test.prompt_text.trim()) return setValidation("Provider, model and prompt are required to run a test.");
              setValidation(null);
              runTest.mutate();
            }}
          >
            <div className="flex gap-2">
              <Input className="h-9 text-xs" placeholder="Provider" value={test.provider_name} onChange={(e) => setTest({ ...test, provider_name: e.target.value })} />
              <Input className="h-9 text-xs" placeholder="Model" value={test.model_name} onChange={(e) => setTest({ ...test, model_name: e.target.value })} />
            </div>
            <textarea rows={2} className="w-full rounded-md border border-input bg-background/50 px-3 py-2 text-xs" placeholder="Prompt" value={test.prompt_text} onChange={(e) => setTest({ ...test, prompt_text: e.target.value })} />
            <Button type="submit" size="sm" isLoading={runTest.isPending}>
              Run test
            </Button>
          </form>
          {runTest.data && (
            <div className="rounded-xl bg-muted/40 p-3 text-xs space-y-1">
              <p>
                <span className="font-semibold">{runTest.data.status}</span> • {runTest.data.latency_ms} ms • {runTest.data.tokens_used} tokens
              </p>
              <p className="text-muted-foreground whitespace-pre-wrap">{runTest.data.response_text}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Monitoring() {
  const queryClient = useQueryClient();
  const audit = useQuery({ queryKey: ["admin-audit"], queryFn: () => api.admin.auditLogs(30) });
  const jobs = useQuery({ queryKey: ["admin-jobs"], queryFn: () => api.admin.backgroundJobs(20) });
  const resources = useQuery({ queryKey: ["admin-resources"], queryFn: api.admin.resources });
  const maintenance = useQuery({ queryKey: ["admin-maintenance"], queryFn: api.admin.maintenanceStatus });
  const [win, setWin] = React.useState({ start_time: "", end_time: "", description: "" });
  const [validation, setValidation] = React.useState<string | null>(null);

  const schedule = useMutation({
    mutationFn: () =>
      api.admin.scheduleMaintenance({
        start_time: new Date(win.start_time).toISOString(),
        end_time: new Date(win.end_time).toISOString(),
        description: win.description.trim() || undefined,
      }),
    onSuccess: async () => {
      setWin({ start_time: "", end_time: "", description: "" });
      await queryClient.invalidateQueries({ queryKey: ["admin-maintenance"] });
    },
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Resources</CardTitle>
        </CardHeader>
        <CardContent>{resources.isLoading ? <LoadingBlock /> : resources.error ? <ErrorBanner error={resources.error} onRetry={() => void resources.refetch()} /> : <JsonView value={resources.data} />}</CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Maintenance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {maintenance.error ? <ErrorBanner error={maintenance.error} /> : <JsonView value={maintenance.data} />}
          <ErrorBanner error={validation ?? schedule.error} />
          <form
            className="space-y-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (!win.start_time || !win.end_time) return setValidation("Choose a start and end time.");
              if (new Date(win.end_time) <= new Date(win.start_time)) return setValidation("The end time must be after the start time.");
              setValidation(null);
              schedule.mutate();
            }}
          >
            <div className="flex gap-2">
              <Input type="datetime-local" className="h-9 text-xs" value={win.start_time} onChange={(e) => setWin({ ...win, start_time: e.target.value })} />
              <Input type="datetime-local" className="h-9 text-xs" value={win.end_time} onChange={(e) => setWin({ ...win, end_time: e.target.value })} />
            </div>
            <Input className="h-9 text-xs" placeholder="Description" value={win.description} onChange={(e) => setWin({ ...win, description: e.target.value })} />
            <Button type="submit" size="sm" isLoading={schedule.isPending}>
              Schedule maintenance
            </Button>
          </form>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Background jobs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {jobs.isLoading ? <LoadingBlock /> : jobs.error ? <ErrorBanner error={jobs.error} onRetry={() => void jobs.refetch()} /> : !jobs.data?.length ? <p className="text-xs text-muted-foreground">No job history.</p> : jobs.data.map((j) => (
            <div key={j.id} className="flex justify-between rounded-xl border border-border p-3 text-xs">
              <span className="font-semibold">{j.job_name}</span>
              <span className="text-muted-foreground">{j.status}</span>
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-bold">Audit log</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {audit.isLoading ? <LoadingBlock /> : audit.error ? <ErrorBanner error={audit.error} onRetry={() => void audit.refetch()} /> : !audit.data?.length ? <p className="text-xs text-muted-foreground">No audit entries yet.</p> : audit.data.map((l) => (
            <div key={l.id} className="rounded-xl border border-border p-3 text-xs">
              <p className="font-semibold">{l.action}</p>
              <p className="text-muted-foreground">
                {l.target_type ?? "—"} {l.target_id ? `• ${l.target_id.slice(0, 8)}` : ""} • {new Date(l.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

const SECTION_TAB: Record<string, string> = {
  users: "users",
  recruiters: "users",
  "community-moderation": "moderation",
  settings: "config",
  "ai-models-placeholder": "ai",
  "system-monitoring": "monitoring",
  "audit-logs": "monitoring",
};

export function AdminPortal({ section }: { section?: string }) {
  const [tab, setTab] = React.useState(SECTION_TAB[section ?? ""] ?? "overview");

  return (
    <div className="space-y-6 text-left">
      <div>
        <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">Platform Administration</span>
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
          <ShieldCheck className="h-7 w-7 text-primary" /> Admin Console
        </h1>
        <p className="text-sm text-muted-foreground">Users, moderation, configuration, AI providers, and system health.</p>
      </div>
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="mb-4 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30">
          <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
          <TabsTrigger value="users" className="text-xs">Users</TabsTrigger>
          <TabsTrigger value="moderation" className="text-xs">Moderation</TabsTrigger>
          <TabsTrigger value="config" className="text-xs">Flags &amp; Settings</TabsTrigger>
          <TabsTrigger value="announcements" className="text-xs">Announcements</TabsTrigger>
          <TabsTrigger value="ai" className="text-xs">AI Config</TabsTrigger>
          <TabsTrigger value="monitoring" className="text-xs">Monitoring</TabsTrigger>
        </TabsList>
        <TabsContent value="overview"><Overview /></TabsContent>
        <TabsContent value="users"><Users /></TabsContent>
        <TabsContent value="moderation"><Moderation /></TabsContent>
        <TabsContent value="config"><Configuration /></TabsContent>
        <TabsContent value="announcements"><Announcements /></TabsContent>
        <TabsContent value="ai"><AiConfig /></TabsContent>
        <TabsContent value="monitoring"><Monitoring /></TabsContent>
      </Tabs>
    </div>
  );
}
