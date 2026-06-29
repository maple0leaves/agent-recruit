import apiClient from "./client";
import type { MatchResult, ReviewDecision } from "@/types/matching";

export interface MatchSessionItem {
  id: number;
  jd_id: number | null;
  jd_title: string | null;
  candidate_id: number | null;
  thread_id: string;
  status: string;
  total_candidates: number;
  approved_count: number;
  rejected_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface MatchSessionResult extends MatchResult {
  review_status?: "approved" | "rejected" | null;
  review_feedback?: string | null;
  resume_source?: string | null;
  resume_text?: string | null;
  summary?: string | null;
}

export interface MatchSessionDetail extends MatchSessionItem {
  results: MatchSessionResult[];
}

export interface MatchSessionListResponse {
  items: MatchSessionItem[];
  total: number;
  page: number;
  page_size: number;
}

export async function fetchMatchSessions(params: {
  page?: number;
  page_size?: number;
  status?: string;
  jd_id?: number;
  keyword?: string;
}): Promise<MatchSessionListResponse> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "" && value !== null) {
      searchParams.set(key, String(value));
    }
  });
  const res = await apiClient.get<MatchSessionListResponse>(
    `/match-sessions?${searchParams.toString()}`
  );
  return res.data;
}

export async function fetchMatchSession(id: number): Promise<MatchSessionDetail> {
  const res = await apiClient.get<MatchSessionDetail>(`/match-sessions/${id}`);
  return res.data;
}

export async function reviewMatchSession(
  id: number,
  approvals: ReviewDecision[],
): Promise<MatchSessionDetail> {
  const res = await apiClient.patch<MatchSessionDetail>(
    `/match-sessions/${id}/review`,
    { approvals },
  );
  return res.data;
}

export async function deleteMatchSession(id: number): Promise<void> {
  await apiClient.delete(`/match-sessions/${id}`);
}

export async function fetchMatchSessionResumePdf(
  id: number,
  candidateName: string,
): Promise<Blob> {
  const res = await apiClient.get<Blob>(`/match-sessions/${id}/resume`, {
    params: { candidate_name: candidateName },
    responseType: "blob",
  });
  return res.data;
}
