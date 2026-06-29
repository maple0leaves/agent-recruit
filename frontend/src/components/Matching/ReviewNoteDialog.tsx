import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../ui/dialog";
import { Textarea } from "../ui/textarea";
import { Button } from "../ui/button";
import { Label } from "../ui/label";

interface ReviewNoteDialogProps {
  open: boolean;
  onClose: () => void;
  candidateName: string;
  isRejection: boolean;
  onSubmit: (feedback: string) => void;
}

export default function ReviewNoteDialog({
  open,
  onClose,
  candidateName,
  isRejection,
  onSubmit,
}: ReviewNoteDialogProps) {
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = () => {
    if (isRejection && !feedback.trim()) {
      setError("请填写驳回理由");
      return;
    }
    onSubmit(feedback.trim());
    setFeedback("");
    setError(null);
  };

  const handleClose = () => {
    setFeedback("");
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(open) => { if (!open) handleClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isRejection ? "驳回候选人" : "通过候选人"} — {candidateName}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <Label htmlFor="review-note">
            {isRejection ? "驳回理由" : "通过备注"}
            {isRejection && <span className="text-destructive ml-1">*</span>}
          </Label>
          <Textarea
            id="review-note"
            placeholder={
              isRejection
                ? "请填写驳回原因（必填）"
                : "通过备注（可选，例如安排面试时间）"
            }
            value={feedback}
            onChange={(e) => {
              setFeedback(e.target.value);
              if (error) setError(null);
            }}
            rows={4}
          />
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            取消
          </Button>
          <Button
            variant={isRejection ? "destructive" : "default"}
            onClick={handleSubmit}
          >
            确认{isRejection ? "驳回" : "通过"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
