import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../ui/dialog";
import { Button } from "../ui/button";

interface CancelMatchDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export default function CancelMatchDialog({
  open,
  onClose,
  onConfirm,
}: CancelMatchDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>取消匹配</DialogTitle>
          <DialogDescription>
            取消后当前匹配进度将丢失，已匹配的结果不会保存。确定要取消吗？
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            继续等待
          </Button>
          <Button variant="destructive" onClick={onConfirm}>
            确认取消
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
