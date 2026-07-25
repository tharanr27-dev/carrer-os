import { create } from "zustand";

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
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAll: () => void;
}

const initialNotifications: NotificationItem[] = [
  {
    id: "notif-1",
    category: "jobs",
    title: "New Job Match: Stripe",
    description: "Your profile is a 94% match for Software Engineer (Frontend) at Stripe. Apply today!",
    time: "10 mins ago",
    isRead: false,
    link: "/jobs",
  },
  {
    id: "notif-2",
    category: "interviews",
    title: "Mock Interview Tomorrow",
    description: "Your mock interview with AI Mentor on 'System Design' starts tomorrow at 10:00 AM.",
    time: "2 hours ago",
    isRead: false,
    link: "/student",
  },
  {
    id: "notif-3",
    category: "learning",
    title: "New Learning Track Recommended",
    description: "Based on your Skill Gap in Next.js 15, we recommend starting the 'Advanced Next.js Architecture' track.",
    time: "4 hours ago",
    isRead: true,
    link: "/careers",
  },
  {
    id: "notif-4",
    category: "system",
    title: "Resume Score Upgraded!",
    description: "Congratulations! Your latest resume upload achieved an ATS score of 87/100 (+12 points).",
    time: "1 day ago",
    isRead: false,
    link: "/resume",
  },
  {
    id: "notif-5",
    category: "community",
    title: "College Placement Drive",
    description: "Google recruitment drive has been announced for Computer Science seniors. Register now.",
    time: "2 days ago",
    isRead: true,
    link: "/jobs",
  },
  {
    id: "notif-6",
    category: "jobs",
    title: "Job Application Viewed",
    description: "Vercel viewed your application for Frontend Engineer Intern.",
    time: "3 days ago",
    isRead: true,
    link: "/jobs",
  },
];

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: initialNotifications,

  addNotification: (category, title, description, link) => {
    const newNotif: NotificationItem = {
      id: `notif-${Date.now()}`,
      category,
      title,
      description,
      time: "Just now",
      isRead: false,
      link,
    };
    set((state) => ({
      notifications: [newNotif, ...state.notifications],
    }));
  },

  markAsRead: (id) => {
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, isRead: true } : n
      ),
    }));
  },

  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, isRead: true })),
    }));
  },

  clearAll: () => {
    set({ notifications: [] });
  },
}));
