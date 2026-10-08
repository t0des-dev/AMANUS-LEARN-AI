export interface HealthStatusResponse {
  status: "ok" | "degraded" | "error";
  version?: string;
  timestamp?: string;
}

export interface ApiError {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}
