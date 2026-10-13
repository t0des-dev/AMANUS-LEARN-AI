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
