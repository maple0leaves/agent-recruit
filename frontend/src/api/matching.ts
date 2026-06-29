import apiClient from "./client";
import { getApiBaseURL } from "./client";
import { useAuthStore } from "../store/authStore";
import type { ReviewDecision, SubmitReviewResponse } from "../types/matching";

function apiUrl(path: string): string {
  return `${getApiBaseURL().replace(/\/$/, "")}${path}`;
}

function streamHeaders(): HeadersInit {
  const token = useAuthStore.getState().accessToken;
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

/** Start a matching session via SSE stream.
 *  Uses fetch directly (not axios) because we need ReadableStream for SSE consumption.
 *  @param signal Optional AbortSignal for cancellation (D-03).
 */
export function startMatchingStream(
  jdId: number,
  topK?: number,
  signal?: AbortSignal,
): Promise<Response> {
  return fetch(apiUrl("/recruit/hitl/stream"), {
    method: "POST",
    headers: streamHeaders(),
    body: JSON.stringify({ jd_id: jdId, top_k: topK }),
    credentials: "include",
    signal,
  });
}

/** Start a reverse matching session via SSE stream (MATCH-04, D-02).
 *  Finds JDs matching the given candidate's skills.
 *  Uses fetch directly for ReadableStream SSE consumption.
 */
export function startReverseMatchingStream(
  candidateId: number,
  signal?: AbortSignal
): Promise<Response> {
  return fetch(apiUrl("/recruit/hitl/reverse-stream"), {
    method: "POST",
    headers: streamHeaders(),
    body: JSON.stringify({ candidate_id: candidateId }),
    credentials: "include",
    signal,
  });
}

/** Submit HR review decisions for all matched candidates (D-12). */
export async function submitReview(
  threadId: string,
  decisions: ReviewDecision[]
): Promise<SubmitReviewResponse> {
  const res = await apiClient.post<SubmitReviewResponse>("/recruit/hitl/resume", {
    thread_id: threadId,
    approvals: decisions,
  });
  return res.data;
}

/** Submit feedback and return SSE stream for re-run results (APRV-03, D-05).
 *  Uses fetch directly (not axios) to consume SSE ReadableStream.
 */
export function submitFeedbackAndStream(
  threadId: string,
  decisions: ReviewDecision[],
  feedback: string
): Promise<Response> {
  return fetch(apiUrl("/recruit/hitl/resume"), {
    method: "POST",
    headers: streamHeaders(),
    body: JSON.stringify({
      thread_id: threadId,
      approvals: decisions,
      feedback_rerun: true,
      global_feedback: feedback,
    }),
    credentials: "include",
  });
}
