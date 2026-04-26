/** Types for AI matching, approval workflow, and dashboard (Phase 4). */

export interface PipelineStep {
  id: string;
  label: string;
  status: "pending" | "active" | "completed";
}

export interface MatchResult {
  candidate_name: string;
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  recommendation: string;
  should_proceed: boolean;
}

export interface HITLPausePayload {
  match_results: MatchResult[];
  thread_id: string;
}

export interface ReviewDecision {
  candidate_name: string;
  approved: boolean;
  feedback: string;
}

export type MatchingState =
  | "IDLE"
  | "CONNECTING"
  | "STREAMING"
  | "PAUSED"
  | "REVIEWING"
  | "SUBMITTING"
  | "DONE"
  | "ERROR"
  | "CANCELLED";

export interface SubmitReviewResponse {
  status: string;
  final_report: string;
  match_results: MatchResult[];
}

export interface DashboardStats {
  active_jds: number;
  total_candidates: number;
  pending_approvals: number;
}

/** Pipeline step definitions for the 4-step visualization (D-02). */
export const PIPELINE_STEPS: PipelineStep[] = [
  { id: "triage", label: "Triage", status: "pending" },
  { id: "search", label: "搜索", status: "pending" },
  { id: "score", label: "评分", status: "pending" },
  { id: "review", label: "审核", status: "pending" },
];
