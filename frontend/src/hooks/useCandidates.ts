import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchCandidates,
  fetchCandidate,
  uploadCandidate,
  uploadCandidatesBatch,
  updateCandidate,
  updateCandidateStatus,
  deleteCandidate,
} from "../api/candidates";
import type {
  Candidate,
  CandidateBatchUploadResponse,
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
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      const hasParsingCandidates = items.some(
        (candidate) =>
          candidate.parse_status === "parsing" ||
          candidate.parse_status === "pending",
      );
      return hasParsingCandidates ? 3000 : false;
    },
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

export function useUploadCandidatesBatch() {
  const queryClient = useQueryClient();
  return useMutation<CandidateBatchUploadResponse, Error, { files: File[]; onProgress?: (pct: number) => void }>({
    mutationFn: ({ files, onProgress }) => uploadCandidatesBatch(files, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates", "list"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
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

export function useDeleteCandidate() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, number>({
    mutationFn: deleteCandidate,
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: ["candidates", "list"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.removeQueries({ queryKey: ["candidates", id] });
    },
  });
}
