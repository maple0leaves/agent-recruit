import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import PipelineStatusBadge from "./PipelineStatusBadge";
import { useUpdateCandidateStatus } from "@/hooks/useCandidates";
import type { CandidateStatus } from "@/types/candidate";

interface PipelineActionsProps {
  currentStatus: CandidateStatus;
  candidateId: number;
  onStatusChanged?: () => void;
}

const VALID_TRANSITIONS: Record<CandidateStatus, CandidateStatus[]> = {
  new: ["screening", "rejected"],
  screening: ["interview", "rejected"],
  interview: ["hired", "rejected"],
  hired: [],
  rejected: [],
};

const STATUS_LABELS: Record<string, string> = {
  new: "新入库",
  screening: "筛选中",
  interview: "面试",
  hired: "已录用",
  rejected: "不合适",
};

const PIPELINE_ORDER: CandidateStatus[] = ["new", "screening", "interview", "hired"];

export default function PipelineActions({
  currentStatus,
  candidateId,
  onStatusChanged,
}: PipelineActionsProps) {
  const [selectedStatus, setSelectedStatus] = useState<CandidateStatus | null>(null);
  const [statusNote, setStatusNote] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const statusMutation = useUpdateCandidateStatus();

  const validNextStatuses = VALID_TRANSITIONS[currentStatus] || [];
  const isTerminal = validNextStatuses.length === 0;
  const isRejected = currentStatus === "rejected";

  const handleConfirm = async () => {
    if (!statusNote.trim() || !selectedStatus) return;
    setError(null);
    try {
      await statusMutation.mutateAsync({
        id: candidateId,
        status: selectedStatus,
        status_note: statusNote.trim(),
      });
      setDialogOpen(false);
      setStatusNote("");
      setSelectedStatus(null);
      onStatusChanged?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : "状态变更失败，请重试";
      setError(message);
    }
  };

  const openDialog = (nextStatus: CandidateStatus) => {
    setSelectedStatus(nextStatus);
    setError(null);
    setStatusNote("");
    setDialogOpen(true);
  };

  const currentIndex = PIPELINE_ORDER.indexOf(currentStatus);

  return (
    <div className="space-y-4">
      {/* Current status badge */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">当前状态：</span>
        <PipelineStatusBadge status={currentStatus} />
      </div>

      {/* Pipeline flow visualization */}
      <div className="flex items-center gap-1 flex-wrap">
        {PIPELINE_ORDER.map((stage, idx) => {
          const stageIndex = PIPELINE_ORDER.indexOf(stage);
          const isPast = currentIndex > stageIndex;
          const isCurrent = currentStatus === stage;

          return (
            <div key={stage} className="flex items-center">
              <span
                className={`text-xs px-2 py-0.5 rounded ${
                  isCurrent
                    ? "bg-primary/10 text-primary font-medium"
                    : isPast
                    ? "text-muted-foreground"
                    : "text-muted-foreground/50"
                }`}
              >
                {STATUS_LABELS[stage]}
              </span>
              {idx < PIPELINE_ORDER.length - 1 && (
                <span className="text-muted-foreground/30 mx-1">→</span>
              )}
            </div>
          );
        })}
        {/* Show rejected as a branch when status is rejected */}
        {isRejected && (
          <div className="flex items-center ml-2">
            <span className="text-xs px-2 py-0.5 rounded bg-destructive/10 text-destructive font-medium">
              {STATUS_LABELS.rejected}
            </span>
          </div>
        )}
        {/* Show rejected as available branch when not terminal or rejected */}
        {!isTerminal && !isRejected && validNextStatuses.includes("rejected") && (
          <div className="flex items-center ml-2">
            <span className="text-xs px-2 py-0.5 rounded bg-destructive/10 text-destructive/60">
              {STATUS_LABELS.rejected}
            </span>
          </div>
        )}
      </div>

      <Separator className="my-2" />

      {/* Transition actions */}
      <div>
        <h4 className="text-sm font-medium mb-2">可执行操作</h4>
        {isTerminal ? (
          <p className="text-sm text-muted-foreground italic">已终态，不可变更</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {validNextStatuses.map((nextStatus) => (
              <Button
                key={nextStatus}
                variant="outline"
                size="sm"
                onClick={() => openDialog(nextStatus)}
              >
                {STATUS_LABELS[nextStatus]}
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* Status change dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认状态变更</DialogTitle>
            <DialogDescription>
              将候选人从「{STATUS_LABELS[currentStatus]}」变更为「{STATUS_LABELS[selectedStatus || ""] || ""}」
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {error && (
              <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label>
                变更备注 <span className="text-red-500">*</span>
              </Label>
              <Textarea
                placeholder="请填写状态变更原因..."
                value={statusNote}
                onChange={(e) => setStatusNote(e.target.value)}
                rows={3}
              />
              {statusNote.trim() === "" && (
                <p className="text-xs text-red-500">备注为必填项</p>
              )}
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                取消
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={!statusNote.trim() || statusMutation.isPending}
              >
                {statusMutation.isPending ? "保存中..." : "确认变更"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
