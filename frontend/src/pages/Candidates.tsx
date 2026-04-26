import { useState } from "react";
import { useCandidates, type CandidateFilters } from "../hooks/useCandidates";
import CandidateTable from "../components/Candidates/CandidateTable";
import CandidateFilterBar from "../components/Candidates/CandidateFilterBar";
import CandidateUpload from "../components/Candidates/CandidateUpload";
import { Button } from "../components/ui/button";
import { Skeleton } from "../components/ui/skeleton";
import { Users, Upload, ChevronLeft, ChevronRight } from "lucide-react";
import type { Candidate, CandidateUploadResponse } from "../types/candidate";

export default function Candidates() {
  const [filters, setFilters] = useState<CandidateFilters>({
    page: 1,
    pageSize: 20,
  });
  const { data, isLoading, isPlaceholderData } = useCandidates(filters);
  const [selectedCandidateId, setSelectedCandidateId] = useState<number | null>(null);
  const [showUpload, setShowUpload] = useState(false);

  const handleFilterChange = (updates: Partial<CandidateFilters>) => {
    setFilters((prev) => ({ ...prev, ...updates, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handleSelect = (candidate: Candidate) => {
    setSelectedCandidateId(candidate.id);
  };

  const handleUploadSuccess = (_candidate: CandidateUploadResponse) => {
    setFilters((prev) => ({ ...prev, page: 1 }));
    setShowUpload(false);
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

  return (
    <div className="flex flex-col gap-6 py-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">候选人管理</h1>
        <Button onClick={() => setShowUpload(!showUpload)}>
          <Upload className="h-4 w-4" />
          {showUpload ? "关闭上传" : "上传简历"}
        </Button>
      </div>

      {/* Filter bar */}
      <CandidateFilterBar
        filters={filters}
        onFilterChange={handleFilterChange}
      />

      {/* Upload widget */}
      {showUpload && (
        <CandidateUpload onSuccess={handleUploadSuccess} />
      )}

      {/* Table section */}
      {isLoading && !isPlaceholderData ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : data?.items.length === 0 ? (
        <div className="flex flex-col items-center gap-4 py-16 text-muted-foreground">
          <Users className="h-12 w-12" />
          <p>暂无候选人数据，请上传简历</p>
        </div>
      ) : (
        <CandidateTable
          data={data?.items || []}
          onSelect={handleSelect}
        />
      )}

      {/* Pagination */}
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
  );
}
