import { useState } from "react";
import {
  useJDs,
  useUpdateJDStatus,
  useCreateJD,
  useUpdateJD,
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
import { FileText } from "lucide-react";
import {
  Dialog,
  DialogContent,
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
  const [editingJD, setEditingJD] = useState<JD | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [showTemplateStep, setShowTemplateStep] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<JDTemplate | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
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

  const handleEdit = (jd: JD) => {
    setEditingJD(jd);
    setDialogOpen(true);
  };

  const handleStatusChange = (id: number, status: string) => {
    updateStatusMutation.mutate(
      { id, status },
      {
        onError: (error) => {
          alert(`操作失败: ${error.message}`);
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
          data: values as import("../types/jd").JDFormValues,
        });
      } else {
        await createMutation.mutateAsync(values as import("../types/jd").JDFormValues);
      }
      resetDialog();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "操作失败，请稍后重试";
      setSubmitError(message);
    }
  };

  return (
    <div className="flex flex-col gap-6 py-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">JD管理</h1>
        <Button
          onClick={() => {
            setEditingJD(null);
            setSelectedTemplate(null);
            setShowTemplateStep(true);
            setDialogOpen(true);
          }}
        >
          新建 JD
        </Button>
      </div>

      {/* Filter bar */}
      <JDFilterBar
        filters={filters}
        onFilterChange={handleFilterChange}
      />

      {/* Table section */}
      {isLoading && !isPlaceholderData ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : data?.items.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-16 text-muted-foreground">
          <FileText className="h-12 w-12" />
          <p>暂无JD数据，点击上方按钮创建</p>
        </div>
      ) : (
        <JDTable
          data={data?.items || []}
          onEdit={handleEdit}
          onStatusChange={handleStatusChange}
          onStartMatching={handleStartMatching}
        />
      )}

      {/* Pagination */}
      {!isLoading && data && data.total > 0 && (
        <JDPagination
          page={filters.page}
          pageSize={filters.pageSize}
          total={data.total}
          onPageChange={handlePageChange}
        />
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) resetDialog(); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingJD ? "编辑JD" : showTemplateStep ? "选择模板" : "新建JD"}
            </DialogTitle>
          </DialogHeader>

          {showTemplateStep && !editingJD ? (
            <>
              <TemplateSelector
                selectedName={selectedTemplate?.name}
                onSelect={(template) => {
                  setSelectedTemplate(template);
                  setShowTemplateStep(false);
                }}
              />
              <div className="text-center mt-4">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setSelectedTemplate(null);
                    setShowTemplateStep(false);
                  }}
                >
                  跳过模板，手动填写
                </Button>
              </div>
            </>
          ) : (
            <>
              {submitError && (
                <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
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
                  } else {
                    resetDialog();
                  }
                }}
                isSubmitting={createMutation.isPending || updateMutation.isPending}
              />
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
