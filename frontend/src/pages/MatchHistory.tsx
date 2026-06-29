import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  AlertTriangle,
  Check,
  ChevronLeft,
  ChevronRight,
  Eye,
  FileDown,
  FileSpreadsheet,
  FileText,
  History,
  Loader2,
  Pencil,
  Search,
  Trash2,
  X,
} from "lucide-react";
import {
  deleteMatchSession,
  fetchMatchSession,
  fetchMatchSessions,
  fetchMatchSessionResumePdf,
  reviewMatchSession,
  type MatchSessionItem,
  type MatchSessionResult,
} from "@/api/matchSessions";
import { getApiBaseURL } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import type { ReviewDecision } from "@/types/matching";

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  pending: {
    label: "待审核",
    className: "border-amber-500/30 bg-amber-500/15 text-amber-200",
  },
  completed: {
    label: "已完成",
    className: "border-emerald-500/30 bg-emerald-500/15 text-emerald-200",
  },
  approved: {
    label: "已通过",
    className: "border-blue-500/30 bg-blue-500/15 text-blue-200",
  },
  rejected: {
    label: "已拒绝",
    className: "border-red-500/30 bg-red-500/15 text-red-200",
  },
};

interface DecisionDraft {
  approved: boolean;
  feedback: string;
}

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_LABELS[status] || {
    label: status,
    className: "border-border bg-muted text-muted-foreground",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  );
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString("zh-CN");
}

function scoreValue(value: number) {
  const parsed = Number(value);
  if (Number.isNaN(parsed)) return 0;
  return Math.max(0, Math.min(100, Math.round(parsed)));
}

function asSkillList(value: string[] | undefined) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function exportSession(sessionId: number, format: "pdf" | "excel") {
  const baseUrl = getApiBaseURL().replace(/\/$/, "");
  window.open(`${baseUrl}/matching/${sessionId}/export/${format}`, "_blank");
}

function CandidateReviewCard({
  result,
  draft,
  disabled,
  onDecisionChange,
  onFeedbackChange,
  onViewResume,
}: {
  result: MatchSessionResult;
  draft: DecisionDraft | undefined;
  disabled: boolean;
  onDecisionChange: (approved: boolean) => void;
  onFeedbackChange: (feedback: string) => void;
  onViewResume: () => void;
}) {
  const score = scoreValue(result.match_score);
  const matchedSkills = asSkillList(result.matched_skills);
  const missingSkills = asSkillList(result.missing_skills);
  const reviewStatus = result.review_status;
  const currentApproved = draft?.approved ?? result.should_proceed;

  return (
    <article className="rounded-lg border bg-card p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="truncate text-base font-semibold">{result.candidate_name}</h3>
            {reviewStatus && <StatusBadge status={reviewStatus} />}
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            AI 建议：{result.should_proceed ? "建议进入下一轮" : "建议暂缓"}
          </p>
        </div>
        <div className="flex shrink-0 items-start gap-3">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onViewResume}
            className="gap-1"
          >
            <FileText className="size-3.5" />
            查看简历
          </Button>
          <div className="text-right">
            <div className="text-2xl font-semibold text-primary">{score}</div>
            <div className="text-xs text-muted-foreground">匹配分</div>
          </div>
        </div>
      </div>

      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${score}%` }} />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div>
          <div className="mb-2 text-xs font-medium text-muted-foreground">匹配技能</div>
          <div className="flex flex-wrap gap-1.5">
            {matchedSkills.length > 0 ? (
              matchedSkills.map((skill) => (
                <Badge key={skill} variant="secondary">
                  {skill}
                </Badge>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">暂无</span>
            )}
          </div>
        </div>
        <div>
          <div className="mb-2 text-xs font-medium text-muted-foreground">缺口技能</div>
          <div className="flex flex-wrap gap-1.5">
            {missingSkills.length > 0 ? (
              missingSkills.map((skill) => (
                <Badge key={skill} variant="outline">
                  {skill}
                </Badge>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">暂无明显缺口</span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 rounded-lg bg-muted/40 p-3 text-sm text-muted-foreground">
        {result.recommendation || result.summary || "暂无推荐说明"}
      </div>

      <div className="mt-4 space-y-3 border-t pt-4">
        <div className="flex items-center justify-between gap-3">
          <div className="text-sm font-medium">HR 审核</div>
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant={currentApproved ? "default" : "outline"}
              disabled={disabled}
              onClick={() => onDecisionChange(true)}
              className="gap-1"
            >
              <Check className="size-3.5" />
              通过
            </Button>
            <Button
              type="button"
              size="sm"
              variant={!currentApproved ? "destructive" : "outline"}
              disabled={disabled}
              onClick={() => onDecisionChange(false)}
              className="gap-1"
            >
              <X className="size-3.5" />
              拒绝
            </Button>
          </div>
        </div>
        <Textarea
          value={draft?.feedback ?? result.review_feedback ?? ""}
          disabled={disabled}
          onChange={(event) => onFeedbackChange(event.target.value)}
          placeholder="填写审核备注，例如进入面试、暂缓原因或后续跟进点"
          className="min-h-20 resize-none"
        />
      </div>
    </article>
  );
}

export default function MatchHistory() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
  const [openReviewInEdit, setOpenReviewInEdit] = useState(false);
  const [isEditingReview, setIsEditingReview] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<MatchSessionItem | null>(null);
  const [resumePreview, setResumePreview] = useState<MatchSessionResult | null>(null);
  const [reviewDraft, setReviewDraft] = useState<Record<string, DecisionDraft>>({});
  const pageSize = 10;

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearchKeyword(searchInput.trim());
      setPage(1);
    }, 300);

    return () => window.clearTimeout(timer);
  }, [searchInput]);

  const { data, isLoading } = useQuery({
    queryKey: ["match-sessions", page, statusFilter, searchKeyword],
    queryFn: () =>
      fetchMatchSessions({
        page,
        page_size: pageSize,
        status: statusFilter || undefined,
        keyword: searchKeyword || undefined,
      }),
  });

  const detailQuery = useQuery({
    queryKey: ["match-session", selectedSessionId],
    queryFn: () => {
      if (selectedSessionId === null) {
        throw new Error("缺少匹配记录 ID");
      }
      return fetchMatchSession(selectedSessionId);
    },
    enabled: selectedSessionId !== null,
  });

  const detail = detailQuery.data;
  const selectedSummary = useMemo(
    () => data?.items.find((session) => session.id === selectedSessionId) ?? null,
    [data?.items, selectedSessionId],
  );

  useEffect(() => {
    if (!detail) return;

    const nextDraft: Record<string, DecisionDraft> = {};
    for (const result of detail.results) {
      nextDraft[result.candidate_name] = {
        approved: result.review_status
          ? result.review_status === "approved"
          : result.should_proceed,
        feedback: result.review_feedback ?? "",
      };
    }
    setReviewDraft(nextDraft);
    setIsEditingReview(detail.status === "pending" || openReviewInEdit);
  }, [detail?.id, detail?.updated_at, detail?.status, openReviewInEdit]);

  const reviewMutation = useMutation({
    mutationFn: async () => {
      if (!detail) {
        throw new Error("匹配详情尚未加载完成");
      }

      const approvals: ReviewDecision[] = detail.results.map((result) => ({
        candidate_name: result.candidate_name,
        approved: reviewDraft[result.candidate_name]?.approved ?? false,
        feedback: reviewDraft[result.candidate_name]?.feedback ?? "",
      }));

      return reviewMatchSession(detail.id, approvals);
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(["match-session", updated.id], updated);
      queryClient.invalidateQueries({ queryKey: ["match-sessions"] });
      setOpenReviewInEdit(false);
      setIsEditingReview(updated.status === "pending");
      toast.success("审核结果已保存");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteMatchSession(id),
    onSuccess: (_data, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ["match-sessions"] });
      queryClient.removeQueries({ queryKey: ["match-session", deletedId] });
      if (selectedSessionId === deletedId) {
        setSelectedSessionId(null);
        setResumePreview(null);
      }
      setDeleteTarget(null);
      toast.success("匹配记录已删除");
    },
  });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;
  const sessions = data?.items ?? [];
  const drawerTitle = detail?.jd_title || selectedSummary?.jd_title || `匹配记录 #${selectedSessionId ?? "-"}`;
  const isPendingReview = detail?.status === "pending";
  const canEditReview = Boolean(detail && detail.results.length > 0 && (isPendingReview || isEditingReview));
  const canSubmitReview = canEditReview;
  const hasActiveFilters = searchInput.trim().length > 0 || statusFilter !== "";
  const resumePreviewName = resumePreview?.candidate_name ?? "";
  const resumePdfQuery = useQuery({
    queryKey: ["match-session-resume-pdf", selectedSessionId, resumePreviewName],
    queryFn: () => {
      if (selectedSessionId === null || !resumePreviewName) {
        throw new Error("缺少简历预览参数");
      }
      return fetchMatchSessionResumePdf(selectedSessionId, resumePreviewName);
    },
    enabled: selectedSessionId !== null && Boolean(resumePreview),
    staleTime: 5 * 60_000,
  });
  const [resumePreviewUrl, setResumePreviewUrl] = useState("");

  useEffect(() => {
    if (!resumePdfQuery.data) {
      setResumePreviewUrl("");
      return;
    }

    const pdfBlob = new Blob([resumePdfQuery.data], { type: "application/pdf" });
    const objectUrl = URL.createObjectURL(pdfBlob);
    setResumePreviewUrl(objectUrl);

    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [resumePdfQuery.data]);

  const updateDecision = (candidateName: string, approved: boolean) => {
    setReviewDraft((prev) => ({
      ...prev,
      [candidateName]: {
        approved,
        feedback: prev[candidateName]?.feedback ?? "",
      },
    }));
  };

  const updateFeedback = (candidateName: string, feedback: string) => {
    setReviewDraft((prev) => ({
      ...prev,
      [candidateName]: {
        approved: prev[candidateName]?.approved ?? false,
        feedback,
      },
    }));
  };

  return (
    <div className="space-y-6 py-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <History className="size-6 text-primary" />
          <div>
            <h1 className="text-2xl font-semibold">匹配历史</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              查看每次智能匹配结果，并处理待审核候选人。
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {["", "pending", "completed"].map((status) => (
            <Button
              key={status || "all"}
              variant={statusFilter === status ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setStatusFilter(status);
                setPage(1);
              }}
            >
              {status === "" ? "全部" : STATUS_LABELS[status]?.label || status}
            </Button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-lg border bg-card p-3 md:flex-row md:items-center">
        <div className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="搜索职位、候选人、记录 ID 或匹配内容"
            className="pl-8"
          />
        </div>
        <Button
          variant="ghost"
          size="sm"
          disabled={!hasActiveFilters}
          onClick={() => {
            setSearchInput("");
            setSearchKeyword("");
            setStatusFilter("");
            setPage(1);
          }}
          className="md:w-fit"
        >
          清空筛选
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-12 w-full" />
          ))}
        </div>
      ) : sessions.length === 0 ? (
        <div className="rounded-lg border border-dashed py-16 text-center text-muted-foreground">
          暂无匹配记录
        </div>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border">
            <Table>
              <TableHeader className="bg-muted/50">
                <TableRow>
                  <TableHead className="px-3">职位</TableHead>
                  <TableHead className="px-3">状态</TableHead>
                  <TableHead className="px-3 text-center">候选人数</TableHead>
                  <TableHead className="px-3 text-center">通过</TableHead>
                  <TableHead className="px-3 text-center">拒绝</TableHead>
                  <TableHead className="px-3">创建时间</TableHead>
                  <TableHead className="px-3 text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.map((session: MatchSessionItem) => (
                  <TableRow
                    key={session.id}
                    className="cursor-pointer"
                    onClick={() => {
                      setOpenReviewInEdit(false);
                      setSelectedSessionId(session.id);
                    }}
                  >
                    <TableCell className="px-3 font-medium">
                      {session.jd_title || `JD #${session.jd_id || "-"}`}
                    </TableCell>
                    <TableCell className="px-3">
                      <StatusBadge status={session.status} />
                    </TableCell>
                    <TableCell className="px-3 text-center">{session.total_candidates}</TableCell>
                    <TableCell className="px-3 text-center text-emerald-400">
                      {session.approved_count}
                    </TableCell>
                    <TableCell className="px-3 text-center text-red-400">
                      {session.rejected_count}
                    </TableCell>
                    <TableCell className="px-3 text-muted-foreground">
                      {formatDate(session.created_at)}
                    </TableCell>
                    <TableCell className="px-3">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(event) => {
                            event.stopPropagation();
                            setOpenReviewInEdit(false);
                            setSelectedSessionId(session.id);
                          }}
                          className="gap-1"
                        >
                          <Eye className="size-3.5" />
                          {session.status === "pending" ? "审核" : "查看"}
                        </Button>
                        {session.status !== "pending" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(event) => {
                              event.stopPropagation();
                              setOpenReviewInEdit(true);
                              setSelectedSessionId(session.id);
                            }}
                            className="gap-1"
                          >
                            <Pencil className="size-3.5" />
                            修改
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label="导出 PDF"
                          onClick={(event) => {
                            event.stopPropagation();
                            exportSession(session.id, "pdf");
                          }}
                        >
                          <FileDown className="size-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          aria-label="删除记录"
                          onClick={(event) => {
                            event.stopPropagation();
                            setDeleteTarget(session);
                          }}
                        >
                          <Trash2 className="size-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">共 {data?.total ?? 0} 条记录</p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((current) => current - 1)}
              >
                <ChevronLeft className="size-4" />
              </Button>
              <span className="text-sm leading-8">
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((current) => current + 1)}
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
        </>
      )}

      <Dialog
        open={selectedSessionId !== null}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedSessionId(null);
            setResumePreview(null);
            setOpenReviewInEdit(false);
            setIsEditingReview(false);
          }
        }}
      >
        <DialogContent className="grid h-[min(860px,calc(100vh-2rem))] w-[min(1120px,calc(100vw-2rem))] max-w-none grid-rows-[auto_minmax(0,1fr)_auto] gap-0 overflow-hidden p-0 sm:max-w-none">
          <DialogHeader className="border-b bg-muted/30 px-6 py-5 pr-14">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <DialogTitle className="text-xl">{drawerTitle}</DialogTitle>
                <DialogDescription>
                  {detail
                    ? `${formatDate(detail.created_at)} · ${detail.total_candidates} 位候选人`
                    : "正在加载匹配详情"}
                </DialogDescription>
              </div>
              {detail && <StatusBadge status={detail.status} />}
            </div>
          </DialogHeader>

          <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
            {detailQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-56 w-full" />
                <Skeleton className="h-56 w-full" />
              </div>
            ) : detailQuery.isError ? (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                匹配详情加载失败，请稍后重试。
              </div>
            ) : !detail || detail.results.length === 0 ? (
              <div className="rounded-lg border border-dashed py-16 text-center text-muted-foreground">
                这条记录还没有可审核的候选人结果。
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-lg border bg-card p-3">
                    <div className="text-xs text-muted-foreground">候选人数</div>
                    <div className="mt-1 text-2xl font-semibold">{detail.total_candidates}</div>
                  </div>
                  <div className="rounded-lg border bg-card p-3">
                    <div className="text-xs text-muted-foreground">已通过</div>
                    <div className="mt-1 text-2xl font-semibold text-emerald-400">
                      {detail.approved_count}
                    </div>
                  </div>
                  <div className="rounded-lg border bg-card p-3">
                    <div className="text-xs text-muted-foreground">已拒绝</div>
                    <div className="mt-1 text-2xl font-semibold text-red-400">
                      {detail.rejected_count}
                    </div>
                  </div>
                </div>

                {isPendingReview && (
                  <div className="rounded-lg border border-primary/25 bg-primary/10 p-3 text-sm text-muted-foreground">
                    可按 AI 建议快速审核，也可以逐个调整通过/拒绝并填写备注。
                  </div>
                )}

                {detail.results.map((result) => (
                  <CandidateReviewCard
                    key={result.candidate_name}
                    result={result}
                    draft={reviewDraft[result.candidate_name]}
                    disabled={!canEditReview || reviewMutation.isPending}
                    onDecisionChange={(approved) => updateDecision(result.candidate_name, approved)}
                    onFeedbackChange={(feedback) => updateFeedback(result.candidate_name, feedback)}
                    onViewResume={() => setResumePreview(result)}
                  />
                ))}
              </div>
            )}
          </div>

          <DialogFooter className="m-0 rounded-none border-t bg-background px-6 py-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex gap-2">
                {detail && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => exportSession(detail.id, "pdf")}
                      className="gap-1"
                    >
                      <FileDown className="size-3.5" />
                      导出 PDF
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => exportSession(detail.id, "excel")}
                      className="gap-1"
                    >
                      <FileSpreadsheet className="size-3.5" />
                      导出 Excel
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setDeleteTarget(detail)}
                      className="gap-1"
                    >
                      <Trash2 className="size-3.5" />
                      删除记录
                    </Button>
                  </>
                )}
              </div>
              <div className="flex gap-2 sm:justify-end">
                <Button variant="outline" onClick={() => setSelectedSessionId(null)}>
                  关闭
                </Button>
                {detail && detail.status !== "pending" && !isEditingReview && detail.results.length > 0 && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setOpenReviewInEdit(true);
                      setIsEditingReview(true);
                    }}
                    className="gap-2"
                  >
                    <Pencil className="size-4" />
                    修改审核
                  </Button>
                )}
                {canSubmitReview && (
                  <Button
                    onClick={() => reviewMutation.mutate()}
                    disabled={reviewMutation.isPending}
                    className="gap-2"
                  >
                    {reviewMutation.isPending && <Loader2 className="size-4 animate-spin" />}
                    {isPendingReview ? "完成审核" : "保存修改"}
                  </Button>
                )}
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteTarget(null);
          }
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <div className="mb-2 flex size-10 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
              <AlertTriangle className="size-5" />
            </div>
            <DialogTitle>删除匹配记录</DialogTitle>
            <DialogDescription>
              确认删除“{deleteTarget?.jd_title || `记录 #${deleteTarget?.id ?? ""}`}”？删除后该次匹配结果、审核备注和导出记录都不能直接恢复。
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setDeleteTarget(null)}
            >
              取消
            </Button>
            <Button
              type="button"
              variant="destructive"
              disabled={deleteMutation.isPending || !deleteTarget}
              onClick={() => {
                if (deleteTarget) {
                  deleteMutation.mutate(deleteTarget.id);
                }
              }}
              className="gap-2"
            >
              <Trash2 className="size-4" />
              {deleteMutation.isPending ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={resumePreview !== null}
        onOpenChange={(open) => {
          if (!open) {
            setResumePreview(null);
          }
        }}
      >
        <DialogContent className="grid h-[min(760px,calc(100vh-2rem))] w-[min(920px,calc(100vw-2rem))] max-w-none grid-rows-[auto_minmax(0,1fr)_auto] gap-0 overflow-hidden p-0 sm:max-w-none">
          <DialogHeader className="border-b bg-muted/30 px-6 py-5 pr-14">
            <DialogTitle className="text-xl">
              {resumePreview ? `${resumePreview.candidate_name} 的简历` : "候选人简历"}
            </DialogTitle>
            <DialogDescription>原始上传 PDF 预览</DialogDescription>
          </DialogHeader>

          <div className="min-h-0 px-6 py-5">
            {resumePdfQuery.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-10 w-48" />
                <Skeleton className="h-[560px] w-full" />
              </div>
            ) : resumePdfQuery.isError ? (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 py-16 text-center text-sm text-destructive">
                原始 PDF 加载失败，请确认该候选人的原始简历文件仍然存在。
              </div>
            ) : resumePreviewUrl ? (
              <iframe
                title={resumePreview ? `${resumePreview.candidate_name} 的原始简历 PDF` : "原始简历 PDF"}
                src={resumePreviewUrl}
                className="h-full min-h-[560px] w-full rounded-lg border bg-muted"
              />
            ) : (
              <div className="rounded-lg border border-dashed py-16 text-center text-muted-foreground">
                这条匹配记录没有可预览的原始 PDF。
              </div>
            )}
          </div>

          <DialogFooter className="m-0 rounded-none border-t bg-background px-6 py-4">
            <Button variant="outline" onClick={() => setResumePreview(null)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
