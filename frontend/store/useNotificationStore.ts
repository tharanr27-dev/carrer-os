import { create } from "zustand";
import type { Announcement } from "@/lib/api";

export type NotificationCategory = "jobs" | "interviews" | "learning" | "system" | "community";

export interface NotificationItem {
  id: string;
  category: NotificationCategory;
  title: string;
  description: string;
  time: string;
  isRead: boolean;
  link?: string;
}

interface NotificationState {
  notifications: NotificationItem[];
  addNotification: (category: NotificationCategory, title: string, description: string, link?: string) => void;
  /** Merges platform announcements fetched from the backend (kept unread-state across syncs). */
  syncAnnouncements: (announcements: Announcement[]) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
}

function relativeTime(iso: string) {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  return `${Math.round(hours / 24)} d ago`;
}

// Notifications originate from real activity (API outcomes) and backend announcements only.
export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],

  addNotification: (category, title, description, link) => {
    const item: NotificationItem = {
      id: `notif-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      category,
      title,
      description,
      time: "Just now",
      isRead: false,
      link,
    };
    set((state) => ({ notifications: [item, ...state.notifications] }));
  },

  syncAnnouncements: (announcements) => {
    set((state) => {
      const existing = new Map(state.notifications.map((n) => [n.id, n]));
      const synced = announcements.map<NotificationItem>((a) => ({
        id: `ann-${a.id}`,
        category: "system",
        title: a.title,
        description: a.content,
        time: relativeTime(a.created_at),
        isRead: existing.get(`ann-${a.id}`)?.isRead ?? false,
      }));
      const local = state.notifications.filter((n) => !n.id.startsWith("ann-"));
      return { notifications: [...local, ...synced] };
    });
  },

  markAsRead: (id) => {
    set((state) => ({
      notifications: state.notifications.map((n) => (n.id === id ? { ...n, isRead: true } : n)),
    }));
  },

  markAllAsRead: () => {
    set((state) => ({ notifications: state.notifications.map((n) => ({ ...n, isRead: true })) }));
  },

  clearAll: () => {
    set({ notifications: [] });
  },
}));
