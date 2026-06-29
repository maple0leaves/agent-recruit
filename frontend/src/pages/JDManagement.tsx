import { useState } from "react";
import {
  useJDs,
  useUpdateJDStatus,
  useCreateJD,
  useUpdateJD,
  useDeleteJD,
  type JDFilters,
} from "../hooks/useJDs";
import JDForm from "../components/JDs/JDForm";
import TemplateSelector from "../components/JDs/TemplateSelector";
import JDTable from "../components/JDs/JDTable";
import JDFilterBar from "../components/JDs/JDFilterBar";
import JDPagination from "../components/JDs/JDPagination";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Skeleton } from "../components/ui/skeleton";
import { AlertTriangle, FileText, Plus, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import type { JD, JDTemplate } from "../types/jd";

export default function JDManagement() {
  const [filters, setFilters] = useState<JDFilters>({
    page: 1,
    pageSize: 20,
  });
  const { data, isLoading, isPlaceholderData } = useJDs(filters);
  const updateStatusMutation = useUpdateJDStatus();
  const createMutation = useCreateJD();
  const updateMutation = useUpdateJD();
  const deleteMutation = useDeleteJD();
  const [editingJD, setEditingJD] = useState<JD | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<JD | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [showTemplateStep, setShowTemplateStep] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<JDTemplate | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleStartMatching = (jd: JD) => {
    navigate(`/matching/${jd.id}`);
  };

  const resetDialog = () => {
    setDialogOpen(false);
    setShowTemplateStep(true);
    setSelectedTemplate(null);
    setEditingJD(null);
    setSubmitError(null);
  };

  const handleFilterChange = (updates: Partial<JDFilters>) => {
    setFilters((prev) => ({ ...prev, ...updates, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handleCreateClick = () => {
    setEditingJD(null);
    setSelectedTemplate(null);
    setShowTemplateStep(true);
    setDialogOpen(true);
  };

  const handleEdit = (jd: JD) => {
    setEditingJD(jd);
    setShowTemplateStep(false);
    setSelectedTemplate(null);
    setDialogOpen(true);
  };

  const handleStatusChange = (id: number, status: string) => {
    updateStatusMutation.mutate(
      { id, status },
      {
        onError: (error) => {
          alert(`操作失败：${error.message}`);
        },
      }
    );
  };

  const handleFormSubmit = async (values: Record<string, unknown>) => {
    setSubmitError(null);
    try {
      if (editingJD) {
        await updateMutation.mutateAsync({
          id: editingJD.id,
          data: values as unknown as import("../types/jd").JDFormValues,
        });
      } else {
        await createMutation.mutateAsync(values as unknown as import("../types/jd").JDFormValues);
      }
      resetDialog();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "操作失败，请稍后重试";
      setSubmitError(message);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;

    setDeleteError(null);
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      setDeleteTarget(null);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "删除失败，请稍后重试";
      setDeleteError(message);
    }
  };

  const dialogTitle = editingJD
    ? "编辑 JD"
    : showTemplateStep
      ? "选择 JD 模板"
      : "新建 JD";
  const dialogDescription = editingJD
    ? "调整岗位信息后保存，新的 JD 会继续参与后续匹配流程。"
    : showTemplateStep
      ? "先选一个模板快速开始，也可以跳过模板从空白 JD 填起。"
      : "填写岗位基础信息、筛选条件和完整职位描述。";

  return (
    <div className="flex flex-col gap-6 py-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">JD 管理</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            维护岗位需求，发起候选人匹配。
          </p>
        </div>
        <Button onClick={handleCreateClick} className="gap-2">
          <Plus className="size-4" />
          新建 JD
        </Button>
      </div>

      <JDFilterBar
        filters={filters}
        onFilterChange={handleFilterChange}
      />

      {isLoading && !isPlaceholderData ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : data?.items.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed py-16 text-muted-foreground">
          <FileText className="size-12" />
          <p>暂无 JD 数据，点击右上角按钮创建。</p>
        </div>
      ) : (
        <JDTable
          data={data?.items || []}
          onEdit={handleEdit}
          onDelete={(jd) => {
            setDeleteError(null);
            setDeleteTarget(jd);
          }}
          onStatusChange={handleStatusChange}
          onStartMatching={handleStartMatching}
        />
      )}

      {!isLoading && data && data.total > 0 && (
        <JDPagination
          page={filters.page}
          pageSize={filters.pageSize}
          total={data.total}
          onPageChange={handlePageChange}
        />
      )}

      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) resetDialog(); }}>
        <DialogContent className="h-[min(760px,calc(100vh-2rem))] w-[min(760px,calc(100vw-2rem))] max-w-none sm:max-w-none grid-rows-[auto_minmax(0,1fr)] gap-0 overflow-hidden p-0">
          <DialogHeader className="border-b bg-muted/30 px-6 py-5 pr-14">
            <DialogTitle className="text-xl">{dialogTitle}</DialogTitle>
            <DialogDescription>{dialogDescription}</DialogDescription>
          </DialogHeader>

          <div
            className={
              showTemplateStep && !editingJD
                ? "min-h-0 overflow-hidden px-6 py-5"
                : "min-h-0 overflow-y-auto px-6 py-5"
            }
          >
            {showTemplateStep && !editingJD ? (
              <TemplateSelector
                selectedName={selectedTemplate?.name}
                onSelect={(template) => {
                  setSelectedTemplate(template);
                  setShowTemplateStep(false);
                }}
              />
            ) : (
              <>
                {submitError && (
                  <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                    {submitError}
                  </div>
                )}
                <JDForm
                  mode={editingJD ? "edit" : "create"}
                  defaultValues={
                    editingJD
                      ? {
                          title: editingJD.title,
                          department: editingJD.department,
                          skills: editingJD.skills,
                          experience_years: editingJD.experience_years,
                          education: editingJD.education,
                          salary_min: editingJD.salary_min,
                          salary_max: editingJD.salary_max,
                          description: editingJD.description,
                        }
                      : undefined
                  }
                  templateValues={selectedTemplate}
                  onSubmit={handleFormSubmit}
                  onCancel={() => {
                    if (!editingJD && !showTemplateStep) {
                      setShowTemplateStep(true);
                      setSelectedTemplate(null);
                    } else {
                      resetDialog();
                    }
                  }}
                  isSubmitting={createMutation.isPending || updateMutation.isPending}
                />
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

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
            <DialogTitle>删除 JD</DialogTitle>
            <DialogDescription>
              确认删除“{deleteTarget?.title}”？删除后该 JD 将从列表中移除，不能直接恢复。
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
    </div>
  );
}
