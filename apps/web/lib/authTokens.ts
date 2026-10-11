import { AuthTokens, UserProfile } from "../types/auth";

const ACCESS_TOKEN_KEY = "amanus_access_token";
const REFRESH_TOKEN_KEY = "amanus_refresh_token";
const USER_KEY = "amanus_user_cache";

export const authStorage = {
  getTokens(): AuthTokens | null {
    if (typeof window === "undefined") return null;
    const access = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refresh = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!access || !refresh) return null;
    return { access, refresh };
  },

  setTokens(tokens: AuthTokens) {
    if (typeof window === "undefined") return;
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  },

  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  setAccessToken(access: string) {
    if (typeof window === "undefined") return;
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
  },

  getCachedUser(): UserProfile | null {
    if (typeof window === "undefined") return null;
    const data = localStorage.getItem(USER_KEY);
    if (!data) return null;
    try {
      return JSON.parse(data) as UserProfile;
    } catch {
      return null;
    }
  },

  setCachedUser(user: UserProfile) {
    if (typeof window === "undefined") return;
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  clear() {
    if (typeof window === "undefined") return;
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export function isJwtExpired(token: string, skewSeconds = 10): boolean {
  if (!token) return true;
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return true;
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    const payload = JSON.parse(json);
    if (typeof payload.exp === "number") {
      return Date.now() >= (payload.exp - skewSeconds) * 1000;
    }
    return false;
  } catch {
    return true;
  }
}
