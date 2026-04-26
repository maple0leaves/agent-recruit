import { useState } from "react";
import { useJDs, useUpdateJDStatus, type JDFilters } from "../hooks/useJDs";
import JDTable from "../components/JDs/JDTable";
import JDFilterBar from "../components/JDs/JDFilterBar";
import JDPagination from "../components/JDs/JDPagination";
import { Button } from "../components/ui/button";
import { Skeleton } from "../components/ui/skeleton";
import { FileText } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import type { JD } from "../types/jd";

export default function JDManagement() {
  const [filters, setFilters] = useState<JDFilters>({
    page: 1,
    pageSize: 20,
  });
  const { data, isLoading, isPlaceholderData } = useJDs(filters);
  const updateStatusMutation = useUpdateJDStatus();
  const [editingJD, setEditingJD] = useState<JD | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

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

  return (
    <div className="flex flex-col gap-6 py-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">JD管理</h1>
        <Button onClick={() => {}}>新建 JD</Button>
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

      {/* Edit dialog placeholder (Plan 04 integration point) */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingJD ? `编辑 - ${editingJD.title}` : "新建 JD"}
            </DialogTitle>
          </DialogHeader>
          <p className="text-muted-foreground">编辑功能</p>
        </DialogContent>
      </Dialog>
    </div>
  );
}
