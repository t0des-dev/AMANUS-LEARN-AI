import { useQuery } from "@tanstack/react-query";
import { fetchHealthStatus } from "../services/healthService";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: fetchHealthStatus,
    refetchInterval: 60000,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    retry: false,
  });
}
