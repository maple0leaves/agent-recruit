import { Badge } from "@/components/ui/badge";
import type { CandidateStatus } from "@/types/candidate";

interface PipelineStatusBadgeProps {
  status: CandidateStatus;
}

const STATUS_CONFIG: Record<
  CandidateStatus,
  { label: string; variant: "default" | "secondary" | "outline" | "destructive" }
> = {
  new: { label: "新入库", variant: "outline" },
  screening: { label: "筛选中", variant: "secondary" },
  interview: { label: "面试", variant: "default" },
  hired: { label: "已录用", variant: "default" },
  rejected: { label: "不合适", variant: "destructive" },
};

export default function PipelineStatusBadge({ status }: PipelineStatusBadgeProps) {
  const { label, variant } = STATUS_CONFIG[status];

  return (
    <Badge
      variant={variant}
      className={
        status === "hired"
          ? "bg-green-100 text-green-800 hover:bg-green-100 border-green-200"
          : undefined
      }
    >
      {label}
    </Badge>
  );
}
