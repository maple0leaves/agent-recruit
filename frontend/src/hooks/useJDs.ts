import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchJDs,
  fetchJDTemplates,
  createJD,
  updateJD,
  updateJDStatus,
  deleteJD,
} from "../api/jd";
import type { JDListResponse, JDFormValues, JDTemplate, JD } from "../types/jd";

export interface JDFilters {
  page: number;
  pageSize: number;
  status?: string;
  keyword?: string;
  dateFrom?: string;
  dateTo?: string;
}

export function useJDs(filters: JDFilters) {
  return useQuery<JDListResponse>({
    queryKey: ["jd", "list", filters],
    queryFn: () => fetchJDs({
      page: filters.page,
      page_size: filters.pageSize,
      ...(filters.status && { status: filters.status }),
      ...(filters.keyword && { keyword: filters.keyword }),
      ...(filters.dateFrom && { date_from: filters.dateFrom }),
      ...(filters.dateTo && { date_to: filters.dateTo }),
    }),
    placeholderData: keepPreviousData, // CRITICAL: v5 API — function, not boolean!
    staleTime: 30_000,
  });
}

export function useJDTemplates() {
  return useQuery<JDTemplate[]>({
    queryKey: ["jd", "templates"],
    queryFn: fetchJDTemplates,
    staleTime: Infinity, // Templates never change (D-11: HR cannot edit)
  });
}

export function useCreateJD() {
  const queryClient = useQueryClient();
  return useMutation<JD, Error, JDFormValues>({
    mutationFn: createJD,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jd", "list"] });
    },
  });
}

export function useUpdateJD() {
  const queryClient = useQueryClient();
  return useMutation<JD, Error, { id: number; data: JDFormValues }>({
    mutationFn: ({ id, data }) => updateJD(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jd", "list"] });
    },
  });
}

export function useUpdateJDStatus() {
  const queryClient = useQueryClient();
  return useMutation<JD, Error, { id: number; status: string }>({
    mutationFn: ({ id, status }) => updateJDStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jd", "list"] });
    },
  });
}

export function useDeleteJD() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, number>({
    mutationFn: deleteJD,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jd", "list"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
