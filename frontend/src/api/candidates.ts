import apiClient from "./client";
import type {
  Candidate,
  CandidateBatchUploadResponse,
  CandidateListResponse,
  CandidateUpdate,
  CandidateUploadResponse,
} from "../types/candidate";

export async function fetchCandidates(params: Record<string, string | number>): Promise<CandidateListResponse> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "" && value !== null) {
      searchParams.set(key, String(value));
    }
  });
  const res = await apiClient.get<CandidateListResponse>(`/candidates?${searchParams.toString()}`);
  return res.data;
}

export async function fetchCandidate(id: number): Promise<Candidate> {
  const res = await apiClient.get<Candidate>(`/candidates/${id}`);
  return res.data;
}

export async function uploadCandidate(
  file: File,
  onProgress?: (pct: number) => void
): Promise<CandidateUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await apiClient.post<CandidateUploadResponse>("/candidates/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });
  return res.data;
}

export async function uploadCandidatesBatch(
  files: File[],
  onProgress?: (pct: number) => void
): Promise<CandidateBatchUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const res = await apiClient.post<CandidateBatchUploadResponse>("/candidates/upload/batch", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });
  return res.data;
}

export async function updateCandidate(id: number, data: CandidateUpdate): Promise<Candidate> {
  const res = await apiClient.put<Candidate>(`/candidates/${id}`, data);
  return res.data;
}

export async function updateCandidateStatus(id: number, status: string, status_note: string): Promise<Candidate> {
  const res = await apiClient.patch<Candidate>(`/candidates/${id}/status`, { status, status_note });
  return res.data;
}

export async function deleteCandidate(id: number): Promise<void> {
  await apiClient.delete(`/candidates/${id}`);
}
