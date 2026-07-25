"use client";

import React from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { Sidebar } from "@/components/ui/sidebar";
import { TopNav } from "@/components/ui/top-nav";
import { FloatingMentor } from "@/features/mentor/components/floating-mentor";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated } = useAuthStore();

  React.useEffect(() => {
    // If not authenticated, redirect to login page
    if (!isAuthenticated) {
      window.location.href = "/login";
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
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
