import { useQuery } from "@tanstack/react-query";
import { fetchHealthStatus } from "../services/healthService";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: fetchHealthStatus,
    refetchInterval: 10000,
    retry: 2,
    staleTime: 5000,
  });
}
