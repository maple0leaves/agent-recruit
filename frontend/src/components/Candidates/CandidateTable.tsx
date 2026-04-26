import { useState, useMemo } from "react";
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
import PipelineStatusBadge from "./PipelineStatusBadge";
import type { Candidate } from "@/types/candidate";

interface CandidateTableProps {
  data: Candidate[];
  onSelect: (candidate: Candidate) => void;
}

export default function CandidateTable({ data, onSelect }: CandidateTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns = useMemo<ColumnDef<Candidate>[]>(
    () => [
      {
        accessorKey: "name",
        header: "姓名",
        enableSorting: true,
      },
      {
        accessorKey: "skills",
        header: "技能",
        enableSorting: false,
        cell: ({ row }) => {
          const skills = row.original.skills;
          if (!skills) return "";
          return skills.length > 50 ? `${skills.slice(0, 50)}...` : skills;
        },
      },
      {
        id: "status",
        header: "状态",
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
    ],
    []
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
                      header.getContext()
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
              colSpan={4}
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
