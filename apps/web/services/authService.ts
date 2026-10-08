import {
  AuthResponse,
  LoginPayload,
  RegisterPayload,
  UserProfile,
  UserUpdatePayload,
} from "../types/auth";

import { getApiBaseUrl } from "./apiClient";

async function authFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    let errorMessage = "Une erreur est survenue.";
    if (typeof data.detail === "string") {
      errorMessage = data.detail;
    } else if (typeof data.message === "string") {
      errorMessage = data.message;
    } else if (typeof data === "object" && data !== null) {
      // Collect field validation errors
      const firstKey = Object.keys(data)[0];
      if (firstKey && Array.isArray(data[firstKey])) {
        errorMessage = `${firstKey}: ${data[firstKey].join(" ")}`;
      }
    }
    throw new Error(errorMessage);
  }

  return data as T;
}

export const authService = {
  async register(payload: RegisterPayload): Promise<AuthResponse> {
    return authFetch<AuthResponse>("auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async login(payload: LoginPayload): Promise<AuthResponse> {
    return authFetch<AuthResponse>("auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async refresh(refreshToken: string): Promise<{ access: string }> {
    return authFetch<{ access: string }>("auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh: refreshToken }),
    });
  },

  async logout(refreshToken?: string): Promise<{ detail: string }> {
    return authFetch<{ detail: string }>("auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh: refreshToken || "" }),
    });
  },

  async getMe(accessToken: string): Promise<UserProfile> {
    return authFetch<UserProfile>("auth/me", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  },

  async updateMe(
    accessToken: string,
    payload: UserUpdatePayload
  ): Promise<UserProfile> {
    return authFetch<UserProfile>("auth/me", {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(payload),
    });
  },
};
