import { apiRequest } from "./apiClient";
import { HealthStatusResponse } from "../types/api";

export async function fetchHealthStatus(): Promise<HealthStatusResponse> {
  return apiRequest<HealthStatusResponse>("health");
}
