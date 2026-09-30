"use client";

import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { GraduationCap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState, ErrorBanner, LoadingBlock, SuccessBanner } from "@/components/ui/feedback";
import { api, DriveRegistration, PlacementDrive } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

const DOMAIN_RE = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/i;
const DRIVE_TYPES = ["Campus", "Virtual", "Off-Campus", "Internship"];
const REGISTRATION_STATUSES = ["Registered", "Shortlisted", "Interviewing", "Offered", "Rejected"];
const selectClass = "flex h-9 rounded-md border border-input bg-background px-2 text-xs";

function CollegeSetup() {
  const refreshUser = useAuthStore((s) => s.refreshUser);
  const [form, setForm] = React.useState({ name: "", domain: "", address: "" });
  const [validation, setValidation] = React.useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => api.createCollege({ name: form.name.trim(), domain: form.domain.trim().toLowerCase(), address: form.address.trim() || undefined }),
    onSuccess: () => refreshUser(),
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return setValidation("College name is required.");
    if (!DOMAIN_RE.test(form.domain.trim())) return setValidation("Enter a valid college domain, e.g. university.edu.");
    setValidation(null);
    create.mutate();
  };

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle className="text-base font-bold flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-primary" /> Register your college
        </CardTitle>
        <CardDescription className="text-xs">Create your college profile to run placement drives.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-3">
          <ErrorBanner error={validation ?? create.error} />
          <Input placeholder="College name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="Domain (university.edu)" value={form.domain} onChange={(e) => setForm({ ...form, domain: e.target.value })} />
          <Input placeholder="Address (optional)" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <Button type="submit" className="w-full" isLoading={create.isPending}>
            Register college
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function CreateDrive() {
  const queryClient = useQueryClient();
  const [form, setForm] = React.useState({ title: "", description: "", drive_type: DRIVE_TYPES[0], date: "", minCgpa: "" });
  const [validation, setValidation] = React.useState<string | null>(null);
  const [notice, setNotice] = React.useState<string | null>(null);

  const create = useMutation({
    mutationFn: () =>
      api.createDrive({
        title: form.title.trim(),
        description: form.description.trim() || undefined,
        drive_type: form.drive_type,
        date_of_drive: form.date || undefined,
        requirements: form.minCgpa ? { min_cgpa: Number(form.minCgpa) } : undefined,
      }),
    onSuccess: async (drive) => {
      setNotice(`Drive "${drive.title}" created.`);
      setForm({ title: "", description: "", drive_type: DRIVE_TYPES[0], date: "", minCgpa: "" });
      await queryClient.invalidateQueries({ queryKey: ["college-drives"] });
    },
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setNotice(null);
    if (!form.title.trim()) return setValidation("Give the drive a title.");
    if (form.minCgpa && (Number.isNaN(Number(form.minCgpa)) || Number(form.minCgpa) < 0 || Number(form.minCgpa) > 10)) {
      return setValidation("Minimum CGPA must be a number between 0 and 10.");
    }
    setValidation(null);
    create.mutate();
  };

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle className="text-base font-bold">Create a placement drive</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="space-y-3">
          <SuccessBanner message={notice} />
          <ErrorBanner error={validation ?? create.error} />
          <Input placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <Input placeholder="Description (optional)" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <div className="grid grid-cols-2 gap-3">
            <select className={`${selectClass} h-10`} value={form.drive_type} onChange={(e) => setForm({ ...form, drive_type: e.target.value })}>
              {DRIVE_TYPES.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
            <Input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
          </div>
          <Input placeholder="Minimum CGPA (optional)" value={form.minCgpa} onChange={(e) => setForm({ ...form, minCgpa: e.target.value })} />
          <Button type="submit" isLoading={create.isPending}>
            Create drive
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function DriveDetail({ drive }: { drive: PlacementDrive }) {
  const queryClient = useQueryClient();
  const [notice, setNotice] = React.useState<string | null>(null);
  const [offers, setOffers] = React.useState<Record<string, string>>({});
  const [validation, setValidation] = React.useState<string | null>(null);

  const registrations = useQuery({ queryKey: ["drive-registrations", drive.id], queryFn: () => api.driveRegistrations(drive.id) });
  // Fresh copy of the drive (GET /placements/drives/{id}) so the panel shows its current details.
  const detail = useQuery({ queryKey: ["drive", drive.id], queryFn: () => api.getDrive(drive.id) });
  const current = detail.data ?? drive;

  const setStatus = useMutation({
    mutationFn: (v: { id: string; status: string }) => api.updateRegistrationStatus(v.id, v.status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["drive-registrations", drive.id] }),
  });

  const offer = useMutation({
    mutationFn: (v: { id: string; details: string }) => api.releaseOffer(v.id, v.details),
    onSuccess: async () => {
      setNotice("Offer released.");
      await queryClient.invalidateQueries({ queryKey: ["drive-registrations", drive.id] });
    },
  });

  const eligibility = useMutation({ mutationFn: () => api.calculateEligibility(drive.id), onSuccess: (r) => setNotice(r.message ?? "Eligibility calculation started.") });
  const rank = useMutation({ mutationFn: () => api.rankStudents(drive.id), onSuccess: (r) => setNotice(r.message ?? "Ranking started.") });

  const releaseOffer = (reg: DriveRegistration) => {
    const details = (offers[reg.id] ?? "").trim();
    if (!details) return setValidation("Enter the package details (e.g. 12 LPA) before releasing an offer.");
    setValidation(null);
    offer.mutate({ id: reg.id, details });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-bold">{drive.title}</CardTitle>
        <CardDescription className="text-xs">
          {drive.drive_type} • {drive.status}
          {drive.date_of_drive ? ` • ${new Date(drive.date_of_drive).toLocaleDateString()}` : ""}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {current.description && <p className="text-xs text-muted-foreground">{current.description}</p>}
        {current.requirements && Object.keys(current.requirements).length > 0 && (
          <p className="text-xs text-muted-foreground">
            Requirements:{" "}
            {Object.entries(current.requirements)
              .map(([k, v]) => `${k.replace(/_/g, " ")}: ${String(v)}`)
              .join(", ")}
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" isLoading={eligibility.isPending} onClick={() => eligibility.mutate()}>
            Calculate eligibility
          </Button>
          <Button size="sm" variant="outline" isLoading={rank.isPending} onClick={() => rank.mutate()}>
            Rank students
          </Button>
        </div>
        <SuccessBanner message={notice} />
        <ErrorBanner error={validation ?? eligibility.error ?? rank.error ?? setStatus.error ?? offer.error} />

        {registrations.isLoading ? (
          <LoadingBlock label="Loading registrations…" />
        ) : registrations.error ? (
          <ErrorBanner error={registrations.error} onRetry={() => void registrations.refetch()} />
        ) : !registrations.data?.length ? (
          <EmptyState title="No registrations yet" description="Students who register for this drive will appear here." />
        ) : (
          registrations.data.map((reg) => (
            <div key={reg.id} className="rounded-xl border border-border p-3 space-y-2">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-semibold">Student {reg.student_id.slice(0, 8)}</p>
                <select
                  className={selectClass}
                  value={reg.status}
                  disabled={setStatus.isPending}
                  aria-label="Registration status"
                  onChange={(e) => setStatus.mutate({ id: reg.id, status: e.target.value })}
                >
                  {[...new Set([reg.status, ...REGISTRATION_STATUSES])].map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </div>
              {reg.status === "Offered" && (
                <div className="flex gap-2">
                  <Input
                    className="h-8 text-xs"
                    placeholder="Package details, e.g. 12 LPA"
                    value={offers[reg.id] ?? ""}
                    onChange={(e) => setOffers({ ...offers, [reg.id]: e.target.value })}
                  />
                  <Button size="sm" isLoading={offer.isPending && offer.variables?.id === reg.id} onClick={() => releaseOffer(reg)}>
                    Release offer
                  </Button>
                </div>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

export function OfficerPortal() {
  const user = useAuthStore((s) => s.user);
  const [tab, setTab] = React.useState("drives");
  const [driveId, setDriveId] = React.useState<string | null>(null);

  const hasCollege = Boolean(user?.collegeId);
  const drives = useQuery({ queryKey: ["college-drives"], queryFn: api.collegeDrives, enabled: hasCollege });
  const selected = drives.data?.find((d) => d.id === driveId);

  return (
    <div className="space-y-6 text-left">
      <div>
        <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">Placement Officer Workspace</span>
        <h1 className="text-3xl font-extrabold tracking-tight">Placement Office</h1>
        <p className="text-sm text-muted-foreground">Run placement drives, manage registrations, and release offers.</p>
      </div>

      {!hasCollege ? (
        <CollegeSetup />
      ) : (
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="mb-4 flex h-auto flex-wrap justify-start gap-1 p-1 bg-muted/30">
            <TabsTrigger value="drives" className="text-xs">Drives</TabsTrigger>
            <TabsTrigger value="create" className="text-xs">New Drive</TabsTrigger>
          </TabsList>
          <TabsContent value="drives" className="space-y-4">
            {drives.isLoading ? (
              <LoadingBlock />
            ) : drives.error ? (
              <ErrorBanner error={drives.error} onRetry={() => void drives.refetch()} />
            ) : !drives.data?.length ? (
              <EmptyState title="No drives yet" description="Create your first placement drive." />
            ) : (
              <>
                <select className={`${selectClass} h-10 w-full max-w-md`} value={driveId ?? ""} onChange={(e) => setDriveId(e.target.value)} aria-label="Select drive">
                  <option value="" disabled>
                    Select a drive…
                  </option>
                  {drives.data.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.title} ({d.status})
                    </option>
                  ))}
                </select>
                {selected ? <DriveDetail key={selected.id} drive={selected} /> : <EmptyState title="Choose a drive" description="Select a drive to manage its registrations." />}
              </>
            )}
          </TabsContent>
          <TabsContent value="create">
            <CreateDrive />
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
