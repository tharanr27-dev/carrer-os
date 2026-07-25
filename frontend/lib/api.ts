const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

type RequestOptions = RequestInit & {
  token?: string | null;
};

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
  errors?: string[] | null;
  request_id?: string | null;
  timestamp?: string;
}

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthUserResponse {
  id: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface ProfileResponse {
  id: string;
  user_id: string;
  first_name?: string | null;
  last_name?: string | null;
  headline?: string | null;
  bio?: string | null;
  profile_image_url?: string | null;
  role_specific_data?: Record<string, unknown> | null;
  completion_percentage: number;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers, body, ...init } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    body,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      payload?.detail ||
      payload?.message ||
      payload?.errors?.join(", ") ||
      `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<AuthTokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  register: (email: string, password: string) =>
    request<AuthUserResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  getProfile: (token: string) =>
    request<ApiResponse<ProfileResponse>>("/users/me/profile", {
      method: "GET",
      token,
    }),

  updateProfile: (
    token: string,
    profile: {
      first_name?: string;
      last_name?: string;
      headline?: string;
      bio?: string;
      profile_image_url?: string;
      role_specific_data?: Record<string, unknown>;
    }
  ) =>
    request<ApiResponse<ProfileResponse>>("/users/me/profile", {
      method: "PUT",
      token,
      body: JSON.stringify(profile),
    }),
};
