import { useQuery } from "@tanstack/react-query";
import { fetchDashboardStats } from "../api/dashboard";
import type { DashboardStats } from "../types/matching";

/** TanStack Query hook for dashboard stats (D-13, D-14).
 *  staleTime: Infinity means data never re-fetches automatically — only on page load.
 */
export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard", "stats"],
    queryFn: fetchDashboardStats,
    staleTime: Infinity,
  });
}
