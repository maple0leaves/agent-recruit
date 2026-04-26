import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link, useLocation } from "react-router-dom";
import { BrainCircuit, ArrowLeft, Send, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Skeleton } from "../components/ui/skeleton";
import { useMatchingSSE } from "../hooks/useMatchingSSE";
import PipelineSteps from "../components/Matching/PipelineSteps";
import MatchCandidateCard from "../components/Matching/MatchCandidateCard";
import ReviewNoteDialog from "../components/Matching/ReviewNoteDialog";
import CancelMatchDialog from "../components/Matching/CancelMatchDialog";
import FeedbackDialog from "../components/Matching/FeedbackDialog";
import type { ReviewDecision } from "../types/matching";

interface ReviewEntry {
  approved: boolean;
  feedback: string;
}

export default function Matching() {
  const { jdId } = useParams<{ jdId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const candidateIdParam = queryParams.get("candidateId");
  const {
    state,
    pipelineSteps,
    candidates,
    finalReport,
    error,
    sessionId,
    start,
    startReverse,
    cancel,
    submitReview,
    submitFeedback,
  } = useMatchingSSE();

  const [reviewMap, setReviewMap] = useState<Record<string, ReviewEntry>>({});
  const [reviewDialog, setReviewDialog] = useState<{
    candidateName: string;
    isRejection: boolean;
  } | null>(null);
  const [feedbackDialog, setFeedbackDialog] = useState<{
    candidateName: string;
  } | null>(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);

  // Start matching when page mounts with jdId (forward) or candidateId (reverse)
  useEffect(() => {
    if (state === "IDLE") {
      if (jdId) {
        const id = parseInt(jdId, 10);
        if (!isNaN(id)) {
          start(id);
        }
      } else if (candidateIdParam) {
        const id = parseInt(candidateIdParam, 10);
        if (!isNaN(id)) {
          startReverse(id);
        }
      }
    }
  }, [jdId, candidateIdParam, state, start, startReverse]);

  const allReviewed = candidates.length > 0 && candidates.every((c) => reviewMap[c.candidate_name]);

  const handleApprove = useCallback((candidateName: string) => {
    setReviewDialog({ candidateName, isRejection: false });
  }, []);

  const handleReject = useCallback((candidateName: string) => {
    setReviewDialog({ candidateName, isRejection: true });
  }, []);

  const handleReviewSubmit = useCallback(
    (feedback: string) => {
      if (!reviewDialog) return;
      const { candidateName, isRejection } = reviewDialog;
      setReviewMap((prev) => ({
        ...prev,
        [candidateName]: { approved: !isRejection, feedback },
      }));
      setReviewDialog(null);
    },
    [reviewDialog]
  );

  const handleSubmitAll = useCallback(async () => {
    const decisions: ReviewDecision[] = candidates.map((c) => ({
      candidate_name: c.candidate_name,
      approved: reviewMap[c.candidate_name]?.approved ?? false,
      feedback: reviewMap[c.candidate_name]?.feedback ?? "",
    }));
    await submitReview(decisions);
  }, [candidates, reviewMap, submitReview]);

  const handleFeedback = useCallback((candidateName: string) => {
    setFeedbackDialog({ candidateName });
  }, []);

  const handleFeedbackSubmit = useCallback(
    async (feedback: string) => {
      if (!feedbackDialog) return;
      const decisions: ReviewDecision[] = candidates.map((c) => ({
        candidate_name: c.candidate_name,
        approved: reviewMap[c.candidate_name]?.approved ?? false,
        feedback: reviewMap[c.candidate_name]?.feedback ?? "",
      }));
      const success = await submitFeedback(feedback, decisions);
      if (success) {
        // Clear review map for re-review
        setReviewMap({});
      }
      setFeedbackDialog(null);
    },
    [feedbackDialog, candidates, reviewMap, submitFeedback]
  );

  // Helper: render state-specific content
  const renderContent = () => {
    switch (state) {
      case "IDLE":
        return (
          <div className="flex flex-col items-center gap-4 py-16 text-muted-foreground">
            <BrainCircuit className="h-16 w-16" />
            <h2 className="text-xl font-semibold">
              {candidateIdParam ? "智能反向匹配" : "智能匹配"}
            </h2>
            <p className="text-sm">
              {candidateIdParam
                ? "正在准备反向匹配，请稍候..."
                : "请从 JD 列表选择一个职位开始匹配"}
            </p>
            {!candidateIdParam && (
              <Button variant="outline" onClick={() => navigate("/jd")}>
                前往 JD 列表
              </Button>
            )}
          </div>
        );

      case "CONNECTING":
      case "STREAMING":
        return (
          <div className="space-y-6">
            {/* Pipeline steps */}
            <PipelineSteps steps={pipelineSteps} />

            {/* Progress indicator */}
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>
                {state === "CONNECTING"
                  ? "正在连接..."
                  : "正在匹配候选人..."
                }
              </span>
            </div>

            {/* Cancel button (D-03) */}
            <div className="flex justify-center">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCancelDialogOpen(true)}
              >
                取消匹配
              </Button>
            </div>

            {/* Progressive candidate cards (D-07) */}
            {candidates.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-muted-foreground">
                  已匹配 {candidates.length} 位候选人
                </h3>
                <div className="grid gap-4 md:grid-cols-2">
                  {candidates.map((c) => (
                    <MatchCandidateCard
                      key={c.candidate_name}
                      candidate={c}
                      onApprove={() => {}}
                      onReject={() => {}}
                      isReviewed={false}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Skeleton while waiting for first results */}
            {candidates.length === 0 && (
              <div className="grid gap-4 md:grid-cols-2">
                {[1, 2].map((i) => (
                  <Skeleton key={i} className="h-40 w-full" />
                ))}
              </div>
            )}
          </div>
        );

      case "PAUSED":
      case "REVIEWING":
        return (
          <div className="space-y-6">
            {/* Pipeline steps -- all completed */}
            <PipelineSteps
              steps={pipelineSteps.map((s) => ({ ...s, status: "completed" as const }))}
            />

            {/* Review area header */}
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                审核匹配结果 ({candidates.length} 位候选人)
              </h2>
              <p className="text-sm text-muted-foreground">
                已审核 {Object.keys(reviewMap).length}/{candidates.length}
              </p>
            </div>

            {/* Candidate cards with review buttons (D-09) */}
            <div className="grid gap-4 md:grid-cols-2">
              {candidates.map((c) => (
                <MatchCandidateCard
                  key={c.candidate_name}
                  candidate={c}
                  onApprove={() => handleApprove(c.candidate_name)}
                  onReject={() => handleReject(c.candidate_name)}
                  onFeedback={() => handleFeedback(c.candidate_name)}
                  isReviewed={!!reviewMap[c.candidate_name]}
                  decision={
                    reviewMap[c.candidate_name]
                      ? reviewMap[c.candidate_name].approved
                        ? "approved"
                        : "rejected"
                      : null
                  }
                />
              ))}
            </div>

            {/* Submit all button (D-12) */}
            {allReviewed && (
              <div className="flex justify-center pt-4">
                <Button
                  size="lg"
                  onClick={handleSubmitAll}
                  className="gap-2"
                >
                  <Send className="h-4 w-4" />
                  完成审核
                </Button>
              </div>
            )}
          </div>
        );

      case "SUBMITTING":
        return (
          <div className="flex flex-col items-center gap-4 py-16">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="text-muted-foreground">正在提交审核结果...</p>
          </div>
        );

      case "DONE":
        return (
          <div className="space-y-6 py-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-green-600 dark:text-green-400">
                {candidateIdParam ? "反向匹配完成" : "匹配完成"}
              </h2>
              <Button variant="outline" onClick={() => navigate("/jd")}>
                返回 JD 列表
              </Button>
            </div>

            {/* Final report */}
            {finalReport && (
              <div className="rounded-lg border bg-card p-4 text-sm">
                <h3 className="mb-2 font-medium">最终报告</h3>
                <p className="whitespace-pre-wrap text-muted-foreground">
                  {finalReport}
                </p>
              </div>
            )}

            {/* Review summary */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium">审核结果汇总</h3>
              <div className="grid gap-3 md:grid-cols-2">
                {candidates.map((c) => {
                  const decision = reviewMap[c.candidate_name];
                  return (
                    <MatchCandidateCard
                      key={c.candidate_name}
                      candidate={c}
                      onApprove={() => {}}
                      onReject={() => {}}
                      isReviewed={true}
                      decision={
                        decision
                          ? decision.approved
                            ? "approved"
                            : "rejected"
                          : null
                      }
                    />
                  );
                })}
              </div>
            </div>
          </div>
        );

      case "ERROR":
        return (
          <div className="flex flex-col items-center gap-4 py-16">
            <AlertCircle className="h-12 w-12 text-destructive" />
            <h2 className="text-lg font-semibold">匹配失败</h2>
            <p className="text-sm text-muted-foreground">{error || "发生未知错误"}</p>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => navigate("/jd")}>
                返回 JD 列表
              </Button>
              {jdId && (
                <Button onClick={() => start(parseInt(jdId, 10))}>
                  重试
                </Button>
              )}
              {candidateIdParam && (
                <Button onClick={() => startReverse(parseInt(candidateIdParam, 10))}>
                  重试
                </Button>
              )}
            </div>
          </div>
        );

      case "CANCELLED":
        return (
          <div className="flex flex-col items-center gap-4 py-16 text-muted-foreground">
            <BrainCircuit className="h-12 w-12" />
            <h2 className="text-lg font-semibold">匹配已取消</h2>
            <p className="text-sm">匹配过程已取消，未保存任何结果</p>
            <Button variant="outline" onClick={() => navigate("/jd")}>
              返回 JD 列表
            </Button>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="py-6">
      {/* Back button */}
      <div className="mb-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate("/jd")}
          className="gap-1"
        >
          <ArrowLeft className="h-4 w-4" />
          返回 JD 列表
        </Button>
      </div>

      {/* Page content */}
      {renderContent()}

      {/* Review note dialog */}
      {reviewDialog && (
        <ReviewNoteDialog
          open={true}
          onClose={() => setReviewDialog(null)}
          candidateName={reviewDialog.candidateName}
          isRejection={reviewDialog.isRejection}
          onSubmit={handleReviewSubmit}
        />
      )}

      {/* Feedback dialog for Agent re-adjustment */}
      {feedbackDialog && (
        <FeedbackDialog
          open={true}
          onClose={() => setFeedbackDialog(null)}
          candidateName={feedbackDialog.candidateName}
          onSubmit={handleFeedbackSubmit}
        />
      )}

      {/* Cancel matching dialog */}
      <CancelMatchDialog
        open={cancelDialogOpen}
        onClose={() => setCancelDialogOpen(false)}
        onConfirm={() => {
          setCancelDialogOpen(false);
          cancel();
        }}
      />
    </div>
  );
}
