"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { useNotificationStore } from "@/store/useNotificationStore";
import { useTheme } from "@/contexts/ThemeContext";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import {
  Bell,
  Search,
  Sun,
  Moon,
  ChevronRight,
  Sparkles,
  Command,
  User,
  Settings,
  LogOut,
  AlertCircle,
  Briefcase,
  Compass,
  Mic,
  MessageSquareText,
  BookOpen,
  BarChart3,
  Bot,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { AnimatePresence, motion } from "framer-motion";

export function TopNav() {
  const pathname = usePathname();
  const { user, logout, switchRole } = useAuthStore();
  const { theme, toggleTheme } = useTheme();
  const { notifications, markAsRead, markAllAsRead, clearAll } = useNotificationStore();

  const [isNotifOpen, setIsNotifOpen] = React.useState(false);
  const [isSearchOpen, setIsSearchOpen] = React.useState(false);
  const [isProfileOpen, setIsProfileOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsSearchOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!user) return null;

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  // Breadcrumb generator
  const getBreadcrumbs = () => {
    const parts = pathname.split("/").filter(Boolean);
    if (parts.length === 0) return [{ label: "Home", href: "/" }];
    return parts.map((part, index) => {
      const href = "/" + parts.slice(0, index + 1).join("/");
      const label = part.charAt(0).toUpperCase() + part.slice(1).replace("-", " ");
      return { label, href };
    });
  };

  const breadcrumbs = getBreadcrumbs();

  // Command palette search actions
  const commandActions = [
    { label: "Go to Dashboard", category: "Navigation", icon: Sparkles, action: () => (window.location.href = `/${user.role}`) },
    { label: "Open Career Discovery", category: "Navigation", icon: Compass, action: () => (window.location.href = "/discovery") },
    { label: "Open Resume Center", category: "Navigation", icon: FileText, action: () => (window.location.href = "/resume") },
    { label: "Open Jobs & Preparation", category: "Navigation", icon: Briefcase, action: () => (window.location.href = "/jobs") },
    { label: "Start AI Mock Interview", category: "AI Modules", icon: Mic, action: () => (window.location.href = "/interviews") },
    { label: "Open Communication Coach", category: "AI Modules", icon: MessageSquareText, action: () => (window.location.href = "/communication") },
    { label: "Open Training Academy", category: "AI Modules", icon: BookOpen, action: () => (window.location.href = "/academy") },
    { label: "Open Job Portal", category: "AI Modules", icon: Briefcase, action: () => (window.location.href = "/job-portal") },
    { label: "Open Application Tracker", category: "AI Modules", icon: BarChart3, action: () => (window.location.href = "/applications") },
    { label: "Open Progress Analytics", category: "AI Modules", icon: BarChart3, action: () => (window.location.href = "/analytics") },
    { label: "Open Community", category: "AI Modules", icon: User, action: () => (window.location.href = "/community") },
    { label: "Open AI Career Mentor", category: "AI Modules", icon: Bot, action: () => (window.location.href = "/mentor") },
    { label: "Open Global Search", category: "System", icon: Search, action: () => (window.location.href = "/global-search") },
    { label: "Open Notification Center", category: "System", icon: Bell, action: () => (window.location.href = "/notification-center") },
    { label: "Open Reports", category: "System", icon: FileText, action: () => (window.location.href = "/reports") },
    { label: "Switch to Student Role", category: "Developer Tools", icon: User, action: () => { switchRole("student"); window.location.href = "/student"; } },
    { label: "Switch to Recruiter Role", category: "Developer Tools", icon: User, action: () => { switchRole("recruiter"); window.location.href = "/recruiter"; } },
    { label: "Switch to Placement Officer", category: "Developer Tools", icon: User, action: () => { switchRole("officer"); window.location.href = "/officer"; } },
    { label: "Switch to Admin Role", category: "Developer Tools", icon: User, action: () => { switchRole("admin"); window.location.href = "/admin"; } },
    { label: "Toggle Theme (Dark / Light)", category: "System", icon: Sun, action: () => toggleTheme() },
    { label: "Sign Out", category: "System", icon: LogOut, action: () => { logout(); window.location.href = "/login"; } },
  ];

  const filteredCommands = searchQuery
    ? commandActions.filter((cmd) => cmd.label.toLowerCase().includes(searchQuery.toLowerCase()))
    : commandActions;

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border bg-background/80 backdrop-blur-md px-6 md:mt-0 mt-14">
        {/* Left: Breadcrumbs */}
        <div className="flex items-center space-x-2 text-sm">
          <span className="text-muted-foreground font-medium">CareerOS AI</span>
          {breadcrumbs.map((crumb, idx) => (
            <React.Fragment key={crumb.href}>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
              <span
                className={cn(
                  "font-medium truncate max-w-[120px] sm:max-w-[200px]",
                  idx === breadcrumbs.length - 1 ? "text-foreground font-semibold" : "text-muted-foreground hover:text-foreground"
                )}
              >
                {crumb.label}
              </span>
            </React.Fragment>
          ))}
        </div>

        {/* Right: Search + Notifications + Theme Toggle + User Menu */}
        <div className="flex items-center space-x-4">
          {/* Search Trigger Button */}
          <button
            onClick={() => setIsSearchOpen(true)}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-input bg-card/50 text-muted-foreground text-xs hover:text-foreground shadow-xs cursor-pointer select-none"
          >
            <Search className="h-4 w-4" />
            <span className="hidden sm:inline">Search...</span>
            <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded-sm border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100">
              <span className="text-xs">⌘</span>K
            </kbd>
          </button>

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
            title="Toggle theme"
          >
            {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>

          {/* Notification Center */}
          <div className="relative">
            <button
              onClick={() => setIsNotifOpen(!isNotifOpen)}
              className="p-2 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors relative cursor-pointer"
              title="Notifications"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-indigo-500 ring-2 ring-background animate-pulse" />
              )}
            </button>

            {/* Notification Dropdown Panel */}
            <AnimatePresence>
              {isNotifOpen && (
                <>
                  {/* Overlay click catcher */}
                  <div className="fixed inset-0 z-40" onClick={() => setIsNotifOpen(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 mt-2 w-80 rounded-xl border border-border bg-card text-card-foreground p-4 shadow-xl z-50 glass dark:bg-slate-950/95"
                  >
                    <div className="flex items-center justify-between border-b border-border pb-2 mb-3">
                      <div className="flex items-center space-x-1.5">
                        <span className="font-semibold text-sm">Notifications</span>
                        {unreadCount > 0 && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary text-primary-foreground font-semibold">
                            {unreadCount} new
                          </span>
                        )}
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={markAllAsRead}
                          className="text-[10px] text-primary hover:underline cursor-pointer"
                        >
                          Mark all read
                        </button>
                        <button
                          onClick={clearAll}
                          className="text-[10px] text-destructive hover:underline cursor-pointer"
                        >
                          Clear
                        </button>
                      </div>
                    </div>

                    <div className="max-h-72 overflow-y-auto space-y-3">
                      {notifications.length === 0 ? (
                        <div className="py-8 text-center text-xs text-muted-foreground flex flex-col items-center justify-center space-y-2">
                          <AlertCircle className="h-6 w-6 text-muted-foreground/50" />
                          <span>No notifications yet.</span>
                        </div>
                      ) : (
                        notifications.map((notif) => (
                          <div
                            key={notif.id}
                            onClick={() => {
                              markAsRead(notif.id);
                              if (notif.link) window.location.href = notif.link;
                            }}
                            className={cn(
                              "p-2.5 rounded-lg text-left text-xs transition-all cursor-pointer relative",
                              notif.isRead
                                ? "bg-muted/30 text-muted-foreground opacity-70"
                                : "bg-muted/80 text-foreground font-medium hover:bg-muted"
                            )}
                          >
                            {!notif.isRead && (
                              <span className="absolute top-3 left-1 h-1.5 w-1.5 rounded-full bg-indigo-500" />
                            )}
                            <div className="pl-2.5">
                              <div className="flex justify-between font-semibold text-xs leading-none mb-1">
                                <span className="capitalize">{notif.category}</span>
                                <span className="text-[10px] text-muted-foreground font-normal">{notif.time}</span>
                              </div>
                              <p className="font-bold text-xs truncate text-foreground">{notif.title}</p>
                              <p className="text-[10px] text-muted-foreground mt-0.5 line-clamp-2 leading-snug">
                                {notif.description}
                              </p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>

          {/* User Profile Menu */}
          <div className="relative">
            <button
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              className="h-8 w-8 rounded-full overflow-hidden border border-border cursor-pointer"
            >
              {user.avatar ? (
                <img src={user.avatar} alt={user.name} className="h-full w-full object-cover" />
              ) : (
                <div className="h-full w-full bg-primary text-white flex items-center justify-center font-bold text-sm">
                  {user.name.charAt(0)}
                </div>
              )}
            </button>

            <AnimatePresence>
              {isProfileOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setIsProfileOpen(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 mt-2 w-56 rounded-xl border border-border bg-card text-card-foreground p-2 shadow-xl z-50 glass dark:bg-slate-950/95"
                  >
                    <div className="px-3 py-2 border-b border-border text-left">
                      <p className="text-sm font-semibold truncate leading-none">{user.name}</p>
                      <p className="text-[10px] text-muted-foreground truncate mt-1">{user.email}</p>
                    </div>
                    <div className="p-1 space-y-1">
                      <Link
                        href="/profile"
                        onClick={() => setIsProfileOpen(false)}
                        className="flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs hover:bg-muted text-muted-foreground hover:text-foreground transition-all"
                      >
                        <User className="h-4 w-4" />
                        <span>My Profile</span>
                      </Link>
                      <Link
                        href="/settings"
                        onClick={() => setIsProfileOpen(false)}
                        className="flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs hover:bg-muted text-muted-foreground hover:text-foreground transition-all"
                      >
                        <Settings className="h-4 w-4" />
                        <span>Settings</span>
                      </Link>
                      <button
                        onClick={() => {
                          setIsProfileOpen(false);
                          logout();
                          window.location.href = "/login";
                        }}
                        className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all cursor-pointer text-left"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>Sign Out</span>
                      </button>
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>
      </header>

      {/* Command Palette Search Dialog */}
      <Dialog open={isSearchOpen} onOpenChange={setIsSearchOpen}>
        <DialogContent className="max-w-xl p-0 overflow-hidden bg-card/95 backdrop-blur-md">
          <div className="flex items-center border-b border-border px-4 py-3">
            <Command className="h-4 w-4 text-muted-foreground mr-3" />
            <input
              type="text"
              placeholder="Search actions, dashboards, or system tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-transparent text-sm text-foreground outline-hidden placeholder:text-muted-foreground"
            />
            <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded-sm border bg-muted px-1.5 font-mono text-[9px] font-medium opacity-80">
              ESC
            </kbd>
          </div>

          <div className="max-h-80 overflow-y-auto p-2">
            {filteredCommands.length === 0 ? (
              <div className="py-8 text-center text-xs text-muted-foreground">
                No matching actions found.
              </div>
            ) : (
              <div>
                {/* Group command actions by category */}
                {Array.from(new Set(filteredCommands.map((c) => c.category))).map((cat) => (
                  <div key={cat} className="mb-2">
                    <div className="text-[10px] font-semibold text-muted-foreground tracking-wider px-3 py-1.5 uppercase">
                      {cat}
                    </div>
                    <div className="space-y-0.5">
                      {filteredCommands
                        .filter((c) => c.category === cat)
                        .map((cmd) => {
                          const Icon = cmd.icon;
                          return (
                            <button
                              key={cmd.label}
                              onClick={() => {
                                setIsSearchOpen(false);
                                cmd.action();
                              }}
                              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs text-foreground hover:bg-primary/10 hover:text-primary transition-all text-left cursor-pointer"
                            >
                              <div className="flex items-center space-x-2.5">
                                <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                                <span>{cmd.label}</span>
                              </div>
                              <ChevronRight className="h-3 w-3 text-muted-foreground/50" />
                            </button>
                          );
                        })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
