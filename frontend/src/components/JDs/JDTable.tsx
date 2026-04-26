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
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal } from "lucide-react";
import JDStatusBadge from "./JDStatusBadge";
import type { JD, JDStatus } from "@/types/jd";

interface JDTableProps {
  data: JD[];
  onEdit: (jd: JD) => void;
  onStatusChange?: (id: number, status: string) => void;
  onStartMatching?: (jd: JD) => void; // D-01: trigger matching
}

export default function JDTable({ data, onEdit, onStatusChange, onStartMatching }: JDTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns = useMemo<ColumnDef<JD>[]>(
    () => [
      {
        accessorKey: "title",
        header: "职位名称",
        enableSorting: true,
      },
      {
        accessorKey: "department",
        header: "部门",
        enableSorting: true,
      },
      {
        id: "status",
        header: "状态",
        cell: ({ row }) => <JDStatusBadge status={row.original.status} />,
      },
      {
        id: "salary",
        header: "薪资范围",
        cell: ({ row }) => {
          const { salary_min, salary_max } = row.original;
          if (salary_min === 0 && salary_max === 0) return "面议";
          return `${salary_min}-${salary_max}`;
        },
      },
      {
        accessorKey: "updated_at",
        header: "更新日期",
        cell: ({ row }) => {
          const date = new Date(row.original.updated_at);
          return date.toLocaleDateString("zh-CN");
        },
      },
      {
        id: "actions",
        header: "操作",
        cell: ({ row }) => {
          const jd = row.original;
          const statusActions: Record<
            JDStatus,
            { label: string; nextStatus: string }[]
          > = {
            draft: [{ label: "发布", nextStatus: "active" }],
            active: [{ label: "关闭", nextStatus: "closed" }],
            closed: [{ label: "重新激活", nextStatus: "active" }],
          };

          return (
            <DropdownMenu>
              <DropdownMenuTrigger
                render={<Button variant="ghost" size="icon" />}
              >
                <MoreHorizontal className="h-4 w-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => onEdit(jd)}>
                  编辑
                </DropdownMenuItem>
                {onStartMatching && (
                  <DropdownMenuItem onClick={() => onStartMatching(jd)}>
                    开始匹配
                  </DropdownMenuItem>
                )}
                {statusActions[jd.status]?.map((action) => (
                  <DropdownMenuItem
                    key={action.nextStatus}
                    onClick={() => onStatusChange?.(jd.id, action.nextStatus)}
                  >
                    {action.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          );
        },
      },
    ],
    [onEdit, onStatusChange, onStartMatching]
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
              colSpan={columns.length}
              className="py-8 text-center text-muted-foreground"
            >
              暂无JD数据
            </TableCell>
          </TableRow>
        ) : (
          table.getRowModel().rows.map((row) => (
            <TableRow key={row.id}>
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
