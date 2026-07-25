"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/useAuthStore";
import { useTheme } from "@/contexts/ThemeContext";
import {
  User,
  Bell,
  Sun,
  Moon,
  Laptop,
  Globe,
  CheckCircle,
  Eye,
  Key,
  Info,
  HelpCircle,
  Users,
  Settings as SettingsIcon,
  Lock,
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const { user, updateUser } = useAuthStore();
  const { theme, setTheme } = useTheme();

  const [activeTab, setActiveTab] = React.useState("profile");
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);
  const [profileForm, setProfileForm] = React.useState({
    name: "",
    email: "",
    phone: "+1 (555) 382-9020",
  });

  // Notifications state
  const [notifJobs, setNotifJobs] = React.useState(true);
  const [notifInterviews, setNotifInterviews] = React.useState(true);
  const [notifLearning, setNotifLearning] = React.useState(false);

  // Active Sessions Mock Data
  const [sessions, setSessions] = React.useState([
    { id: "sess-1", device: "Chrome on Windows 11 (This Device)", location: "San Francisco, CA", active: "Active Now", current: true },
    { id: "sess-2", device: "Safari on iPhone 15 Pro", location: "San Jose, CA", active: "2 hours ago", current: false },
    { id: "sess-3", device: "Microsoft Edge on Windows Server", location: "Seattle, WA", active: "3 days ago", current: false },
  ]);

  const triggerSaveAlert = (message: string) => {
    setSuccessMsg(message);
    setTimeout(() => setSuccessMsg(null), 3000);
  };

  const terminateSession = (id: string) => {
    setSessions(sessions.filter((s) => s.id !== id));
    triggerSaveAlert("Session terminated successfully.");
  };

  React.useEffect(() => {
    if (user) {
      setProfileForm((current) => ({
        ...current,
        name: user.name,
        email: user.email,
      }));
    }
  }, [user]);

  const handleProfileSave = async () => {
    try {
      await updateUser({
        name: profileForm.name.trim(),
        email: profileForm.email.trim(),
      });
      triggerSaveAlert("Profile contact information updated.");
    } catch {
      triggerSaveAlert("Unable to sync profile with backend. Please try again.");
    }
  };

  if (!user) return null;

  // Settings tabs configuration
  const tabs = [
    { id: "profile", label: "Profile", icon: User },
    { id: "account", label: "Account", icon: SettingsIcon },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "privacy", label: "Privacy", icon: Eye },
    { id: "security", label: "Security", icon: Lock },
    { id: "theme", label: "Theme", icon: Sun },
    { id: "language", label: "Language", icon: Globe },
    { id: "community", label: "Community", icon: Users },
    { id: "help", label: "Help Center", icon: HelpCircle },
    { id: "about", label: "About", icon: Info },
  ];

  return (
    <div className="space-y-8 text-left max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Configure security credentials, notification pathways, interface languages, and visual settings.
        </p>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-xl flex items-center gap-2 max-w-4xl">
          <CheckCircle className="h-4.5 w-4.5 shrink-0" /> <span>{successMsg}</span>
        </div>
      )}

      {/* Main split layout: Left side list, Right side details */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
        {/* Left Side Tab Navigation */}
        <div className="md:col-span-3 space-y-1 bg-card/25 dark:bg-slate-950/20 p-2.5 rounded-xl border border-border">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold text-left transition-all cursor-pointer",
                  isActive
                    ? "bg-primary/10 text-primary border-l-2 border-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Right Side Settings Panel Details */}
        <div className="md:col-span-9">
          {/* PROFILE */}
          {activeTab === "profile" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <User className="h-4.5 w-4.5 text-primary" /> Profile Settings
                </CardTitle>
                <CardDescription className="text-xs">Update your primary registration contact fields.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase">Full Name</label>
                    <Input
                      type="text"
                      value={profileForm.name}
                      onChange={(event) => setProfileForm((current) => ({ ...current, name: event.target.value }))}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase">Email Address</label>
                    <Input
                      type="email"
                      value={profileForm.email}
                      onChange={(event) => setProfileForm((current) => ({ ...current, email: event.target.value }))}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase">Telephone Contact</label>
                    <Input
                      type="tel"
                      value={profileForm.phone}
                      onChange={(event) => setProfileForm((current) => ({ ...current, phone: event.target.value }))}
                    />
                  </div>
                </div>
              </CardContent>
              <CardFooter className="justify-end border-t border-border pt-4">
                <Button onClick={handleProfileSave} className="cursor-pointer">
                  Save Profile
                </Button>
              </CardFooter>
            </Card>
          )}

          {/* ACCOUNT */}
          {activeTab === "account" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <SettingsIcon className="h-4.5 w-4.5 text-primary" /> Account Details
                </CardTitle>
                <CardDescription className="text-xs">Manage system designations, roles, and zones.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase">Active Role Type</label>
                    <Input type="text" defaultValue={user.role} disabled className="opacity-60 bg-muted/20 capitalize font-bold" />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase">Target Timezone</label>
                    <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm text-foreground focus:outline-hidden focus:ring-2 focus:ring-ring transition-all">
                      <option className="bg-background text-foreground">GMT-08:00 (Pacific Time)</option>
                      <option className="bg-background text-foreground">GMT-05:00 (Eastern Time)</option>
                      <option className="bg-background text-foreground">GMT+05:30 (India Standard Time)</option>
                    </select>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="justify-end border-t border-border pt-4">
                <Button onClick={() => triggerSaveAlert("Account specifications updated.")} className="cursor-pointer">
                  Save Changes
                </Button>
              </CardFooter>
            </Card>
          )}

          {/* NOTIFICATIONS */}
          {activeTab === "notifications" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Bell className="h-4.5 w-4.5 text-primary" /> Notification Pathways
                </CardTitle>
                <CardDescription className="text-xs">Configure how matched jobs, lesson streaks, and calendar alarms are delivered.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="space-y-3">
                  <div className="flex items-start space-x-3 p-3 bg-muted/40 rounded-xl border border-muted">
                    <input
                      type="checkbox"
                      id="notifJobs"
                      checked={notifJobs}
                      onChange={(e) => setNotifJobs(e.target.checked)}
                      className="h-4 w-4 rounded-sm border-input bg-background/50 text-primary cursor-pointer mt-0.5"
                    />
                    <div className="text-left space-y-0.5">
                      <label htmlFor="notifJobs" className="font-semibold text-foreground cursor-pointer">Job Matching Alarms</label>
                      <p className="text-[10px] text-muted-foreground">Receive instant alerts when matched roles score compatibility indexes over 85%.</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 p-3 bg-muted/40 rounded-xl border border-muted">
                    <input
                      type="checkbox"
                      id="notifInterviews"
                      checked={notifInterviews}
                      onChange={(e) => setNotifInterviews(e.target.checked)}
                      className="h-4 w-4 rounded-sm border-input bg-background/50 text-primary cursor-pointer mt-0.5"
                    />
                    <div className="text-left space-y-0.5">
                      <label htmlFor="notifInterviews" className="font-semibold text-foreground cursor-pointer">Interview & Mock Reminders</label>
                      <p className="text-[10px] text-muted-foreground">Receive upcoming simulation calendars or scheduled recruiter screens.</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 p-3 bg-muted/40 rounded-xl border border-muted">
                    <input
                      type="checkbox"
                      id="notifLearning"
                      checked={notifLearning}
                      onChange={(e) => setNotifLearning(e.target.checked)}
                      className="h-4 w-4 rounded-sm border-input bg-background/50 text-primary cursor-pointer mt-0.5"
                    />
                    <div className="text-left space-y-0.5">
                      <label htmlFor="notifLearning" className="font-semibold text-foreground cursor-pointer">Learning Streak Notifications</label>
                      <p className="text-[10px] text-muted-foreground">Receive summary emails outlining weekly completed courses or achievements.</p>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="justify-end border-t border-border pt-4">
                <Button onClick={() => triggerSaveAlert("Notification options updated successfully.")} className="cursor-pointer">
                  Save Preferences
                </Button>
              </CardFooter>
            </Card>
          )}

          {/* PRIVACY */}
          {activeTab === "privacy" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Eye className="h-4.5 w-4.5 text-primary" /> Privacy Safeguards
                </CardTitle>
                <CardDescription className="text-xs">Control public placement flags and data permissions.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="space-y-3">
                  <div className="flex items-start space-x-3 p-3 bg-muted/40 rounded-xl border border-muted">
                    <input type="checkbox" id="profileVisibility" defaultChecked className="h-4 w-4 rounded-sm border-input bg-background/50 text-primary cursor-pointer mt-0.5" />
                    <div className="text-left space-y-0.5">
                      <label htmlFor="profileVisibility" className="font-semibold text-foreground cursor-pointer">Recruiter Directory Visibility</label>
                      <p className="text-[10px] text-muted-foreground">Allow verified corporate recruitment accounts to query and view your compatibility indexes.</p>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 p-3 bg-muted/40 rounded-xl border border-muted">
                    <input type="checkbox" id="anonymousCommunity" defaultChecked className="h-4 w-4 rounded-sm border-input bg-background/50 text-primary cursor-pointer mt-0.5" />
                    <div className="text-left space-y-0.5">
                      <label htmlFor="anonymousCommunity" className="font-semibold text-foreground cursor-pointer">Anonymous Forum Posting</label>
                      <p className="text-[10px] text-muted-foreground">Enable auto-masking username strings when submitting comments inside community discussion categories.</p>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="justify-end border-t border-border pt-4">
                <Button onClick={() => triggerSaveAlert("Privacy settings updated.")} className="cursor-pointer">
                  Save Preferences
                </Button>
              </CardFooter>
            </Card>
          )}

          {/* SECURITY */}
          {activeTab === "security" && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold flex items-center gap-2">
                    <Key className="h-4.5 w-4.5 text-primary" /> Reset Credentials
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-xs">
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase">Current Password</label>
                    <Input type="password" placeholder="••••••••" />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-semibold text-muted-foreground uppercase">New Password</label>
                    <Input type="password" placeholder="••••••••" />
                  </div>
                </CardContent>
                <CardFooter className="justify-end border-t border-border pt-4">
                  <Button onClick={() => triggerSaveAlert("Password changed successfully.")} className="cursor-pointer">
                    Update Password
                  </Button>
                </CardFooter>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base font-bold flex items-center gap-2">
                    <Laptop className="h-4.5 w-4.5 text-primary" /> Active Sessions
                  </CardTitle>
                  <CardDescription className="text-xs">Logged-in devices currently accessing CareerOS.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-xs text-left">
                  {sessions.map((sess) => (
                    <div key={sess.id} className="p-3.5 border border-muted bg-muted/30 rounded-xl flex items-center justify-between">
                      <div className="space-y-0.5">
                        <p className="font-semibold text-foreground">{sess.device}</p>
                        <p className="text-[10px] text-muted-foreground">{sess.location} • {sess.active}</p>
                      </div>
                      {!sess.current && (
                        <button
                          onClick={() => terminateSession(sess.id)}
                          className="text-[10px] text-destructive hover:underline cursor-pointer font-semibold"
                        >
                          Revoke
                        </button>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          )}

          {/* THEME */}
          {activeTab === "theme" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Sun className="h-4.5 w-4.5 text-primary" /> Theme Configuration
                </CardTitle>
                <CardDescription className="text-xs">Select site visualization layout configurations.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-3 text-xs">
                <button
                  onClick={() => { setTheme("dark"); triggerSaveAlert("Dark mode activated."); }}
                  className={cn(
                    "flex flex-col items-center gap-2 p-4 border rounded-xl transition-all cursor-pointer",
                    theme === "dark" ? "bg-primary/10 border-primary text-foreground" : "bg-card border-border hover:bg-muted text-muted-foreground"
                  )}
                >
                  <Moon className="h-5 w-5" />
                  <span className="font-semibold">Dark Theme</span>
                </button>
                <button
                  onClick={() => { setTheme("light"); triggerSaveAlert("Light mode activated."); }}
                  className={cn(
                    "flex flex-col items-center gap-2 p-4 border rounded-xl transition-all cursor-pointer",
                    theme === "light" ? "bg-primary/10 border-primary text-foreground" : "bg-card border-border hover:bg-muted text-muted-foreground"
                  )}
                >
                  <Sun className="h-5 w-5" />
                  <span className="font-semibold">Light Theme</span>
                </button>
              </CardContent>
            </Card>
          )}

          {/* LANGUAGE */}
          {activeTab === "language" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Globe className="h-4.5 w-4.5 text-primary" /> Site Languages
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-left">
                <label className="text-[10px] font-semibold text-muted-foreground uppercase">Primary Translation Locale</label>
                <select className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm text-foreground focus:outline-hidden focus:ring-2 focus:ring-ring transition-all">
                  <option className="bg-background text-foreground">English (United States)</option>
                  <option className="bg-background text-foreground">Español (España)</option>
                  <option className="bg-background text-foreground">Français (France)</option>
                </select>
              </CardContent>
              <CardFooter className="justify-end border-t border-border pt-4">
                <Button onClick={() => triggerSaveAlert("Language preferences updated.")} className="cursor-pointer">
                  Save Language
                </Button>
              </CardFooter>
            </Card>
          )}

          {/* COMMUNITY */}
          {activeTab === "community" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Users className="h-4.5 w-4.5 text-primary" /> Community Settings
                </CardTitle>
                <CardDescription className="text-xs">Configure notifications and content filters for community discussions.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="space-y-3">
                  <div className="flex items-start space-x-3 p-3 bg-muted/40 rounded-xl border border-muted">
                    <input type="checkbox" id="commNotifs" defaultChecked className="h-4 w-4 rounded-sm border-input bg-background/50 text-primary cursor-pointer mt-0.5" />
                    <div className="text-left space-y-0.5">
                      <label htmlFor="commNotifs" className="font-semibold text-foreground cursor-pointer">Replies & Mention Notifications</label>
                      <p className="text-[10px] text-muted-foreground">Receive instant panel updates when replies are logged under your interview experiences.</p>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="justify-end border-t border-border pt-4">
                <Button onClick={() => triggerSaveAlert("Community options updated.")} className="cursor-pointer">
                  Save Settings
                </Button>
              </CardFooter>
            </Card>
          )}

          {/* HELP CENTER */}
          {activeTab === "help" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <HelpCircle className="h-4.5 w-4.5 text-primary" /> Help & Support
                </CardTitle>
                <CardDescription className="text-xs">Access tutorials or submit questions to the placement office.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-4 border border-border bg-muted/20 rounded-xl space-y-1 text-left">
                    <p className="font-bold text-foreground">Interactive User Guides</p>
                    <p className="text-[10px] text-muted-foreground leading-relaxed">Read tutorial docs on setting up mock interviews and checking ATS ratings.</p>
                  </div>
                  <div className="p-4 border border-border bg-muted/20 rounded-xl space-y-1 text-left">
                    <p className="font-bold text-foreground">Support Ticket Desk</p>
                    <p className="text-[10px] text-muted-foreground leading-relaxed">Submit a message to our developers regarding placement drive issues.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ABOUT */}
          {activeTab === "about" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Info className="h-4.5 w-4.5 text-primary" /> About Platform
                </CardTitle>
                <CardDescription className="text-xs">Version control and platform license details.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs text-left leading-relaxed">
                <div className="p-4 border border-border bg-muted/20 rounded-xl space-y-2">
                  <p className="font-bold text-foreground">CareerOS AI Suite</p>
                  <p className="text-[10px] text-muted-foreground">Version: **v1.4.2-turbopack**</p>
                  <p className="text-[10px] text-muted-foreground">Framework: **Next.js 15.5, React 19.1, Tailwind CSS v4.0**</p>
                </div>
                <p className="text-[10px] text-muted-foreground px-1">
                  © 2026 CareerOS AI. All rights reserved. Platform operates under placement board licensing guidelines.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
