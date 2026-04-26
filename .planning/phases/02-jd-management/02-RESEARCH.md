# Phase 2: JD Management - Research

**Researched:** 2026-04-26
**Domain:** Job Description CRUD, server-side pagination/filtering, template system
**Confidence:** HIGH (all packages verified against npm registry)

## Summary

Phase 2 adds the first business feature layer on top of Phase 1's auth foundation. HR can create, manage, search, and filter job descriptions (JDs), with support for preset templates. The phase covers four requirements (JD-01 through JD-04) and introduces the JD data model, CRUD API endpoints, a list page with server-side pagination/filtering, a create/edit form, and a hardcoded template system.

**Primary recommendation:** Build backend-first: JD model + Alembic migration + CRUD API + template config, then frontend list page with shadcn Table + TanStack Query pagination, then create/edit form with shadcn Form + react-hook-form + Zod validation. Use `@tanstack/react-table` for table logic (not hand-rolled), `react-hook-form` for form state, and SQLAlchemy dynamic `.where()` chaining for server-side filtering.

**Key discovery -- TanStack Query v5 pagination API change:** In TanStack Query v5 (already installed at v5.100.5), `keepPreviousData` is no longer a boolean option. It's now imported as a function and passed to `placeholderData`: `import { keepPreviousData } from "@tanstack/react-query"` then `placeholderData: keepPreviousData`. The `isPreviousData` property is renamed to `isPlaceholderData`. This is a critical API change from v4 patterns still common in older tutorials.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** JD 核心字段：title (str), department (str, 自由文本), skills (str, 逗号分隔), experience_years (int), education (enum), salary_min (int), salary_max (int), description (str, 长文本), status (enum)
- **D-02:** education 枚举值：高中 / 大专 / 本科 / 硕士 / 博士 / 不限
- **D-03:** title 无命名规范约束，HR 自由输入
- **D-04:** created_at / updated_at 时间戳自动维护
- **D-05:** 表格布局（shadcn/ui Table），列：职位名称、部门、状态、薪资范围、更新日期
- **D-06:** 传统分页（每页 20 条），页码按钮 + 上一页/下一页
- **D-07:** 服务端搜索和筛选，API 传参过滤
- **D-08:** 筛选维度：状态筛选、关键词搜索、日期范围筛选
- **D-09:** 3-5 个预设模板，硬编码在代码/配置文件里，不需要数据库表
- **D-10:** 模板预设所有字段（skills, experience_years, education, salary_min, salary_max, description），HR 填写 title 和 department
- **D-11:** HR 不能编辑或创建模板（Phase 2 范围外）
- **D-12:** 三状态：draft（草稿）→ active（发布中）→ closed（已关闭），closed 可重新激活回 active
- **D-13:** 只关不删，不提供删除功能（软删除/硬删除都不做）
- **D-14:** 任何登录用户都可以创建/编辑任何 JD，不做创建者所有权控制

### Claude's Discretion
- 模板具体包含哪些职位（如"软件工程师"、"产品经理"等）
- skills 逗号分隔格式的具体值
- 列表页表格列的具体顺序和宽度
- 日期范围筛选的 UI 组件选择
- 新增 JD 时表单的布局和分步方式

### Deferred Ideas (OUT OF SCOPE)
- 部门预设枚举列表（department 下拉选择）— Phase 2 用自由文本
- HR 可自定义模板（创建/编辑/删除模板）— 后续阶段
- JD 所有权控制（创建者+admin 才可编辑）— 后续阶段
- JD 删除/软删除功能 — 当前只关不删
- JD 审批流程 — 当前无需审批，即时创建
- 批量导入 JD — v2 范围（RES-06 同类功能）
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| JD-01 | HR can create JD with structured fields (title, department, skills, experience, salary range) | JD model with all D-01 fields; shadcn Form + react-hook-form + Zod for validation; POST /jd endpoint for creation; template system (JD-04) pre-fills common fields |
| JD-02 | HR can edit, close existing JD | PUT /jd/{id} for editing; PATCH /jd/{id}/status for close/reactivate; same form component for create/edit; status lifecycle: draft -> active -> closed (D-12), re-activatable |
| JD-03 | HR can filter/search JD list by department, status, date | Server-side filtering via API query params; SQLAlchemy dynamic `.where()` chaining; TanStack Query v5 pagination with `placeholderData: keepPreviousData`; shadcn Table + search input + filter controls |
| JD-04 | System provides JD templates for quick creation | Hardcoded Python config with 3-5 presets (D-09); GET /jd/templates endpoint; POST /jd/from-template with pre-filled fields; HR fills title + department (D-10) |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| JD data persistence | Database / Storage | -- | SQLAlchemy async + SQLite; JD model with all D-01 fields |
| JD CRUD API | API / Backend | -- | FastAPI APIRouter + Depends(get_current_user); all business logic server-side |
| JD search/filter (query building) | API / Backend | -- | SQLAlchemy dynamic WHERE; API returns filtered + paginated results |
| Template config storage | API / Backend | -- | Hardcoded Python dict in config file (D-09), served via API |
| JD list page (table) | Browser / Client | -- | shadcn Table + TanStack Table for rendering |
| Pagination state | Browser / Client | API / Backend | URL params or React state drives API calls; server returns paginated data |
| Search/filter UI | Browser / Client | -- | Input fields, select dropdowns, date picker; sends params to API |
| JD create/edit form | Browser / Client | API / Backend | react-hook-form + Zod validation; submits to API |
| Template selection | Browser / Client | -- | UI shows template options; on select, pre-fills form fields |
| Status transitions | API / Backend | -- | Backend enforces D-12 state machine (draft->active, active->closed, closed->active) |

---

## Standard Stack

### Existing (from Phase 1 -- no changes needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.3 | API framework | Already in project; async-native; auto OpenAPI docs |
| SQLAlchemy | 2.0.49 | Async ORM | Standard Python ORM; async engine for SQLite via aiosqlite |
| Alembic | 1.18.4 | DB migrations | Standard; auto-generation from model changes |
| aiosqlite | 0.22.1 | Async SQLite driver | Required by SQLAlchemy async engine |
| React | 19.2.5 | UI framework | Latest stable; concurrent features |
| Vite | 8.0.10 | Build tool | Sub-second HMR; 42KB bundle baseline |
| TypeScript | 6.x | Type safety | Catches schema mismatches at compile time |
| Tailwind CSS | 4.2.4 | Styling | Zero runtime CSS; CSS-first config |
| TanStack Query | 5.100.5 | Server state | Auto caching, pagination, background refetch |
| axios | 1.15.2 | HTTP client | withCredentials for cookie-based auth |
| React Router | 7.14.2 | Client routing | Mature; URL-based state |
| Zustand | 5.0.12 | State management | Lightweight; used by authStore |
| Zod | 4.3.6 | Schema validation | Type-safe validation for forms + API |
| @hookform/resolvers | 5.2.2 | Zod resolver | Bridges react-hook-form + Zod |
| shadcn/ui | latest | UI components | Copy-paste components; zero runtime dep |

### New (to install for Phase 2)

**npm packages:**
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tanstack/react-table | 8.21.3 | Table logic | Headless UI for sorting, filtering, pagination state; pairs with shadcn Table markup |
| react-hook-form | 7.74.0 | Form state | Industry standard for React forms; built-in validation, error handling, field array support |
| react-day-picker | 9.14.0 | Date picker | Required by shadcn/ui Calendar component; needs v9+ for shadcn v4+ compat |
| date-fns | 4.1.0 | Date formatting | Required by react-day-picker; tree-shakeable |

**shadcn components to add:**
| Component | Command | Purpose |
|-----------|---------|---------|
| table | `npx shadcn@latest add table` | Static HTML table markup (TanStack Table provides logic) |
| form | `npx shadcn@latest add form` | Form wrapper with react-hook-form integration |
| select | `npx shadcn@latest add select` | Dropdown for status filter, education field |
| badge | `npx shadcn@latest add badge` | Status display (draft/active/closed) |
| textarea | `npx shadcn@latest add textarea` | JD description field |
| popover | `npx shadcn@latest add popover` | Date picker popover wrapper |
| calendar | `npx shadcn@latest add calendar` | Date range selection (react-day-picker) |
| dialog | `npx shadcn@latest add dialog` | Modal for create/edit form (optional, could use page) |
| command | `npx shadcn@latest add command` | Searchable command palette (for advanced filter) |
| dropdown-menu | `npx shadcn@latest add dropdown-menu` | Action menu for each row (edit/close) |

### Installation

```bash
# Frontend -- new npm packages
npm install @tanstack/react-table react-hook-form react-day-picker date-fns

# Frontend -- shadcn components
npx shadcn@latest add table form select badge textarea popover calendar dialog command dropdown-menu
```

### Backend Packages

No new Python packages needed -- SQLAlchemy, Alembic, aiosqlite are already installed from Phase 1.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| @tanstack/react-table | Hand-rolled table state | TanStack handles column sorting, pagination math, selection, keyboard nav. Hand-rolling is error-prone for anything beyond static display |
| react-hook-form + shadcn Form | Plain form state (useState) | shadcn Form provides validation UX, error messages, accessibility. Plain state requires manual error handling |
| react-day-picker | Native `<input type="date">` | Native date input has inconsistent styling across browsers; react-day-picker integrates with shadcn Calendar popover |
| Hardcoded template dict (Python) | Database template table | D-09 explicitly rejects DB-based templates; hardcoded is simpler and matches user preference |

---

## Architecture Patterns

### System Architecture Diagram

```
[Browser: React SPA]
     |
     | axios withCredentials (cookies auto-sent)
     | GET/POST/PUT/PATCH /jd/*
     v
[FastAPI: JD CRUD Endpoints]
     |
     |-- Depends(get_current_user) -- all endpoints require auth
     |-- D-14: any role can create/edit (no ownership check)
     |
     v
[FastAPI: Filter/Search Logic]
     |
     |-- Query params: page, page_size, status, keyword, date_from, date_to
     |-- SQLAlchemy: dynamic .where() chaining based on params
     |-- COUNT + SELECT pattern for pagination
     |
     v
[SQLAlchemy: JD Model]
     |
     |-- Backend creates SELECT + COUNT queries
     |-- Returns { items: [...], total: N, page: P, page_size: S }
     |
     v
[SQLite (data/dev.db)]
     |-- jds table (NEW: Alembic migration version 002)
     |-- users table (existing)
     |-- LangGraph checkpoint tables (existing)

[JD Templates (hardcoded)]
     |
     |-- GET /jd/templates returns list of preset templates
     |-- POST /jd/from-template creates JD from template + title + department
     |-- Config file: backend/config/templates.py (Python dict)
```

### Data Flow: Create JD from Template

```
1. HR clicks "新建 JD" → sees template selection cards
2. HR selects template (e.g., "软件工程师") → form pre-fills with template field values
3. HR fills title + department (required), adjusts any field
4. HR submits form → POST /jd { title, department, skills, experience_years, ... }
5. Backend validates with Pydantic → inserts into SQLite → returns created JD
6. TanStack Query invalidates list cache → table refreshes
```

### Data Flow: List with Pagination + Filtering

```
1. Page loads: GET /jd?page=1&page_size=20
2. HR types keyword in search box: debounce 300ms → GET /jd?page=1&keyword=前端
3. HR selects status filter: GET /jd?page=1&status=active&keyword=前端
4. HR selects date range: GET /jd?page=1&status=active&date_from=2026-01-01&date_to=2026-04-26
5. HR clicks page 3: GET /jd?page=3&page_size=20&status=active
```

### Recommended Project Structure

```
hellojobs/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                    # EXISTING
│   │   │   └── jd.py                      # NEW: JD CRUD endpoints
│   │   └── deps.py                        # EXISTING (reuse get_current_user)
│   ├── db/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                    # EXISTING
│   │   │   └── jd.py                      # NEW: JD model
│   │   ├── migrations/
│   │   │   ├── versions/
│   │   │   │   ├── 4fce5ea929cc_create_users_table.py  # EXISTING
│   │   │   │   └── 002_create_jds_table.py             # NEW: migration
│   │   │   ├── env.py                     # MODIFIED: import JD model
│   │   │   └── ...
│   │   └── ...
│   ├── config/
│   │   └── templates.py                   # NEW: hardcoded JD templates
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts                  # EXISTING
│   │   │   └── jd.ts                      # NEW: JD API functions
│   │   ├── hooks/
│   │   │   ├── useAuth.ts                 # EXISTING
│   │   │   └── useJDs.ts                  # NEW: TanStack Query hooks for JD
│   │   ├── pages/
│   │   │   ├── Login.tsx                  # EXISTING
│   │   │   ├── JDManagement.tsx           # REPLACE: full JD list page
│   │   │   ├── JDCreate.tsx               # NEW: JD create form (or inline in modal)
│   │   │   ├── JDEdit.tsx                 # NEW: JD edit form (or inline in modal)
│   │   ├── components/
│   │   │   ├── Layout.tsx                 # EXISTING
│   │   │   ├── ProtectedRoute.tsx         # EXISTING
│   │   │   ├── JDs/
│   │   │   │   ├── JDTable.tsx            # NEW: TanStack Table wrapper
│   │   │   │   ├── JDFilterBar.tsx        # NEW: search + filter controls
│   │   │   │   ├── JDForm.tsx             # NEW: reusable create/edit form
│   │   │   │   ├── JDPagination.tsx       # NEW: page number buttons
│   │   │   │   ├── JDStatusBadge.tsx      # NEW: status badge component
│   │   │   │   └── TemplateSelector.tsx   # NEW: template selection UI
│   │   ├── stores/
│   │   │   └── authStore.ts               # EXISTING
│   │   └── types/
│   │       └── jd.ts                      # NEW: TypeScript types for JD
```

### Pattern 1: JD Model with Enum Fields

**What:** SQLAlchemy model for JD with enum-based status and education fields. Follows the same pattern as the User model from Phase 1.

**When to use:** All new business entities in this project.

**Example:**

```python
# backend/db/models/jd.py [VERIFIED: SQLAlchemy 2.0 docs, User model pattern]
import enum
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, func
from backend.db.engine import Base


class EducationLevel(str, enum.Enum):
    HIGH_SCHOOL = "高中"
    ASSOCIATE = "大专"
    BACHELOR = "本科"
    MASTER = "硕士"
    PHD = "博士"
    ANY = "不限"


class JDStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class JD(Base):
    __tablename__ = "jds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    department = Column(String(100), nullable=False)
    skills = Column(String(1000), nullable=False)  # comma-separated
    experience_years = Column(Integer, nullable=False, default=0)
    education = Column(Enum(EducationLevel), nullable=False, default=EducationLevel.ANY)
    salary_min = Column(Integer, nullable=False)
    salary_max = Column(Integer, nullable=False)
    description = Column(Text, nullable=False, default="")
    status = Column(Enum(JDStatus), nullable=False, default=JDStatus.DRAFT, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

### Pattern 2: SQLAlchemy Dynamic Query Building for Server-Side Filtering

**What:** Chain `.where()` clauses conditionally based on request query parameters. Wrapped in a reusable function for both the data query and the count query.

**When to use:** All GET /jd endpoint with query params for filtering and pagination.

**Example:**

```python
# backend/api/routes/jd.py -- dynamic query pattern [VERIFIED: SQLAlchemy 2.0 docs]
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession


async def list_jds(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    keyword: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    # Base query
    base_query = select(JD)

    # Dynamic filters
    if status:
        base_query = base_query.where(JD.status == status)

    if keyword:
        keyword_filter = f"%{keyword}%"
        base_query = base_query.where(
            or_(
                JD.title.ilike(keyword_filter),
                JD.department.ilike(keyword_filter),
                JD.skills.ilike(keyword_filter),
            )
        )

    if date_from:
        base_query = base_query.where(JD.updated_at >= date_from)

    if date_to:
        base_query = base_query.where(JD.updated_at <= date_to)  # + " 23:59:59" if needed

    # Count total (same filters)
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginated select
    query = base_query.order_by(JD.updated_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": [jd_to_dict(jd) for jd in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
```

### Pattern 3: TanStack Query v5 Pagination with `placeholderData: keepPreviousData`

**What:** Standard pattern for page-number pagination in TanStack Query v5. The query key includes the page number and filter parameters. `placeholderData: keepPreviousData` maintains the previous page's data while fetching the new page (no loading flash).

**When to use:** All paginated lists in this project -- JD list is the first, candidate list (Phase 3) and matching results will follow the same pattern.

**Example:**

```typescript
// frontend/src/hooks/useJDs.ts [VERIFIED: TanStack Query v5 docs]
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";
import type { JD, JDListResponse } from "../types/jd";

interface JDFilters {
  page: number;
  pageSize: number;
  status?: string;
  keyword?: string;
  dateFrom?: string;
  dateTo?: string;
}

export function useJDs(filters: JDFilters) {
  return useQuery<JDListResponse>({
    queryKey: ["jd", "list", filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("page", String(filters.page));
      params.set("page_size", String(filters.pageSize));
      if (filters.status) params.set("status", filters.status);
      if (filters.keyword) params.set("keyword", filters.keyword);
      if (filters.dateFrom) params.set("date_from", filters.dateFrom);
      if (filters.dateTo) params.set("date_to", filters.dateTo);

      const res = await apiClient.get<JDListResponse>(`/jd?${params.toString()}`);
      return res.data;
    },
    placeholderData: keepPreviousData,  // v5 API: function, not boolean!
    staleTime: 30_000,  // 30s before refetch
  });
}
```

**Key differences from TanStack Query v4:**
| v4 | v5 |
|----|----|
| `keepPreviousData: true` (boolean option) | `placeholderData: keepPreviousData` (imported function) |
| `isPreviousData` (boolean) | `isPlaceholderData` (boolean) |
| Auto-import from `@tanstack/react-query` | Must import `{ keepPreviousData }` explicitly |

### Pattern 4: shadcn Form + react-hook-form + Zod

**What:** Standard form pattern using shadcn/ui Form wrapper with react-hook-form for state management and Zod for schema validation.

**When to use:** All data-entry forms in this project -- JD create/edit is the first.

**Example:**

```typescript
// frontend/src/components/JDs/JDForm.tsx [VERIFIED: shadcn/ui docs]
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Form, FormField, FormItem, FormLabel, FormControl, FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

const jdFormSchema = z.object({
  title: z.string().min(1, "职位名称不能为空").max(200),
  department: z.string().min(1, "部门不能为空").max(100),
  skills: z.string().min(1, "技能要求不能为空"),
  experience_years: z.coerce.number().int().min(0),
  education: z.string().min(1),
  salary_min: z.coerce.number().int().min(0),
  salary_max: z.coerce.number().int().min(0),
  description: z.string().optional().default(""),
}).refine((data) => data.salary_max >= data.salary_min, {
  message: "最高薪资不能低于最低薪资",
  path: ["salary_max"],
});

type JDFormValues = z.infer<typeof jdFormSchema>;

interface JDFormProps {
  defaultValues?: Partial<JDFormValues>;
  onSubmit: (values: JDFormValues) => Promise<void>;
}

export function JDForm({ defaultValues, onSubmit }: JDFormProps) {
  const form = useForm<JDFormValues>({
    resolver: zodResolver(jdFormSchema),
    defaultValues: {
      title: "",
      department: "",
      skills: "",
      experience_years: 0,
      education: "本科",
      salary_min: 0,
      salary_max: 0,
      description: "",
      ...defaultValues,
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <FormField control={form.control} name="title"
            render={({ field }) => (
              <FormItem>
                <FormLabel>职位名称</FormLabel>
                <FormControl><Input {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField control={form.control} name="department"
            render={({ field }) => (
              <FormItem>
                <FormLabel>部门</FormLabel>
                <FormControl><Input {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
        {/* ... more fields ... */}
        <Button type="submit">保存</Button>
      </form>
    </Form>
  );
}
```

### Pattern 5: shadcn Table + TanStack Table

**What:** shadcn/ui provides styled Table markup (Table, TableHead, TableBody). TanStack Table provides headless logic (sorting, column visibility). For Phase 2, sorting is client-side (small dataset per page, 20 items). Pagination, filtering, and search are server-side.

**When to use:** All data-display tables in this project.

**Example:**

```typescript
// frontend/src/components/JDs/JDTable.tsx [VERIFIED: TanStack Table 8 docs]
import {
  useReactTable, getCoreRowModel, getSortedRowModel, flexRender,
  type ColumnDef, type SortingState,
} from "@tanstack/react-table";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { JDStatusBadge } from "./JDStatusBadge";
import type { JD } from "@/types/jd";
import { useState } from "react";

interface JDTableProps {
  data: JD[];
}

const columns: ColumnDef<JD>[] = [
  { accessorKey: "title", header: "职位名称", enableSorting: true },
  { accessorKey: "department", header: "部门", enableSorting: true },
  {
    accessorKey: "status",
    header: "状态",
    cell: ({ row }) => <JDStatusBadge status={row.original.status} />,
  },
  {
    header: "薪资范围",
    cell: ({ row }) => `${row.original.salary_min}-${row.original.salary_max}`,
  },
  {
    accessorKey: "updated_at",
    header: "更新日期",
    cell: ({ row }) => new Date(row.original.updated_at).toLocaleDateString("zh-CN"),
  },
  // Action column with dropdown menu for edit/close
];

export function JDTable({ data }: JDTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

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
        {table.getHeaderGroups().map((group) => (
          <TableRow key={group.id}>
            {group.headers.map((header) => (
              <TableHead key={header.id} onClick={header.column.getToggleSortingHandler()}>
                {flexRender(header.column.columnDef.header, header.getContext())}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.map((row) => (
          <TableRow key={row.id}>
            {row.getVisibleCells().map((cell) => (
              <TableCell key={cell.id}>
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### Pattern 6: Hardcoded Template Config

**What:** Simple Python file with a list of template dicts. Each template pre-fills all JD fields except title and department.

**When to use:** D-09 explicitly requires hardcoded templates (no database table). This pattern keeps it simple.

**Example:**

```python
# backend/config/templates.py
from typing import TypedDict


class JDTemplate(TypedDict):
    name: str
    description: str
    skills: str
    experience_years: int
    education: str
    salary_min: int
    salary_max: int
    description: str


TEMPLATES: list[JDTemplate] = [
    {
        "name": "软件工程师",
        "description": "前后端全栈开发工程师",
        "skills": "Java, Python, SQL, React, Docker, Git",
        "experience_years": 3,
        "education": "本科",
        "salary_min": 15000,
        "salary_max": 30000,
        "description": "负责公司核心产品的功能开发与维护...",
    },
    {
        "name": "产品经理",
        "description": "B端产品规划与设计",
        "skills": "Axure, Figma, SQL, 用户调研, 数据分析",
        "experience_years": 2,
        "education": "本科",
        "salary_min": 12000,
        "salary_max": 25000,
        "description": "负责产品需求分析、原型设计、项目跟进...",
    },
    {
        "name": "销售经理",
        "description": "企业客户销售与关系维护",
        "skills": "商务谈判, CRM, 方案制作, 客户管理",
        "experience_years": 3,
        "education": "大专",
        "salary_min": 10000,
        "salary_max": 20000,
        "description": "负责开拓和维护企业客户...",
    },
]
```

### Pattern 7: JD CRUD API Endpoints

**What:** FastAPI APIRouter with CRUD endpoints following the same pattern as auth.py. All endpoints require `get_current_user`.

**When to use:** Standard API route structure for all business entities.

**Example:**

```python
# backend/api/routes/jd.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_current_user, get_db
from backend.db.models.jd import JD, JDStatus, EducationLevel
from backend.config.templates import TEMPLATES

router = APIRouter(prefix="/jd", tags=["jd"])

class JDSchema(BaseModel):
    title: str
    department: str
    skills: str
    experience_years: int
    education: str
    salary_min: int
    salary_max: int
    description: str

@router.get("")
async def list_jds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    keyword: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    # ... see Pattern 2 for implementation ...

@router.get("/templates")
async def list_templates(_user: dict = Depends(get_current_user)):
    return TEMPLATES

@router.post("")
async def create_jd(
    data: JDSchema,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    jd = JD(**data.model_dump())
    db.add(jd)
    await db.commit()
    await db.refresh(jd)
    return jd

@router.get("/{jd_id}")
async def get_jd(
    jd_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(select(JD).where(JD.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="JD 不存在")
    return jd

@router.put("/{jd_id}")
async def update_jd(jd_id: int, data: JDSchema, ...):
    # ... standard update pattern ...

@router.patch("/{jd_id}/status")
async def update_jd_status(
    jd_id: int,
    status: JDStatus,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(select(JD).where(JD.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="JD 不存在")
    # D-12 state machine: draft->active, active->closed, closed->active
    valid_transitions = {
        JDStatus.DRAFT: [JDStatus.ACTIVE],
        JDStatus.ACTIVE: [JDStatus.CLOSED],
        JDStatus.CLOSED: [JDStatus.ACTIVE],
    }
    if status not in valid_transitions.get(jd.status, []):
        raise HTTPException(status_code=400, detail="无效的状态转换")
    jd.status = status
    await db.commit()
    return jd
```

### Anti-Patterns to Avoid

- **Over-fetching data:** Don't load all JDs and filter client-side. Always filter server-side (D-07: "API 传参过滤").
- **Per-page total count query without caching:** COUNT queries on every request are fine for <100K rows in SQLite. If performance becomes an issue, add a redis counter cache in a later phase.
- **Re-creating the form for create vs edit:** Use a single `<JDForm>` component that accepts optional `defaultValues`. The edit page passes the existing JD data as defaults.
- **Using `keepPreviousData: true` as boolean:** TanStack Query v5 (already installed) changed this API. Must use `placeholderData: keepPreviousData` with the imported function.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table sorting/pagination logic | Manual state management | `@tanstack/react-table` | Handles column sorting, selection, pagination math, keyboard nav. Headless -- pairs with shadcn Table markup |
| Form state + validation | Manual `useState` + validation | `react-hook-form` + `zod` | Handles dirty states, error messages, field arrays, cross-field validation. shadcn Form provides accessible UI |
| Date picker | Native `<input type="date">` | `react-day-picker` + shadcn Calendar | Inconsistent browser styling; shadcn Calendar integrates with Popover for good UX |
| Server-side filtering | Client-side filter after all data loaded | SQLAlchemy dynamic `.where()` | D-07 requires server-side filtering. Client-side filtering only works with full dataset loaded (impractical) |

**Key insight:** The Don't-Hand-Roll pattern from Phase 1 extends naturally into Phase 2. Every item represents a domain where edge cases and UX matter more than the surface-level simplicity suggests. TanStack Table's pagination math alone (handling edge pages, page count, overflow) justifies the dependency.

---

## Common Pitfalls

### Pitfall 1: TanStack Query v5 `keepPreviousData` API Breakage

**What goes wrong:** Following old tutorials (v4 era), you write `keepPreviousData: true` in the query options. This does nothing in v5 -- the option is silently ignored, and the page transition shows a loading spinner.

**Why it happens:** TanStack Query v5 (5.100.5 is installed) changed `keepPreviousData` from a boolean option to a function passed to `placeholderData`. The old `isPreviousData` renamed to `isPlaceholderData`.

**How to avoid:** Always import `keepPreviousData` from `@tanstack/react-query` and pass it as `placeholderData: keepPreviousData`.

**How to detect:** Search for `keepPreviousData: true` in useQuery options. Should be `placeholderData: keepPreviousData`.

### Pitfall 2: zod v4 API Changes

**What goes wrong:** zod v4.3.6 (installed) has API differences from zod v3. The `z.infer<>` pattern still works, but some v3 utilities may be deprecated.

**Why it happens:** zod v4 is relatively new (late 2025). Tutorials still reference v3 patterns.

**How to avoid:** Verify any zod utility function against the installed v4 docs. The basic schema definition + infer + refine pattern used in this phase is stable.

### Pitfall 3: Date Range Filter with SQLite Date Strings

**What goes wrong:** SQLite stores DateTime as ISO strings. Comparing with `>=` and `<=` on string representation may produce incorrect results if timezone-aware timestamps are compared with date-only strings.

**Why it happens:** SQLite has no native DATE type. String comparison of `"2026-01-01"` with `"2026-01-01T12:00:00"` will exclude rows on the same day if the date_to is exclusive.

**How to avoid:** Either (a) append ` 23:59:59` to date_to before querying, or (b) use SQLAlchemy's `cast()` to compare as dates:
```python
from sqlalchemy import cast, Date
base_query = base_query.where(cast(JD.updated_at, Date) >= date_from)
base_query = base_query.where(cast(JD.updated_at, Date) <= date_to)
```
Option (a) is simpler and sufficient for this phase.

### Pitfall 4: Status Transition Validation

**What goes wrong:** The frontend form allows any status selection, but the backend validates transitions. If the backend error response is not properly handled, the user sees a confusing generic error.

**Why it happens:** D-12 defines a specific state machine (draft -> active -> closed -> active). Not all transitions are valid (e.g., closed -> draft is not allowed).

**How to avoid:** Define the transition map clearly in the backend and return a descriptive Chinese error message:
```python
raise HTTPException(status_code=400, detail="不能从「已关闭」回到「草稿」状态")
```

### Pitfall 5: Alembic Autogeneration with Async Engine

**What goes wrong:** The Alembic `env.py` currently uses a sync engine (correct for Alembic, which uses synchronous SQLAlchemy). The existing migration (`4fce5ea929cc_create_users_table.py`) works with the sync URL. The new JD model must be imported in `env.py` for autogeneration to detect it.

**How to avoid:** Follow the established pattern: add `from backend.db.models.jd import JD` to `env.py` alongside the existing `User` import. Run `cd backend && alembic revision --autogenerate -m "create_jds_table"` to generate the migration.

### Pitfall 6: React-hook-form `onSubmit` Type with Async

**What goes wrong:** The `handleSubmit` callback expects a `Promise<void>` return. If the async function throws an error without catching, the form shows no feedback but the error is silently swallowed.

**How to avoid:** Always wrap the submission logic in try/catch inside the handler. Use the form's `setError` for field-level errors:
```typescript
const onSubmit = async (values: JDFormValues) => {
  try {
    await createJDMutation.mutateAsync(values);
    // navigate or show success
  } catch (err) {
    // `setError("root", ...)` for form-level error
  }
};
```

### Warning Signs Checklist

- [ ] `keepPreviousData: true` in useQuery options (should be `placeholderData: keepPreviousData`)
- [ ] No `date_to` boundary handling in SQLAlchemy query (should handle end-of-day)
- [ ] Status transition without validation in backend (must enforce D-12 state machine)
- [ ] JD model not imported in `env.py` (Alembic won't auto-detect new table)
- [ ] Client-side filtering of full JD list (must be server-side)
- [ ] `tailwind.config.js` modifications (Tailwind v4 uses CSS config)
- [ ] Using `passlib` (Phase 1 confirmed this is replaced with direct bcrypt)
- [ ] Form submission without try/catch (silent error swallowing)

---

## Code Examples

### Backend: JD Route Registration

```python
# api/server.py -- add JD router
from backend.api.routes.jd import router as jd_router

app.include_router(jd_router)
```

### Backend: Alembic env.py Update

```python
# backend/db/migrations/env.py -- add JD model import
from backend.db.models.user import User  # noqa: F401
from backend.db.models.jd import JD  # noqa: F401 -- ADD THIS LINE
```

### Backend: Pydantic Response Schema with Omit

```python
# backend/api/routes/jd.py -- response schema for paginated list
from pydantic import BaseModel
from datetime import datetime

class JDResponse(BaseModel):
    id: int
    title: str
    department: str
    skills: str
    experience_years: int
    education: str
    salary_min: int
    salary_max: int
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

class JDListResponse(BaseModel):
    items: list[JDResponse]
    total: int
    page: int
    page_size: int
```

### Frontend: JD API Functions

```typescript
// frontend/src/api/jd.ts [PATTERN: axios + TanStack Query]
import apiClient from "./client";
import type { JD, JDListResponse, JDFormValues, JDTemplate } from "../types/jd";

export async function fetchJDs(params: Record<string, string | number>): Promise<JDListResponse> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") searchParams.set(key, String(value));
  });
  const res = await apiClient.get<JDListResponse>(`/jd?${searchParams.toString()}`);
  return res.data;
}

export async function fetchJDTemplates(): Promise<JDTemplate[]> {
  const res = await apiClient.get<JDTemplate[]>("/jd/templates");
  return res.data;
}

export async function createJD(data: JDFormValues): Promise<JD> {
  const res = await apiClient.post<JD>("/jd", data);
  return res.data;
}

export async function updateJD(id: number, data: JDFormValues): Promise<JD> {
  const res = await apiClient.put<JD>(`/jd/${id}`, data);
  return res.data;
}

export async function updateJDStatus(id: number, status: string): Promise<JD> {
  const res = await apiClient.patch<JD>(`/jd/${id}/status`, { status });
  return res.data;
}
```

### Frontend: TypeScript Type Definitions

```typescript
// frontend/src/types/jd.ts
export type JDStatus = "draft" | "active" | "closed";
export type EducationLevel = "高中" | "大专" | "本科" | "硕士" | "博士" | "不限";

export interface JD {
  id: number;
  title: string;
  department: string;
  skills: string;
  experience_years: number;
  education: EducationLevel;
  salary_min: number;
  salary_max: number;
  description: string;
  status: JDStatus;
  created_at: string;
  updated_at: string;
}

export interface JDListResponse {
  items: JD[];
  total: number;
  page: number;
  page_size: number;
}

export interface JDFormValues {
  title: string;
  department: string;
  skills: string;
  experience_years: number;
  education: EducationLevel;
  salary_min: number;
  salary_max: number;
  description: string;
}

export interface JDTemplate {
  name: string;
  description: string;
  skills: string;
  experience_years: number;
  education: EducationLevel;
  salary_min: number;
  salary_max: number;
  description: string;
}
```

### Frontend: Pagination Component

```typescript
// frontend/src/components/JDs/JDPagination.tsx
interface JDPaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function JDPagination({ page, pageSize, total, onPageChange }: JDPaginationProps) {
  const totalPages = Math.ceil(total / pageSize);

  // Generate page numbers: [1, ..., current-1, current, current+1, ..., last]
  const getPageNumbers = () => {
    const pages: (number | "...")[] = [];
    // Simplified logic: show first, last, and 5 pages around current
    // ... (implementation depends on desired UX)
    return pages;
  };

  return (
    <div className="flex items-center justify-between px-2 py-4">
      <div className="text-sm text-muted-foreground">
        共 {total} 条，第 {page}/{totalPages} 页
      </div>
      <div className="flex items-center gap-1">
        <Button variant="outline" size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}>
          上一页
        </Button>
        {/* Page number buttons */}
        {getPageNumbers().map((p, i) =>
          p === "..." ? (
            <span key={`ellipsis-${i}`} className="px-2">...</span>
          ) : (
            <Button key={p} variant={p === page ? "default" : "outline"} size="sm"
              onClick={() => onPageChange(p as number)}>
              {p}
            </Button>
          )
        )}
        <Button variant="outline" size="sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}>
          下一页
        </Button>
      </div>
    </div>
  );
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TanStack Query v4 `keepPreviousData: true` | v5 `placeholderData: keepPreviousData` (function) | Q1 2024 (v5 GA) | Code following v4 tutorials will silently lose the keep-previous-data behavior |
| Zod v3 | Zod v4.3 | Late 2025 | API is largely compatible but `z.infer<>`, `z.object()`, `.refine()` remain stable. Some deprecated utilities removed |
| react-day-picker v8 | react-day-picker v9 | 2024-2025 | v9 changed API; shadcn Calendar component requires v9 |
| shadcn/ui classic presets | shadcn/ui v4 (base-nova) | 2025 | Already used by Phase 1; no migration needed. Components install with slightly different markup (data-slot attributes) |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | TanStack Query v5 `placeholderData: keepPreviousData` works with the project's existing @tanstack/react-query 5.100.5 | Architecture Patterns | LOW: v5.100.5 is a recent v5 release; the `keepPreviousData` function has been stable since v5.0 |
| A2 | shadcn `npx shadcn@latest add table/form/select/badge/textarea/popover/calendar/dialog` installs correctly with the existing components | Standard Stack | LOW: The existing shadcn components (button, card, input, label) were installed with the same `npx shadcn@latest` command in Phase 1. New components should install identically |
| A3 | react-day-picker v9 is compatible with the installed shadcn Calendar component | Standard Stack | MEDIUM: If the shadcn Calendar generates a v8-based import, we may need to pin react-day-picker @8 or update the Calendar component. Verify after installation |
| A4 | Alembic autogeneration with --autogenerate works with the existing sync URL setup | Architecture Patterns | LOW: The existing env.py + alembic.ini followed the standard pattern in Phase 1. Adding the JD model import should work |
| A5 | The status transition validation (closed -> active allowed, closed -> draft blocked) matches D-12 intent | Architecture Patterns | LOW: D-12 says "closed 可重新激活回 active" which implies closed-only transitions are active<->closed and draft->active. If user expects closed->draft, update the validation map |
| A6 | SQLite date string comparison with appended " 23:59:59" handles timezone correctly | Common Pitfalls | LOW: SQLite stores DateTime as UTC ISO strings. If frontend sends local date strings, the comparison may be off by timezone offset. The current design uses UTC throughout (Phase 1 convention) |

---

## Open Questions (RESOLVED)

1. **Date range filter: date_from/date_to format**
   - What we know: D-08 requires date range filtering. shadcn Calendar returns Date objects.
   - What's unclear: Whether the frontend should send local date strings or UTC date strings. React-day-picker returns local dates.
   - Recommendation: Send ISO date strings (`YYYY-MM-DD`) from the frontend. Backend treats them as UTC. Append `T23:59:59Z` to date_to for inclusive end-of-day comparison.

2. **JD form placement: modal dialog vs. dedicated page**
   - What we know: The JD management page is a placeholder to be replaced.
   - What's unclear: Whether create/edit should be a modal (staying on list page) or a dedicated route (e.g., `/jd/new`, `/jd/123/edit`).
   - Recommendation: Use a dialog/modal for quick create/edit (shadcn Dialog). If the form grows complex in later phases, switch to dedicated pages. Modal keeps the list visible context.

3. **JD detail view**
   - What we know: JD-01/JD-02 require create and edit. No explicit requirement for a read-only detail view.
   - What's unclear: Whether clicking a row in the table should open detail view or directly go to edit mode.
   - Recommendation: Click row -> open edit dialog (same form, populated with data). No separate detail view needed for Phase 2.

4. **Template names (Claude's discretion)**
   - What we know: D-09 says 3-5 presets. D-10 says pre-fill all fields except title and department.
   - What's unclear: Which specific job titles/roles to include as presets.
   - Recommendation: Start with 3: "软件工程师", "产品经理", "销售经理". These cover the most common roles and demonstrate the template feature clearly. Add more if needed.

---

## Validation Architecture

> `workflow.nyquist_validation` is enabled (`true` in `.planning/config.json`).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| Config file | `pytest.ini` (from Phase 1) |
| Quick run command | `python -m pytest tests/ -x -q -k "jd"` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| JD-01 | Create JD with valid fields returns 200 + JD object | integration | `pytest tests/test_jd.py::test_create_jd_success -x` | Needs Wave 0 |
| JD-01 | Create JD with missing required fields returns 422 | integration | `pytest tests/test_jd.py::test_create_jd_validation -x` | Needs Wave 0 |
| JD-01 | Create JD without auth returns 401 | integration | `pytest tests/test_jd.py::test_create_jd_unauthorized -x` | Needs Wave 0 |
| JD-02 | Edit JD updates fields correctly | integration | `pytest tests/test_jd.py::test_update_jd -x` | Needs Wave 0 |
| JD-02 | Close JD changes status to closed | integration | `pytest tests/test_jd.py::test_close_jd -x` | Needs Wave 0 |
| JD-02 | Reactivate closed JD changes status back to active | integration | `pytest tests/test_jd.py::test_reactivate_jd -x` | Needs Wave 0 |
| JD-02 | Invalid status transition returns 400 | integration | `pytest tests/test_jd.py::test_invalid_status_transition -x` | Needs Wave 0 |
| JD-03 | List JDs returns paginated results | integration | `pytest tests/test_jd.py::test_list_jds_pagination -x` | Needs Wave 0 |
| JD-03 | Filter JDs by status returns filtered results | integration | `pytest tests/test_jd.py::test_list_jds_filter_status -x` | Needs Wave 0 |
| JD-03 | Search JDs by keyword returns matching results | integration | `pytest tests/test_jd.py::test_list_jds_search_keyword -x` | Needs Wave 0 |
| JD-03 | Empty filter returns all JDs paginated | integration | `pytest tests/test_jd.py::test_list_jds_no_filters -x` | Needs Wave 0 |
| JD-04 | GET /jd/templates returns list of presets | integration | `pytest tests/test_jd.py::test_list_templates -x` | Needs Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q -k "jd"`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_jd.py` -- JD CRUD + filter + template tests (use existing conftest.py from Phase 1)
- [ ] No new conftest needed -- Phase 1 already provides `test_client`, `test_session`, `db_path` fixtures

---

## Security Domain

> `security_enforcement` is enabled by default (absent from config.json, set to `true`).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (inherited) | Phase 1's JWT + bcrypt. All JD endpoints use `Depends(get_current_user)` |
| V4 Access Control | partial | D-14: any logged-in user can create/edit any JD. No ownership or role-based restrictions on JD endpoints |
| V5 Input Validation | yes | Zod schema (frontend) + Pydantic models (backend) validate all JD fields. Length limits, type checks |
| V6 Cryptography | no | JD data is not encrypted at rest. SQLite file is on server filesystem (Phase 1 scoped this out) |

### Known Threat Patterns for FastAPI + SQLAlchemy

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SQL injection via keyword search | Tampering | SQLAlchemy ORM's `ilike()` uses parameterized queries; not vulnerable |
| Mass assignment via PUT/POST | Elevation of Privilege | Pydantic schema defines exact allowed fields; status changes via dedicated PATCH endpoint only |
| XSS via JD description field | Information Disclosure | React auto-escapes HTML in JSX. Description field renders as text, not HTML |
| CSRF on mutation endpoints | Tampering | Cookies are SameSite=Lax (Phase 1). All mutations require JWT in Authorization header |

---

## Sources

### Primary (HIGH confidence)

| Source | What Was Verified |
|--------|-------------------|
| [VERIFIED: npm registry] | @tanstack/react-table@8.21.3, react-hook-form@7.74.0, react-day-picker@9.14.0, date-fns@4.1.0 |
| [VERIFIED: npm registry] | @tanstack/react-query@5.100.5 (already installed, confirms v5 API) |
| [VERIFIED: existing codebase] | User model pattern, auth route pattern, deps.py, App.tsx route setup, Layout.tsx nav structure, JDManagement.tsx placeholder |
| [VERIFIED: existing codebase] | Alembic env.py (imports User model), config.py (CORS, JWT, DB settings), api/server.py (includes auth_router) |
| [VERIFIED: existing codebase] | Frontend package.json confirms: @hookform/resolvers@5.2.2, zod@4.3.6, @tanstack/react-query@5.100.5, tailwindcss@4.2.4 |
| [VERIFIED: pip index] | SQLAlchemy 2.0.49, aiosqlite 0.22.1, Alembic 1.18.4 (already installed) |

### Secondary (MEDIUM confidence)

| Source | What Was Verified |
|--------|-------------------|
| [CITED: TanStack Query v5 docs] | `placeholderData: keepPreviousData` pagination pattern; `isPlaceholderData` flag |
| [CITED: shadcn/ui docs] | Table component installation via `npx shadcn@latest add table`; Form + react-hook-form integration |
| [CITED: SQLAlchemy 2.0 docs] | `select()`, `.where()`, `.ilike()`, `.order_by()`, `.offset()`.`.limit()`, `func.count()` -- all verified for async usage |
| [CITED: TanStack Table 8 docs] | `useReactTable()`, `getCoreRowModel()`, `getSortedRowModel()`, `flexRender()` |
| [CITED: Phase 1 RESEARCH.md] | All stack versions verified; patterns (JWT auth, dependency injection, file structure) are inherited directly |

### Tertiary (LOW confidence)

None -- all findings are based on verified registry lookups, existing codebase audit, or official documentation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all npm packages verified via registry. Backend dependencies confirmed installed. shadcn component installation follows Phase 1 pattern.
- Architecture: HIGH -- SQLAlchemy dynamic filtering, TanStack Query pagination, and shadcn Form patterns are well-documented and match established project conventions.
- Pitfalls: MEDIUM -- TanStack Query v5 API change is confirmed. Date filtering edge case with SQLite is documentable but not runtime-verified. Zod v4 API differences from v3 are based on registry version only.

**Research date:** 2026-04-26
**Valid until:** 2026-05-26 (30 days for stable packages; 7 days for shadcn/ui and fast-moving frontend tools)
