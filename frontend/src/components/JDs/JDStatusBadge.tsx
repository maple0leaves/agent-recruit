import { Badge } from "@/components/ui/badge";
import type { JDStatus } from "@/types/jd";

interface JDStatusBadgeProps {
  status: JDStatus;
}

const statusConfig: Record<JDStatus, { variant: "secondary" | "default" | "outline"; label: string }> = {
  draft: { variant: "secondary", label: "草稿" },
  active: { variant: "default", label: "发布中" },
  closed: { variant: "outline", label: "已关闭" },
};

export default function JDStatusBadge({ status }: JDStatusBadgeProps) {
  const { variant, label } = statusConfig[status];

  return (
    <Badge
      variant={variant}
      className={
        status === "active"
          ? "bg-green-100 text-green-800 hover:bg-green-100"
          : status === "closed"
            ? "text-red-500 border-red-200"
            : undefined
      }
    >
      {label}
    </Badge>
  );
}
