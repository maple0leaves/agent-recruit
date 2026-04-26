import { useState, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { CandidateFilters } from "@/hooks/useCandidates";

interface CandidateFilterBarProps {
  filters: CandidateFilters;
  onFilterChange: (filters: Partial<CandidateFilters>) => void;
}

export default function CandidateFilterBar({ filters, onFilterChange }: CandidateFilterBarProps) {
  const [searchInput, setSearchInput] = useState(filters.keyword || "");
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const handleSearchChange = (value: string) => {
    setSearchInput(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onFilterChange({ keyword: value || undefined });
    }, 300);
  };

  const handleReset = () => {
    setSearchInput("");
    if (debounceRef.current) clearTimeout(debounceRef.current);
    onFilterChange({ keyword: undefined, status: undefined });
  };

  return (
    <div className="flex flex-wrap items-center gap-4">
      <Input
        placeholder="搜索姓名/技能..."
        className="w-64"
        value={searchInput}
        onChange={(e) => handleSearchChange(e.target.value)}
      />
      <Select
        value={filters.status || "all"}
        onValueChange={(value) =>
          onFilterChange({ status: value === "all" ? undefined : value })
        }
      >
        <SelectTrigger className="w-[130px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部状态</SelectItem>
          <SelectItem value="new">新入库</SelectItem>
          <SelectItem value="screening">筛选中</SelectItem>
          <SelectItem value="interview">面试</SelectItem>
          <SelectItem value="hired">已录用</SelectItem>
          <SelectItem value="rejected">不合适</SelectItem>
        </SelectContent>
      </Select>
      <Button variant="ghost" size="sm" onClick={handleReset}>
        重置
      </Button>
    </div>
  );
}
