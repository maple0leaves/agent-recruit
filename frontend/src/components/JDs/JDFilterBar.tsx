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
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { type DateRange } from "react-day-picker";
import type { JDFilters } from "@/hooks/useJDs";

interface JDFilterBarProps {
  filters: JDFilters;
  onFilterChange: (filters: Partial<JDFilters>) => void;
}

export default function JDFilterBar({ filters, onFilterChange }: JDFilterBarProps) {
  const [searchInput, setSearchInput] = useState("");
  const [date, setDate] = useState<DateRange | undefined>();
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const handleSearchChange = (value: string) => {
    setSearchInput(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onFilterChange({ keyword: value || undefined });
    }, 300);
  };

  const handleReset = () => {
    setSearchInput("");
    setDate(undefined);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    onFilterChange({
      keyword: undefined,
      status: undefined,
      dateFrom: undefined,
      dateTo: undefined,
    });
  };

  const formatDateRange = () => {
    if (!date?.from) return "日期范围";
    if (!date?.to) return format(date.from, "yyyy-MM-dd");
    return `${format(date.from, "yyyy-MM-dd")} - ${format(date.to, "yyyy-MM-dd")}`;
  };

  return (
    <div className="flex flex-wrap items-center gap-4">
      <Input
        placeholder="搜索职位名称/部门/技能..."
        className="w-64"
        value={searchInput}
        onChange={(e) => handleSearchChange(e.target.value)}
      />
      <Select
        value={filters.status || "all"}
        onValueChange={(value) =>
          onFilterChange({ status: value === "all" ? undefined : value as string | undefined })
        }
      >
        <SelectTrigger className="w-[130px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部</SelectItem>
          <SelectItem value="draft">草稿</SelectItem>
          <SelectItem value="active">发布中</SelectItem>
          <SelectItem value="closed">已关闭</SelectItem>
        </SelectContent>
      </Select>
      <Popover>
        <PopoverTrigger
          render={
            <Button
              variant="outline"
              className="w-[240px] justify-start text-left font-normal"
            />
          }
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {formatDateRange()}
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="range"
            selected={date}
            onSelect={(range) => {
              setDate(range);
              if (range?.from && range?.to) {
                onFilterChange({
                  dateFrom: format(range.from, "yyyy-MM-dd"),
                  dateTo: format(range.to, "yyyy-MM-dd"),
                });
              }
            }}
          />
          {date?.from && (
            <div className="border-t p-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setDate(undefined);
                  onFilterChange({
                    dateFrom: undefined,
                    dateTo: undefined,
                  });
                }}
              >
                清除日期
              </Button>
            </div>
          )}
        </PopoverContent>
      </Popover>
      <Button variant="ghost" size="sm" onClick={handleReset}>
        重置
      </Button>
    </div>
  );
}
