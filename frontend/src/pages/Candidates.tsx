import { useState } from "react";
import {
  useCandidates,
  useDeleteCandidate,
  type CandidateFilters,
} from "../hooks/useCandidates";
import CandidateTable from "../components/Candidates/CandidateTable";
import CandidateFilterBar from "../components/Candidates/CandidateFilterBar";
import CandidateUpload from "../components/Candidates/CandidateUpload";
import CandidateDetail from "../components/Candidates/CandidateDetail";
import { Button } from "../components/ui/button";
import { Skeleton } from "../components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Upload,
  Users,
} from "lucide-react";
import type { Candidate, CandidateBatchUploadResponse } from "../types/candidate";

export default function Candidates() {
  const [filters, setFilters] = useState<CandidateFilters>({
    page: 1,
    pageSize: 20,
  });
  const { data, isLoading, isPlaceholderData } = useCandidates(filters);
  const deleteMutation = useDeleteCandidate();
  const [selectedCandidateId, setSelectedCandidateId] = useState<number | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Candidate | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleFilterChange = (updates: Partial<CandidateFilters>) => {
    setFilters((prev) => ({ ...prev, ...updates, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handleSelect = (candidate: Candidate) => {
    setSelectedCandidateId(candidate.id);
  };

  const handleUploadSuccess = (_result: CandidateBatchUploadResponse) => {
    setFilters((prev) => ({ ...prev, page: 1 }));
  };

  const handleBackToList = () => {
    setSelectedCandidateId(null);
  };

  const openDeleteDialog = (candidate: Candidate) => {
    setDeleteError(null);
    setDeleteTarget(candidate);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;

    setDeleteError(null);
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      if (selectedCandidateId === deleteTarget.id) {
        setSelectedCandidateId(null);
      }
      setDeleteTarget(null);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "删除失败，请稍后重试";
      setDeleteError(message);
    }
  };

  const totalPages = data ? Math.ceil(data.total / filters.pageSize) : 0;

  const getPageNumbers = (): (number | "...")[] => {
    const pages: (number | "...")[] = [];
    pages.push(1);

    const rangeStart = Math.max(2, filters.page - 2);
    const rangeEnd = Math.min(totalPages - 1, filters.page + 2);

    if (rangeStart > 2) {
      pages.push("...");
    }
    for (let i = rangeStart; i <= rangeEnd; i++) {
      pages.push(i);
    }
    if (rangeEnd < totalPages - 1) {
      pages.push("...");
    }
    if (totalPages > 1) {
      pages.push(totalPages);
    }

    return pages;
  };

  const deleteDialog = (
    <Dialog
      open={Boolean(deleteTarget)}
      onOpenChange={(open) => {
        if (!open) {
          setDeleteTarget(null);
          setDeleteError(null);
        }
      }}
    >
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="mb-2 flex size-10 items-center justify-center rounded-lg bg-destructive/10 text-destructive">
            <AlertTriangle className="size-5" />
          </div>
          <DialogTitle>删除候选人</DialogTitle>
          <DialogDescription>
            确认删除“{deleteTarget?.name || "该候选人"}”？删除后候选人记录和已上传简历文件都会被移除，不能直接恢复。
          </DialogDescription>
        </DialogHeader>

        {deleteError && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {deleteError}
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setDeleteTarget(null);
              setDeleteError(null);
            }}
          >
            取消
          </Button>
          <Button
            type="button"
            variant="destructive"
            onClick={handleDeleteConfirm}
            disabled={deleteMutation.isPending}
            className="gap-2"
          >
            <Trash2 className="size-4" />
            {deleteMutation.isPending ? "删除中..." : "确认删除"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  if (selectedCandidateId !== null) {
    return (
      <>
        <div className="py-6">
          <CandidateDetail
            candidateId={selectedCandidateId}
            onBack={handleBackToList}
            onDelete={openDeleteDialog}
          />
        </div>
        {deleteDialog}
      </>
    );
  }

  return (
    <>
      <div className="flex flex-col gap-6 py-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">候选人管理</h1>
          <Button onClick={() => setShowUpload(!showUpload)}>
            <Upload className="h-4 w-4" />
            {showUpload ? "关闭上传" : "批量上传简历"}
          </Button>
        </div>

        <CandidateFilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
        />

        {showUpload && (
          <CandidateUpload onSuccess={handleUploadSuccess} />
        )}

        {isLoading && !isPlaceholderData ? (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : data?.items.length === 0 ? (
          <div className="flex flex-col items-center gap-4 py-16 text-muted-foreground">
            <Users className="h-12 w-12" />
            <p>暂无候选人数据，请批量上传简历</p>
          </div>
        ) : (
          <CandidateTable
            data={data?.items || []}
            onSelect={handleSelect}
            onDelete={openDeleteDialog}
          />
        )}

        {!isLoading && data && data.total > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              共 {data.total} 条，第 {filters.page}/{totalPages} 页
            </span>
            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                disabled={filters.page <= 1}
                onClick={() => handlePageChange(filters.page - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              {getPageNumbers().map((p, idx) =>
                p === "..." ? (
                  <span
                    key={`ellipsis-${idx}`}
                    className="px-2 text-sm text-muted-foreground"
                  >
                    ...
                  </span>
                ) : (
                  <Button
                    key={p}
                    variant={p === filters.page ? "default" : "outline"}
                    size="sm"
                    onClick={() => handlePageChange(p)}
                  >
                    {p}
                  </Button>
                )
              )}
              <Button
                variant="outline"
                size="sm"
                disabled={filters.page >= totalPages}
                onClick={() => handlePageChange(filters.page + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
      {deleteDialog}
    </>
  );
}
