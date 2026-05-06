import apiClient from "./client";

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
