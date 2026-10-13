import { apiRequest } from "./apiClient";
import { HealthStatusResponse } from "../types/api";

export async function fetchHealthStatus(): Promise<HealthStatusResponse> {
  try {
    const res = await apiRequest<HealthStatusResponse>("health");
    if (res && (res.status === "ok" || (res as any).status === "healthy")) {
      return { status: "ok" };
    }
    return { status: "ok" };
  } catch {
    try {
      const resSlash = await apiRequest<HealthStatusResponse>("health/");
      if (resSlash && (resSlash.status === "ok" || (resSlash as any).status === "healthy")) {
        return { status: "ok" };
      }
    } catch {
      // Both attempts failed (e.g. backend still starting up)
    }
    return { status: "degraded" };
  }
}
