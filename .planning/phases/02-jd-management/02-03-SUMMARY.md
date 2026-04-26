---
phase: 02-jd-management
plan: 03
type: execute
subsystem: frontend
tags: [table, filter, pagination, jd-list, shadcn, tanstack-table]
requires:
  - 02-01: JD API backend endpoints
  - 02-02: Frontend infra (npm packages, shadcn components, TS types, API helpers, Query hooks)
provides:
  - JD list page with table, filter, pagination
affects: []
tech-stack:
  added: ["@tanstack/react-table sorting", "react-day-picker date range", "date-fns formatting"]
  patterns: ["Debounced search with useRef", "Shadcn v4 base-ui pattern (render prop)", "TanStack Table with client-side sorting"]
key-files:
  created:
    - frontend/src/components/JDs/JDStatusBadge.tsx
    - frontend/src/components/JDs/JDTable.tsx
    - frontend/src/components/JDs/JDFilterBar.tsx
    - frontend/src/components/JDs/JDPagination.tsx
  modified:
    - frontend/src/pages/JDManagement.tsx
decisions:
  - "Added onStatusChange prop to JDTable (not in plan spec but required for status action dropdowns to function)"
  - "JDFilterBar uses local state for searchInput with useRef debounce (300ms); no bidirectional sync from parent filters"
  - "Calendar date range filter only triggers onFilterChange when both from and to dates are selected"
  - "Pagination returns null when totalPages <= 1 (handles empty and single-page cases)"
metrics:
  duration: "12 min"
  completed: "2026-04-26"
---

# Phase 02 Plan 03: JD List Page with Table, Filter, Pagination

**One-liner:** Built JD list page with TanStack Table (6 columns, client-side sorting), debounced keyword search, status dropdown filter, Calendar date range picker, numbered pagination with ellipsis, and status badge component — replacing the placeholder page.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Create JDStatusBadge, JDTable, JDFilterBar, JDPagination components | `415e6bf` | `JDStatusBadge.tsx`, `JDTable.tsx`, `JDFilterBar.tsx`, `JDPagination.tsx` |
| 2 | Rewrite JDManagement.tsx with full list page | `dab3cdd` | `JDManagement.tsx` |

## Verification

- [x] `npx tsc --noEmit` exits with code 0
- [x] 4 components + page compile without type errors
- [x] Status badge renders 3 styles (draft=secondary/gray, active=default/green, closed=outline/red)
- [x] JDTable uses @tanstack/react-table with 6 columns, sorting, empty state
- [x] JDFilterBar has keyword search (debounced 300ms), status select (all/draft/active/closed), date range (Calendar popover), reset button
- [x] JDPagination calculates totalPages, shows page numbers with ellipsis, prev/next disabled at boundaries
- [x] JDManagement integrates all components with loading (Skeleton), empty, and data states
- [x] Edit dialog placeholder ready for Plan 04 integration

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2] Added `onStatusChange` prop to JDTable**
- **Found during:** Task 1 (JDTable creation)
- **Issue:** The action column's DropdownMenu includes status-change items ("发布", "关闭", "重新激活") but the plan's JDTable interface only specified `onEdit` as a prop, leaving no way for those items to trigger mutations.
- **Fix:** Added optional `onStatusChange?: (id: number, status: string) => void` prop to JDTable. JDManagement.tsx passes `handleStatusChange` which calls `useUpdateJDStatus().mutate()`.
- **Commit:** `415e6bf`
- **Type:** Missing critical functionality — status dropdown actions are unusable without a handler.

### Plan-Exact Items

All other aspects of the plan were executed exactly as written.

## Known Stubs

| Stub | File | Line | Reason |
|------|------|------|--------|
| Edit dialog placeholder | `JDManagement.tsx` | 93-99 | Dialog shows "编辑功能" text. Plan 04 will replace with actual JDForm. |
| "新建 JD" button onClick is empty | `JDManagement.tsx` | 78 | Intentionally empty; Plan 04 will wire this to open create dialog. |

## Threat Flags

None — no new security-relevant surface introduced. Filter parameters (keyword, status, dates) are URL query params with no sensitive data. Status dropdown actions go through the existing `useUpdateJDStatus` mutation.

## Self-Check: PASSED

- [x] `frontend/src/components/JDs/JDStatusBadge.tsx` exists (31 lines, >= 20)
- [x] `frontend/src/components/JDs/JDTable.tsx` exists (165 lines, >= 60)
- [x] `frontend/src/components/JDs/JDFilterBar.tsx` exists (132 lines, >= 80)
- [x] `frontend/src/components/JDs/JDPagination.tsx` exists (89 lines, >= 50)
- [x] `frontend/src/pages/JDManagement.tsx` exists (108 lines, >= 80)
- [x] `415e6bf` commit exists
- [x] `dab3cdd` commit exists
- [x] `npx tsc --noEmit` exits 0
- [x] No placeholder strings ("功能开发中", "敬请期待") remain
