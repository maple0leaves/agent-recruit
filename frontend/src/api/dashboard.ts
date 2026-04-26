import apiClient from "./client";
import type { DashboardStats } from "../types/matching";

/** Fetch dashboard aggregate stats (D-13, DASH-01). */
export async function fetchDashboardStats(): Promise<DashboardStats> {
  const res = await apiClient.get<DashboardStats>("/dashboard/stats");
  return res.data;
}
