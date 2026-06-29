import apiClient from "./client";
import type { JD, JDListResponse, JDFormValues, JDTemplate } from "../types/jd";

export async function fetchJDs(params: Record<string, string | number>): Promise<JDListResponse> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "" && value !== null) {
      searchParams.set(key, String(value));
    }
  });
  const res = await apiClient.get<JDListResponse>(`/jd?${searchParams.toString()}`);
  return res.data;
}

export async function fetchJDTemplates(): Promise<JDTemplate[]> {
  const res = await apiClient.get<JDTemplate[]>("/jd/templates");
  return res.data;
}

export async function createJD(data: JDFormValues): Promise<JD> {
  const res = await apiClient.post<JD>("/jd", data);
  return res.data;
}

export async function updateJD(id: number, data: JDFormValues): Promise<JD> {
  const res = await apiClient.put<JD>(`/jd/${id}`, data);
  return res.data;
}

export async function updateJDStatus(id: number, status: string): Promise<JD> {
  const res = await apiClient.patch<JD>(`/jd/${id}/status`, { status });
  return res.data;
}

export async function deleteJD(id: number): Promise<void> {
  await apiClient.delete(`/jd/${id}`);
}
