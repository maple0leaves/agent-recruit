import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchMatchSessions, type MatchSessionItem } from "@/api/matchSessions";
import { Button } from "@/components/ui/button";
import { History, FileDown, ChevronLeft, ChevronRight } from "lucide-react";

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  pending: { label: "待审核", className: "bg-yellow-100 text-yellow-800" },
  completed: { label: "已完成", className: "bg-green-100 text-green-800" },
  approved: { label: "已通过", className: "bg-blue-100 text-blue-800" },
};

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_LABELS[status] || {
    label: status,
    className: "bg-gray-100 text-gray-800",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  );
}

export default function MatchHistory() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const pageSize = 10;

  const { data, isLoading } = useQuery({
    queryKey: ["match-sessions", page, statusFilter],
    queryFn: () =>
      fetchMatchSessions({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
      }),
  });

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <History className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">匹配历史</h1>
        </div>
        <div className="flex gap-2">
          {["", "pending", "completed"].map((s) => (
            <Button
              key={s}
              variant={statusFilter === s ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setStatusFilter(s);
                setPage(1);
              }}
            >
              {s === "" ? "全部" : STATUS_LABELS[s]?.label || s}
            </Button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">加载中...</div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          暂无匹配记录
        </div>
      ) : (
        <>
          <div className="border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left p-3 font-medium">职位</th>
                  <th className="text-left p-3 font-medium">状态</th>
                  <th className="text-center p-3 font-medium">候选人数</th>
                  <th className="text-center p-3 font-medium">通过</th>
                  <th className="text-center p-3 font-medium">拒绝</th>
                  <th className="text-left p-3 font-medium">创建时间</th>
                  <th className="text-center p-3 font-medium">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.items.map((session: MatchSessionItem) => (
                  <tr key={session.id} className="hover:bg-muted/30">
                    <td className="p-3">
                      {session.jd_title || `JD #${session.jd_id || "-"}`}
                    </td>
                    <td className="p-3">
                      <StatusBadge status={session.status} />
                    </td>
                    <td className="p-3 text-center">
                      {session.total_candidates}
                    </td>
                    <td className="p-3 text-center text-green-600">
                      {session.approved_count}
                    </td>
                    <td className="p-3 text-center text-red-600">
                      {session.rejected_count}
                    </td>
                    <td className="p-3 text-muted-foreground">
                      {session.created_at
                        ? new Date(session.created_at).toLocaleString("zh-CN")
                        : "-"}
                    </td>
                    <td className="p-3 text-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          window.open(
                            `/api/matching/${session.id}/export/pdf`,
                            "_blank"
                          )
                        }
                      >
                        <FileDown className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              共 {data.total} 条记录
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm leading-8">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
