"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore, UserRole } from "@/store/useAuthStore";
import {
  LayoutDashboard,
  Briefcase,
  Settings,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Sparkles,
  BarChart3,
  Rocket,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

export function Sidebar() {
  const pathname = usePathname();
  const { user, switchRole, logout } = useAuthStore();
  const [isCollapsed, setIsCollapsed] = React.useState(false);
  const [isMobileOpen, setIsMobileOpen] = React.useState(false);

  if (!user) return null;

  const getNavLinks = (role: UserRole) => {
    const dashboardMap = {
      student: "/student",
      recruiter: "/recruiter",
      officer: "/officer",
      admin: "/admin",
    };

    return [
      { href: dashboardMap[role] || "/student", label: "Dashboard", icon: LayoutDashboard },
      { href: "/workspace", label: "Workspace", icon: Rocket },
      { href: "/jobs", label: "Jobs", icon: Briefcase },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/settings", label: "Settings", icon: Settings },
    ];
  };

  const navLinks = getNavLinks(user.role);

  const toggleMobile = () => setIsMobileOpen(!isMobileOpen);

  const sidebarContent = (
    <div className="flex flex-col h-full bg-card dark:bg-slate-950 text-foreground border-r border-border p-4 transition-all duration-300">
      {/* Brand Header */}
      <div className="flex items-center justify-between mb-8">
        <Link href="/" className="flex items-center space-x-2">
          <div className="p-2 bg-gradient-to-tr from-indigo-500 to-violet-500 rounded-lg text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          {!isCollapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-bold text-lg bg-gradient-to-r from-indigo-500 to-violet-500 bg-clip-text text-transparent"
            >
              CareerOS AI
            </motion.span>
          )}
        </Link>
        {isMobileOpen && (
          <button onClick={toggleMobile} className="md:hidden">
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Nav Links */}
      <nav className="flex-1 space-y-1">
        {navLinks.map((link) => {
          const isActive = pathname === link.href || (link.href !== "/student" && pathname.startsWith(link.href));
          const Icon = link.icon;

          return (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 group relative",
                isActive
                  ? "bg-primary/10 text-primary border-l-2 border-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className={cn("h-5 w-5 shrink-0", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
              {!isCollapsed && <span>{link.label}</span>}
              {isCollapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded-md opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity shadow-md z-50 whitespace-nowrap">
                  {link.label}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Role Switcher Widget (For testing RBAC in production demo) */}
      <div className="border-t border-border pt-4 mt-4 space-y-2">
        {!isCollapsed && (
          <span className="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase">
            Test Roles (RBAC)
          </span>
        )}
        <div className={cn("flex gap-1", isCollapsed ? "flex-col" : "flex-row flex-wrap")}>
          {(["student", "recruiter", "officer", "admin"] as UserRole[]).map((r) => (
            <button
              key={r}
              onClick={() => {
                switchRole(r);
                // Redirect user to their respective dashboard
                const map = {
                  student: "/student",
                  recruiter: "/recruiter",
                  officer: "/officer",
                  admin: "/admin",
                };
                window.location.href = map[r];
              }}
              title={`Switch to ${r}`}
              className={cn(
                "px-2 py-1 text-[10px] font-medium rounded-sm border cursor-pointer capitalize transition-all",
                user.role === r
                  ? "bg-primary text-white border-primary"
                  : "border-muted text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              {isCollapsed ? r.substring(0, 2) : r}
            </button>
          ))}
        </div>
      </div>

      {/* User Section */}
      <div className="border-t border-border pt-4 mt-4 flex items-center justify-between">
        <div className="flex items-center space-x-3 overflow-hidden">
          {user.avatar ? (
            <img src={user.avatar} alt={user.name} className="h-8 w-8 rounded-full object-cover border border-border" />
          ) : (
            <div className="h-8 w-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-semibold text-sm">
              {user.name.charAt(0)}
            </div>
          )}
          {!isCollapsed && (
            <div className="text-left overflow-hidden">
              <p className="text-xs font-semibold truncate leading-tight">{user.name}</p>
              <p className="text-[10px] text-muted-foreground truncate capitalize">{user.role}</p>
            </div>
          )}
        </div>
        {!isCollapsed && (
          <button
            onClick={() => {
              logout();
              window.location.href = "/login";
            }}
            className="text-muted-foreground hover:text-destructive p-1 rounded-md cursor-pointer"
            title="Log Out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Toggle Button */}
      <div className="hidden md:flex">
        <div className={cn("relative transition-all duration-300", isCollapsed ? "w-20" : "w-64")}>
          <div className="fixed inset-y-0 left-0 z-20 flex flex-col h-full" style={{ width: isCollapsed ? "80px" : "256px" }}>
            {sidebarContent}
            {/* Collapse toggle pin */}
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="absolute -right-3 top-10 p-1 bg-card dark:bg-slate-950 border border-border rounded-full hover:bg-muted text-muted-foreground hover:text-foreground shadow-xs cursor-pointer z-50"
            >
              {isCollapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Top Navbar (Burger Menu) */}
      <div className="md:hidden flex items-center justify-between bg-card dark:bg-slate-950 border-b border-border px-4 py-3 fixed top-0 left-0 right-0 z-40">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 bg-gradient-to-tr from-indigo-500 to-violet-500 rounded-lg text-white">
            <Sparkles className="h-4 w-4" />
          </div>
          <span className="font-bold text-sm bg-gradient-to-r from-indigo-500 to-violet-500 bg-clip-text text-transparent">
            CareerOS AI
          </span>
        </div>
        <button onClick={toggleMobile} className="p-1 text-muted-foreground hover:text-foreground">
          <Menu className="h-6 w-6" />
        </button>
      </div>

      {/* Mobile Sidebar Overlay Drawer */}
      <AnimatePresence>
        {isMobileOpen && (
          <div className="fixed inset-0 z-50 md:hidden flex">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={toggleMobile}
              className="fixed inset-0 bg-black/60 backdrop-blur-xs"
            />
            {/* Drawer */}
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative w-64 h-full z-10"
            >
              {sidebarContent}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
