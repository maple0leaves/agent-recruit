import apiClient from "./client";
import type { ReviewDecision, SubmitReviewResponse } from "../types/matching";

/** Start a matching session via SSE stream.
 *  Uses fetch directly (not axios) because we need ReadableStream for SSE consumption.
 *  @param signal Optional AbortSignal for cancellation (D-03).
 */
export function startMatchingStream(jdId: number, signal?: AbortSignal): Promise<Response> {
  return fetch("/recruit/hitl/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jd_id: jdId }),
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
  return fetch("/recruit/hitl/reverse-stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
