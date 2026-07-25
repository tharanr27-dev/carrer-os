import { create } from "zustand";
import { api, ProfileResponse } from "@/lib/api";

export type UserRole = "student" | "recruiter" | "officer" | "admin";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
  company?: string; // Recruiter specific
  college?: string; // Placement Officer specific
  title?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, role?: UserRole) => Promise<boolean>;
  register: (name: string, email: string, password: string, role: UserRole) => Promise<boolean>;
  logout: () => void;
  switchRole: (role: UserRole) => void;
  updateUser: (updatedUser: Partial<User>) => Promise<void>;
}

const mockUsers: Record<UserRole, User> = {
  student: {
    id: "stu-101",
    name: "Alex Morgan",
    email: "alex.morgan@university.edu",
    role: "student",
    title: "Computer Science Junior",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=200",
  },
  recruiter: {
    id: "rec-202",
    name: "Sarah Jenkins",
    email: "sjenkins@stripe.com",
    role: "recruiter",
    title: "Senior Tech Talent Lead",
    company: "Stripe",
    avatar: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=200",
  },
  officer: {
    id: "off-303",
    name: "Dr. Robert Chen",
    email: "robert.chen@university.edu",
    role: "officer",
    title: "Director of Career Services & Placement",
    college: "Stanford School of Engineering",
    avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&q=80&w=200",
  },
  admin: {
    id: "adm-404",
    name: "Elena Rostova",
    email: "elena.r@careeros.ai",
    role: "admin",
    title: "Chief System Administrator",
    avatar: "https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&q=80&w=200",
  },
};

const TOKEN_STORAGE_KEY = "careeros_auth_tokens";

interface StoredTokens {
  accessToken: string;
  refreshToken: string;
}

function getStoredTokens(): StoredTokens | null {
  if (typeof window === "undefined") return null;

  const rawTokens = window.localStorage.getItem(TOKEN_STORAGE_KEY);
  if (!rawTokens) return null;

  try {
    return JSON.parse(rawTokens) as StoredTokens;
  } catch {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    return null;
  }
}

function setStoredTokens(tokens: StoredTokens) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));
}

function clearStoredTokens() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

function splitName(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return {
    firstName: parts[0] ?? "",
    lastName: parts.slice(1).join(" "),
  };
}

function profileToName(profile?: ProfileResponse | null) {
  const name = [profile?.first_name, profile?.last_name].filter(Boolean).join(" ").trim();
  return name || null;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: mockUsers.student, // Default to student role for testing convenience
  isAuthenticated: true,
  isLoading: false,

  login: async (email, password, forcedRole) => {
    set({ isLoading: true });

    try {
      const role = forcedRole || "student";
      const tokens = await api.login(email, password);
      setStoredTokens({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      });

      const profileResponse = await api.getProfile(tokens.access_token).catch(() => null);
      const profile = profileResponse?.data ?? null;
      const profileName = profileToName(profile);
      const selectedUser = {
        ...mockUsers[role],
        id: profile?.user_id ?? mockUsers[role].id,
        name: profileName ?? mockUsers[role].name,
        email,
        role,
        title: profile?.headline ?? mockUsers[role].title,
        avatar: profile?.profile_image_url ?? mockUsers[role].avatar,
      };

      set({
        user: selectedUser,
        isAuthenticated: true,
        isLoading: false,
      });
      return true;
    } catch (error) {
      console.error("Login failed", error);
      clearStoredTokens();
      set({ user: null, isAuthenticated: false, isLoading: false });
      return false;
    }
  },

  register: async (name, email, password, role) => {
    set({ isLoading: true });

    try {
      const registeredUser = await api.register(email, password);
      const tokens = await api.login(email, password);
      setStoredTokens({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      });

      const { firstName, lastName } = splitName(name);
      await api.updateProfile(tokens.access_token, {
        first_name: firstName,
        last_name: lastName,
        headline:
          role === "student"
            ? "Undergraduate Student"
            : role === "recruiter"
              ? "Hiring Manager"
              : role === "officer"
                ? "Placement Executive"
                : "Platform Moderator",
        profile_image_url: `https://api.dicebear.com/7.x/adventurer/svg?seed=${encodeURIComponent(name)}`,
        role_specific_data: { selected_role: role },
      });

      const newUser: User = {
        id: registeredUser.id,
        name,
        email,
        role,
        title: role === "student" ? "Undergraduate Student" : role === "recruiter" ? "Hiring Manager" : role === "officer" ? "Placement Executive" : "Platform Moderator",
        avatar: `https://api.dicebear.com/7.x/adventurer/svg?seed=${name}`,
      };

      set({
        user: newUser,
        isAuthenticated: true,
        isLoading: false,
      });
      return true;
    } catch (error) {
      console.error("Registration failed", error);
      clearStoredTokens();
      set({ isLoading: false });
      return false;
    }
  },

  logout: () => {
    clearStoredTokens();
    set({ user: null, isAuthenticated: false });
  },

  switchRole: (role) => {
    set({ user: mockUsers[role], isAuthenticated: true });
  },

  updateUser: async (updatedUser) => {
    const tokens = getStoredTokens();

    if (tokens?.accessToken && updatedUser.name) {
      const { firstName, lastName } = splitName(updatedUser.name);
      await api.updateProfile(tokens.accessToken, {
        first_name: firstName,
        last_name: lastName,
        headline: updatedUser.title,
        profile_image_url: updatedUser.avatar,
      });
    }

    set((state) => ({
      user: state.user ? { ...state.user, ...updatedUser } : null,
    }));
  },
}));
