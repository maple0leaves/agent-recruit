import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchCandidates,
  fetchCandidate,
  uploadCandidate,
  updateCandidate,
  updateCandidateStatus,
} from "../api/candidates";
import type {
  Candidate,
  CandidateListResponse,
  CandidateUpdate,
  CandidateUploadResponse,
} from "../types/candidate";

export interface CandidateFilters {
  page: number;
  pageSize: number;
  status?: string;
  keyword?: string;
}

export function useCandidates(filters: CandidateFilters) {
  return useQuery<CandidateListResponse>({
    queryKey: ["candidates", "list", filters],
    queryFn: () =>
      fetchCandidates({
        page: filters.page,
        page_size: filters.pageSize,
        ...(filters.status && { status: filters.status }),
        ...(filters.keyword && { keyword: filters.keyword }),
      }),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useCandidate(id: number | null) {
  return useQuery<Candidate>({
    queryKey: ["candidates", id],
    queryFn: () => fetchCandidate(id!),
    enabled: id !== null,
  });
}

export function useUploadCandidate() {
  const queryClient = useQueryClient();
  return useMutation<CandidateUploadResponse, Error, { file: File; onProgress?: (pct: number) => void }>({
    mutationFn: ({ file, onProgress }) => uploadCandidate(file, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates", "list"] });
    },
  });
}

export function useUpdateCandidate() {
  const queryClient = useQueryClient();
  return useMutation<Candidate, Error, { id: number; data: CandidateUpdate }>({
    mutationFn: ({ id, data }) => updateCandidate(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["candidates", "list"] });
      queryClient.invalidateQueries({ queryKey: ["candidates", variables.id] });
    },
  });
}

export function useUpdateCandidateStatus() {
  const queryClient = useQueryClient();
  return useMutation<Candidate, Error, { id: number; status: string; status_note: string }>({
    mutationFn: ({ id, status, status_note }) => updateCandidateStatus(id, status, status_note),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["candidates", "list"] });
      queryClient.invalidateQueries({ queryKey: ["candidates", variables.id] });
    },
  });
}
