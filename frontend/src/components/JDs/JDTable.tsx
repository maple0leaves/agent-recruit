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
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  MoreHorizontal,
  Pencil,
  PlayCircle,
  Power,
  Trash2,
} from "lucide-react";
import JDStatusBadge from "./JDStatusBadge";
import type { JD, JDStatus } from "@/types/jd";

const statusOptions: { value: JDStatus; label: string }[] = [
  { value: "draft", label: "草稿" },
  { value: "active", label: "进行中" },
  { value: "closed", label: "已关闭" },
];

interface JDTableProps {
  data: JD[];
  onEdit: (jd: JD) => void;
  onDelete: (jd: JD) => void;
  onStatusChange?: (id: number, status: string) => void;
  onStartMatching?: (jd: JD) => void;
}

export default function JDTable({
  data,
  onEdit,
  onDelete,
  onStatusChange,
  onStartMatching,
}: JDTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns = useMemo<ColumnDef<JD>[]>(
    () => [
      {
        accessorKey: "title",
        header: "职位名称",
        enableSorting: true,
        cell: ({ row }) => (
          <div className="max-w-[260px]">
            <div className="truncate font-medium">{row.original.title}</div>
            <div className="truncate text-xs text-muted-foreground">
              {row.original.skills}
            </div>
          </div>
        ),
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
          return `${salary_min.toLocaleString()}-${salary_max.toLocaleString()}`;
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

          return (
            <DropdownMenu>
              <DropdownMenuTrigger
                render={
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`打开 ${jd.title} 的操作菜单`}
                  />
                }
              >
                <MoreHorizontal className="size-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-36">
                <DropdownMenuItem onClick={() => onEdit(jd)}>
                  <Pencil className="size-4" />
                  编辑
                </DropdownMenuItem>
                {onStartMatching && (
                  <DropdownMenuItem onClick={() => onStartMatching(jd)}>
                    <PlayCircle className="size-4" />
                    开始匹配
                  </DropdownMenuItem>
                )}
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger>
                    <Power className="size-4" />
                    修改状态
                  </DropdownMenuSubTrigger>
                  <DropdownMenuSubContent className="w-32">
                    <DropdownMenuRadioGroup
                      value={jd.status}
                      onValueChange={(value) => {
                        if (!value || value === jd.status) return;
                        onStatusChange?.(jd.id, value);
                      }}
                    >
                      {statusOptions.map((option) => (
                        <DropdownMenuRadioItem
                          key={option.value}
                          value={option.value}
                        >
                          {option.label}
                        </DropdownMenuRadioItem>
                      ))}
                    </DropdownMenuRadioGroup>
                  </DropdownMenuSubContent>
                </DropdownMenuSub>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  variant="destructive"
                  onClick={() => onDelete(jd)}
                >
                  <Trash2 className="size-4" />
                  删除
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          );
        },
      },
    ],
    [onDelete, onEdit, onStatusChange, onStartMatching]
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
              暂无 JD 数据
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
