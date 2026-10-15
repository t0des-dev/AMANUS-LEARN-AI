import { authStorage, isJwtExpired } from "../lib/authTokens";

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    // In browser: always use relative path '/api/v1' unless an explicit non-localhost URL is provided.
    // This guarantees requests route cleanly through Nginx on the current domain/IP and port.
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl && !envUrl.includes("localhost") && !envUrl.includes("127.0.0.1") && envUrl.startsWith("http")) {
      return envUrl;
    }
    return "/api/v1";
  }
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.API_BASE_URL ||
    "http://api:8000/api/v1"
  );
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Request failed with status ${response.status}`
    );
  }

  return response.json() as Promise<T>;
}

export class AuthRefreshError extends Error {
  constructor(message = "Session expirée. Veuillez vous reconnecter.") {
    super(message);
    this.name = "AuthRefreshError";
  }
}

let refreshPromise: Promise<string> | null = null;

async function performTokenRefresh(): Promise<string> {
  const tokens = authStorage.getTokens();
  if (!tokens?.refresh) {
    throw new AuthRefreshError();
  }

  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl.replace(/\/$/, "")}/auth/refresh`;

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: tokens.refresh }),
  });

  if (!response.ok) {
    authStorage.clear();
    throw new AuthRefreshError();
  }

  const data = (await response.json()) as { access: string; refresh?: string };
  authStorage.setAccessToken(data.access);
  if (data.refresh) {
    authStorage.setTokens({ access: data.access, refresh: data.refresh });
  }
  return data.access;
}

async function refreshAccessToken(): Promise<string> {
  // Single-flight: concurrent 401s share one refresh call
  if (!refreshPromise) {
    refreshPromise = performTokenRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

/**
 * Central authenticated fetch wrapper.
 * - Injects the Bearer token from storage automatically.
 * - Proactively refreshes if the access token is expired.
 * - On a 401 response, performs a single-flight refresh and retries once.
 * - Clears stored tokens and throws AuthRefreshError if refresh fails.
 */
export async function authedRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  providedToken?: string,
  defaultErrorMessage?: string
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;
  const isFormData = options.body instanceof FormData;

  const buildHeaders = (token: string | null): Record<string, string> => {
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    if (!isFormData && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  };

  let token = providedToken ?? authStorage.getAccessToken();

  // Proactive refresh if token is expired (or missing but a refresh token exists)
  if ((!token || isJwtExpired(token)) && authStorage.getTokens()?.refresh) {
    try {
      token = await refreshAccessToken();
    } catch {
      token = authStorage.getAccessToken();
    }
  }

  let response = await fetch(url, {
    ...options,
    headers: buildHeaders(token),
  });

  if (response.status === 401 && authStorage.getTokens()?.refresh) {
    try {
      const newToken = await refreshAccessToken();
      response = await fetch(url, {
        ...options,
        headers: buildHeaders(newToken),
      });
    } catch {
      throw new AuthRefreshError();
    }
  }

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401) {
      authStorage.clear();
      throw new AuthRefreshError();
    }

    let errorMessage = defaultErrorMessage || "Une erreur est survenue.";
    if (typeof data.detail === "string") {
      errorMessage = data.detail;
    } else if (typeof data.message === "string") {
      errorMessage = data.message;
    } else if (typeof data === "object" && data !== null) {
      const firstKey = Object.keys(data)[0];
      if (firstKey && Array.isArray(data[firstKey])) {
        errorMessage = `${firstKey}: ${data[firstKey].join(" ")}`;
      } else if (firstKey && typeof data[firstKey] === "string") {
        errorMessage = `${firstKey}: ${data[firstKey]}`;
      }
    }
    throw new Error(errorMessage);
  }

  return data as T;
}
