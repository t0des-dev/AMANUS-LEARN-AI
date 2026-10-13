import { apiRequest } from "./apiClient";
import { HealthStatusResponse } from "../types/api";

export async function fetchHealthStatus(): Promise<HealthStatusResponse> {
  try {
    return await apiRequest<HealthStatusResponse>("health");
  } catch {
    return { status: "degraded" };
  }
}
