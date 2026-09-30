"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import { HOME_PATH, useAuthStore, UserRole } from "@/store/useAuthStore";
import { Sidebar } from "@/components/ui/sidebar";
import { TopNav } from "@/components/ui/top-nav";
import { FloatingMentor } from "@/features/mentor/components/floating-mentor";

/** Portals only their own role may open (the backend enforces the same rules). */
const PORTAL_ROLE: Record<string, UserRole> = {
  "/recruiter": "recruiter",
  "/officer": "officer",
  "/admin": "admin",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isAuthenticated, isInitializing, init } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  // Restore the session from stored tokens on first load.
  React.useEffect(() => {
    if (isInitializing) void init();
  }, [isInitializing, init]);

  const portal = Object.keys(PORTAL_ROLE).find((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
  const forbidden = Boolean(user && portal && PORTAL_ROLE[portal] !== user.role);

  React.useEffect(() => {
    if (isInitializing) return;
    if (!isAuthenticated) router.replace("/login");
    else if (forbidden && user) router.replace(HOME_PATH[user.role]);
  }, [isInitializing, isAuthenticated, forbidden, user, router]);

  if (isInitializing || !isAuthenticated || forbidden) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-foreground">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm font-medium">Securing session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-full bg-background text-foreground font-sans overflow-x-hidden transition-colors duration-200">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Panel */}
      <div className="flex-1 flex flex-col min-h-screen relative overflow-x-hidden">
        {/* Top Header */}
        <TopNav />

        {/* Dynamic Main Body Content */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl w-full mx-auto pb-24">
          {children}
        </main>

        {/* AI Career Mentor Widget */}
        <FloatingMentor />
      </div>
    </div>
  );
}
