import { useState, useCallback, useRef, useEffect } from "react";
import type {
  PipelineStep,
  MatchResult,
  MatchingState,
  ReviewDecision,
  SubmitReviewResponse,
} from "../types/matching";
import { PIPELINE_STEPS } from "../types/matching";
import { startMatchingStream, startReverseMatchingStream, submitFeedbackAndStream, submitReview } from "../api/matching";

export interface SSEEvent {
  event: string;
  data: Record<string, unknown>;
}

export function useMatchingSSE() {
  const [state, setState] = useState<MatchingState>("IDLE");
  const [pipelineSteps, setPipelineSteps] = useState<PipelineStep[]>(PIPELINE_STEPS);
  const [candidates, setCandidates] = useState<MatchResult[]>([]);
  const [finalReport, setFinalReport] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const threadIdRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const handleSSEEvent = useCallback((event: string, data: Record<string, unknown>) => {
    switch (event) {
      case "status": {
        const { node } = data as { node: string };
        const stepId = getStepIdFromNode(node);
        setPipelineSteps((prev) =>
          prev.map((step) => {
            if (step.id === stepId) {
              return { ...step, status: "completed" };
            }
            if (step.status === "active") {
              return { ...step, status: "completed" };
            }
            return step;
          })
        );
        break;
      }
      case "progress": {
        // Optional: show progress status text (could add to state if needed)
        break;
      }
      case "match_result": {
        const candidate = data as unknown as MatchResult;
        setCandidates((prev) => {
          if (prev.some((c) => c.candidate_name === candidate.candidate_name)) {
            return prev;
          }
          // Insert in descending order by match_score (D-08)
          const idx = prev.findIndex((c) => c.match_score < candidate.match_score);
          if (idx === -1) return [...prev, candidate];
          return [...prev.slice(0, idx), candidate, ...prev.slice(idx)];
        });
        break;
      }
      case "hitl_pause": {
        const { match_results, thread_id, session_id } = data as {
          match_results: MatchResult[];
          thread_id: string;
          session_id?: number;
        };
        threadIdRef.current = thread_id;
        if (session_id) {
          setSessionId(session_id);
        }
        // Sort descending by score (D-08)
        const sorted = [...match_results].sort(
          (a, b) => b.match_score - a.match_score
        );
        setCandidates(sorted);
        setState("PAUSED");
        break;
      }
      case "error": {
        setError((data as { message: string }).message);
        setState("ERROR");
        break;
      }
      case "done": {
        // Only transition if not already in an end state
        setState((prev) => {
          if (prev === "STREAMING") return "PAUSED";
          return prev;
        });
        break;
      }
    }
  }, []);

  const start = useCallback(async (jdId: number) => {
    // Reset state
    setState("CONNECTING");
    setError(null);
    setCandidates([]);
    setFinalReport("");
    setPipelineSteps(PIPELINE_STEPS.map((s) => ({ ...s, status: "pending" as const })));
    threadIdRef.current = null;

    abortRef.current = new AbortController();

    try {
      const response = await startMatchingStream(jdId, abortRef.current.signal);

      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error((errBody as { detail?: string }).detail || "匹配请求失败");
      }

      setState("STREAMING");
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          try {
            const parsed = JSON.parse(part.slice(6)) as SSEEvent;
            handleSSEEvent(parsed.event, parsed.data);
          } catch {
            // Skip malformed events
          }
        }
      }

      // Stream ended — if still streaming, transition to paused
      setState((prev) => {
        if (prev === "STREAMING") return "PAUSED";
        return prev;
      });
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setState("CANCELLED");
        return;
      }
      const message = err instanceof Error ? err.message : "连接异常";
      setError(message);
      setState("ERROR");
    }
  }, [handleSSEEvent]);

  const startReverse = useCallback(async (candidateId: number) => {
    setState("CONNECTING");
    setError(null);
    setCandidates([]);
    setFinalReport("");
    setSessionId(null);
    setPipelineSteps(PIPELINE_STEPS.map((s) => ({ ...s, status: "pending" as const })));
    threadIdRef.current = null;

    abortRef.current = new AbortController();

    try {
      const response = await startReverseMatchingStream(candidateId, abortRef.current.signal);

      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error((errBody as { detail?: string }).detail || "反向匹配请求失败");
      }

      setState("STREAMING");
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          try {
            const parsed = JSON.parse(part.slice(6)) as SSEEvent;
            handleSSEEvent(parsed.event, parsed.data);
          } catch {
            // Skip malformed events
          }
        }
      }

      setState((prev) => {
        if (prev === "STREAMING") return "PAUSED";
        return prev;
      });
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setState("CANCELLED");
        return;
      }
      const message = err instanceof Error ? err.message : "连接异常";
      setError(message);
      setState("ERROR");
    }
  }, [handleSSEEvent]);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setState("CANCELLED");
    setPipelineSteps(PIPELINE_STEPS.map((s) => ({ ...s, status: "pending" as const })));
  }, []);

  const submitReviewResult = useCallback(
    async (decisions: ReviewDecision[]): Promise<SubmitReviewResponse | null> => {
      if (!threadIdRef.current) {
        setError("缺少会话 ID");
        setState("ERROR");
        return null;
      }
      setState("SUBMITTING");
      try {
        const result = await submitReview(threadIdRef.current, decisions);
        setFinalReport(result.final_report);
        setState("DONE");
        return result;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "提交失败";
        setError(message);
        setState("ERROR");
        return null;
      }
    },
    []
  );

  const submitFeedback = useCallback(
    async (feedback: string, currentDecisions: ReviewDecision[]): Promise<boolean> => {
      if (!threadIdRef.current) {
        setError("缺少会话 ID");
        setState("ERROR");
        return false;
      }
      setState("SUBMITTING");
      try {
        const response = await submitFeedbackAndStream(
          threadIdRef.current, currentDecisions, feedback
        );

        if (!response.ok) {
          const errBody = await response.json().catch(() => ({}));
          throw new Error((errBody as { detail?: string }).detail || "反馈提交失败");
        }

        // Reset state for new SSE stream (clear candidates, reset to STREAMING)
        setState("STREAMING");
        setCandidates([]);
        setPipelineSteps(PIPELINE_STEPS.map((s) => ({ ...s, status: "pending" as const })));

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() || "";

          for (const part of parts) {
            if (!part.startsWith("data: ")) continue;
            try {
              const parsed = JSON.parse(part.slice(6)) as SSEEvent;
              handleSSEEvent(parsed.event, parsed.data);
            } catch {
              // Skip malformed events
            }
          }
        }

        setState((prev) => {
          if (prev === "STREAMING") return "PAUSED";
          return prev;
        });
        return true;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "反馈提交失败";
        setError(message);
        setState("ERROR");
        return false;
      }
    },
    [handleSSEEvent]
  );

  return {
    state,
    pipelineSteps,
    candidates,
    finalReport,
    error,
    sessionId,
    start,
    startReverse,
    cancel,
    submitReview: submitReviewResult,
    submitFeedback,
  };
}

/** Map LangGraph node names to user-facing pipeline step IDs (D-02). */
function getStepIdFromNode(nodeName: string): string {
  switch (nodeName) {
    case "triage_router":
      return "triage";
    case "planner_agent":
      return "search";
    case "worker_agent":
      return "score";
    case "reviewer_agent":
      return "review";
    default:
      return "triage";
  }
}
