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
import { MessageSquare } from "lucide-react";

interface FeedbackDialogProps {
  open: boolean;
  onClose: () => void;
  candidateName: string;
  onSubmit: (feedback: string) => void;
}

export default function FeedbackDialog({
  open,
  onClose,
  candidateName,
  onSubmit,
}: FeedbackDialogProps) {
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = () => {
    if (!feedback.trim()) {
      setError("请填写反馈内容");
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
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            反馈重新匹配 — {candidateName}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <Label htmlFor="feedback-text">
            您的反馈将帮助 Agent 重新调整匹配结果
          </Label>
          <Textarea
            id="feedback-text"
            placeholder="请描述您对匹配结果的建议，Agent 将据此重新调整..."
            value={feedback}
            onChange={(e) => {
              setFeedback(e.target.value);
              if (error) setError(null);
            }}
            rows={5}
          />
          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            取消
          </Button>
          <Button onClick={handleSubmit} className="gap-2">
            <MessageSquare className="h-4 w-4" />
            提交反馈并重新匹配
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
