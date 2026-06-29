import { useMemo, useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import PipelineStatusBadge from "./PipelineStatusBadge";
import { Loader2, Trash2 } from "lucide-react";
import type { Candidate, CandidateParseStatus } from "@/types/candidate";

interface CandidateTableProps {
  data: Candidate[];
  onSelect: (candidate: Candidate) => void;
  onDelete: (candidate: Candidate) => void;
}

const PARSE_STATUS_CONFIG: Record<
  CandidateParseStatus,
  { label: string; className: string }
> = {
  pending: {
    label: "待解析",
    className: "border-muted-foreground/30 text-muted-foreground",
  },
  parsing: {
    label: "解析中",
    className: "border-blue-200 bg-blue-50 text-blue-700",
  },
  parsed: {
    label: "已解析",
    className: "border-green-200 bg-green-50 text-green-700",
  },
  failed: {
    label: "解析失败",
    className: "border-destructive/30 bg-destructive/10 text-destructive",
  },
};

function ParseStatusBadge({ status }: { status: CandidateParseStatus }) {
  const config = PARSE_STATUS_CONFIG[status] ?? PARSE_STATUS_CONFIG.pending;

  return (
    <Badge variant="outline" className={config.className}>
      {status === "parsing" && <Loader2 className="size-3 animate-spin" />}
      {config.label}
    </Badge>
  );
}

export default function CandidateTable({
  data,
  onSelect,
  onDelete,
}: CandidateTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns = useMemo<ColumnDef<Candidate>[]>(
    () => [
      {
        accessorKey: "name",
        header: "姓名",
        enableSorting: true,
        cell: ({ row }) => {
          const candidate = row.original;
          return candidate.name || "解析中候选人";
        },
      },
      {
        accessorKey: "skills",
        header: "技能",
        enableSorting: false,
        cell: ({ row }) => {
          const { skills, parse_status } = row.original;
          if (!skills && parse_status === "parsing") {
            return <span className="text-muted-foreground">等待后台解析</span>;
          }
          if (!skills) return "";
          return skills.length > 50 ? `${skills.slice(0, 50)}...` : skills;
        },
      },
      {
        id: "parse_status",
        header: "解析状态",
        cell: ({ row }) => (
          <ParseStatusBadge status={row.original.parse_status} />
        ),
      },
      {
        id: "status",
        header: "流程状态",
        cell: ({ row }) => <PipelineStatusBadge status={row.original.status} />,
      },
      {
        accessorKey: "created_at",
        header: "上传日期",
        cell: ({ row }) => {
          const date = new Date(row.original.created_at);
          return date.toLocaleDateString("zh-CN");
        },
      },
      {
        id: "actions",
        header: "操作",
        enableSorting: false,
        cell: ({ row }) => {
          const candidate = row.original;
          const name = candidate.name || "该候选人";

          return (
            <Button
              type="button"
              variant="destructive"
              size="icon-sm"
              aria-label={`删除 ${name}`}
              title={`删除 ${name}`}
              onClick={(event) => {
                event.stopPropagation();
                onDelete(candidate);
              }}
            >
              <Trash2 className="size-4" />
            </Button>
          );
        },
      },
    ],
    [onDelete],
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map((headerGroup) => (
          <TableRow key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <TableHead key={header.id}>
                {header.isPlaceholder
                  ? null
                  : flexRender(
                      header.column.columnDef.header,
                      header.getContext(),
                    )}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.length === 0 ? (
          <TableRow>
            <TableCell
              colSpan={6}
              className="py-8 text-center text-muted-foreground"
            >
              暂无候选人数据
            </TableCell>
          </TableRow>
        ) : (
          table.getRowModel().rows.map((row) => (
            <TableRow
              key={row.id}
              className="cursor-pointer hover:bg-muted/50"
              onClick={() => onSelect(row.original)}
            >
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}
