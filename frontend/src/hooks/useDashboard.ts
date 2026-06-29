import { useQuery } from "@tanstack/react-query";
import { fetchDashboardStats, fetchDashboardTrend, type TrendDataPoint } from "../api/dashboard";
import type { DashboardStats } from "../types/matching";

export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard", "stats"],
    queryFn: fetchDashboardStats,
    staleTime: Infinity,
  });
}

export function useDashboardTrend() {
  return useQuery<TrendDataPoint[]>({
    queryKey: ["dashboard", "trend"],
    queryFn: fetchDashboardTrend,
    staleTime: Infinity,
  });
}
