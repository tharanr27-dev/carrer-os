import { create } from "zustand";
import {
  api,
  ApiError,
  clearStoredTokens,
  errorMessage,
  getStoredTokens,
  MeResponse,
  onSessionExpired,
  ProfileResponse,
  setStoredTokens,
} from "@/lib/api";

export type UserRole = "student" | "recruiter" | "officer" | "admin";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
  title?: string;
  permissions: string[];
  companyId: string | null;
  collegeId: string | null;
  /** Recruiter/officer who has registered but not yet created their company/college. */
  needsOrgSetup: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  /** True while the initial session restore (stored tokens -> /auth/me) is running. */
  isInitializing: boolean;
  isLoading: boolean;
  error: string | null;
  init: () => Promise<void>;
  login: (email: string, password: string) => Promise<boolean>;
  register: (name: string, email: string, password: string, role: Exclude<UserRole, "admin">) => Promise<boolean>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  refreshSession: () => Promise<boolean>;
  updateUser: (updated: { name?: string; title?: string; avatar?: string }) => Promise<void>;
}

export const HOME_PATH: Record<UserRole, string> = {
  student: "/student",
  recruiter: "/recruiter",
  officer: "/officer",
  admin: "/admin",
};

const REGISTRATION_TITLES: Record<Exclude<UserRole, "admin">, string> = {
  student: "Undergraduate Student",
  recruiter: "Hiring Manager",
  officer: "Placement Executive",
};

function splitName(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return { firstName: parts[0] ?? "", lastName: parts.slice(1).join(" ") };
}

function profileName(profile: ProfileResponse | null): string | null {
  const name = [profile?.first_name, profile?.last_name].filter(Boolean).join(" ").trim();
  return name || null;
}

/**
 * Role comes from the backend: admin = admin RBAC permission, recruiter = linked to a company,
 * officer = registered placement officer. Before the org exists, the role chosen at sign-up
 * (stored in the profile) decides which portal shows the setup step. Admin is never self-selected.
 */
function deriveRole(me: MeResponse, profile: ProfileResponse | null): { role: UserRole; needsOrgSetup: boolean } {
  if (me.permissions.some((p) => p.startsWith("admin:"))) return { role: "admin", needsOrgSetup: false };
  if (me.company_id) return { role: "recruiter", needsOrgSetup: false };
  if (me.college_id) return { role: "officer", needsOrgSetup: false };

  const selected = profile?.role_specific_data?.selected_role;
  if (selected === "recruiter") return { role: "recruiter", needsOrgSetup: true };
  if (selected === "officer") return { role: "officer", needsOrgSetup: true };
  return { role: "student", needsOrgSetup: false };
}

function buildUser(me: MeResponse, profile: ProfileResponse | null): User {
  const { role, needsOrgSetup } = deriveRole(me, profile);
  return {
    id: me.id,
    name: profileName(profile) ?? me.email.split("@")[0],
    email: me.email,
    role,
    avatar: profile?.profile_image_url ?? undefined,
    title: profile?.headline ?? undefined,
    permissions: me.permissions,
    companyId: me.company_id,
    collegeId: me.college_id,
    needsOrgSetup,
  };
}

async function loadUser(): Promise<User> {
  const me = await api.me();
  const profile = await api.getProfile().catch(() => null);
  return buildUser(me, profile);
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isInitializing: true,
  isLoading: false,
  error: null,

  init: async () => {
    if (!getStoredTokens()) {
      set({ user: null, isAuthenticated: false, isInitializing: false });
      return;
    }
    try {
      const user = await loadUser();
      set({ user, isAuthenticated: true, isInitializing: false });
    } catch (error) {
      // Only an auth failure ends the session; a network blip keeps tokens for the next try.
      if (error instanceof ApiError && (error.status === 401 || error.status === 403)) clearStoredTokens();
      set({ user: null, isAuthenticated: false, isInitializing: false, error: errorMessage(error) });
    }
  },

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const tokens = await api.login(email, password);
      setStoredTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      const user = await loadUser();
      set({ user, isAuthenticated: true, isLoading: false });
      return true;
    } catch (error) {
      clearStoredTokens();
      set({ user: null, isAuthenticated: false, isLoading: false, error: errorMessage(error) });
      return false;
    }
  },

  register: async (name, email, password, role) => {
    set({ isLoading: true, error: null });
    try {
      await api.register(email, password);
      const tokens = await api.login(email, password);
      setStoredTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });

      const { firstName, lastName } = splitName(name);
      await api.updateProfile({
        first_name: firstName,
        last_name: lastName,
        headline: REGISTRATION_TITLES[role],
        role_specific_data: { selected_role: role },
      });

      const user = await loadUser();
      set({ user, isAuthenticated: true, isLoading: false });
      return true;
    } catch (error) {
      clearStoredTokens();
      set({ user: null, isAuthenticated: false, isLoading: false, error: errorMessage(error) });
      return false;
    }
  },

  logout: () => {
    clearStoredTokens();
    set({ user: null, isAuthenticated: false, error: null });
  },

  refreshUser: async () => {
    try {
      set({ user: await loadUser() });
    } catch (error) {
      set({ error: errorMessage(error) });
    }
  },

  refreshSession: async () => {
    const tokens = getStoredTokens();
    if (!tokens?.refreshToken) return false;
    try {
      const fresh = await api.refreshToken(tokens.refreshToken);
      setStoredTokens({ accessToken: fresh.access_token, refreshToken: fresh.refresh_token });
      return true;
    } catch {
      return false;
    }
  },

  updateUser: async (updated) => {
    const current = get().user;
    if (!current) return;

    const payload: Parameters<typeof api.updateProfile>[0] = {};
    if (updated.name !== undefined) {
      const { firstName, lastName } = splitName(updated.name);
      payload.first_name = firstName;
      payload.last_name = lastName;
    }
    if (updated.title !== undefined) payload.headline = updated.title;
    if (updated.avatar !== undefined) payload.profile_image_url = updated.avatar;

    // Persist first; only reflect the change in the UI once the backend accepted it.
    const profile = await api.updateProfile(payload);
    set({
      user: {
        ...current,
        name: profileName(profile) ?? current.name,
        title: profile.headline ?? current.title,
        avatar: profile.profile_image_url ?? current.avatar,
      },
    });
  },
}));

// An unrecoverable 401 anywhere in the app ends the session.
onSessionExpired(() => {
  useAuthStore.setState({ user: null, isAuthenticated: false });
});
