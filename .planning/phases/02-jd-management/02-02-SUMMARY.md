---
phase: 02-jd-management
plan: 02
subsystem: frontend, types, api-client, hooks
tags: jd-infrastructure, shadcn-ui, tanstack-query, typescript, npm-packages

# Dependency graph
requires:
  - phase: 01-backend-foundation-auth
    provides: React 19 + Vite + TypeScript shell, shadcn/ui v4 base-nova style, TanStack Query v5, axios apiClient
provides:
  - 4 new npm packages (@tanstack/react-table@8, react-hook-form@7, react-day-picker@9, date-fns@4)
  - 10 shadcn/ui v4 base-nova components (table, form, select, badge, textarea, popover, calendar, dialog, command, dropdown-menu)
  - TypeScript types for JD domain (JD, JDListResponse, JDFormValues, JDTemplate, JDStatus, EducationLevel)
  - 5 Axios API functions (fetchJDs, fetchJDTemplates, createJD, updateJD, updateJDStatus)
  - 5 TanStack Query hooks (useJDs, useJDTemplates, useCreateJD, useUpdateJD, useUpdateJDStatus)
affects:
  - 03-resume-candidate-management (resume hooks will follow same pattern)
  - 04-ai-matching-approval (matching results reuse existing hooks pattern)

# Tech tracking
tech-stack:
  added:
    - "@tanstack/react-table: ^8.21.3"
    - "react-hook-form: ^7.74.0"
    - "react-day-picker: ^9.14.0"
    - "date-fns: ^4.1.0"
    - "@radix-ui/react-label: ^2.1.8 (shadcn form dependency)"
    - "@radix-ui/react-slot: ^1.2.4 (shadcn form dependency)"
  patterns:
    - "Types defined in frontend/src/types/ with export interface pattern"
    - "API functions import apiClient from ./client with typed axios responses"
    - "Hooks import API functions, use queryKey [domain, action] convention"
    - "keepPreviousData imported as function (TanStack Query v5 API), not boolean (v4)"
    - "Mutations invalidate [jd, list] queryKey on success"
    - "Templates hook uses staleTime: Infinity (never change per D-11)"

# Key files
key-files:
  created:
    - frontend/src/components/ui/table.tsx
    - frontend/src/components/ui/form.tsx
    - frontend/src/components/ui/select.tsx
    - frontend/src/components/ui/badge.tsx
    - frontend/src/components/ui/textarea.tsx
    - frontend/src/components/ui/popover.tsx
    - frontend/src/components/ui/calendar.tsx
    - frontend/src/components/ui/dialog.tsx
    - frontend/src/components/ui/command.tsx
    - frontend/src/components/ui/dropdown-menu.tsx
    - frontend/src/types/jd.ts
    - frontend/src/api/jd.ts
    - frontend/src/hooks/useJDs.ts
  modified:
    - frontend/package.json
    - frontend/package-lock.json

# Metrics
metrics:
  duration: "5m 15s"
  completed: "2026-04-26T17:31:35Z"
  tasks: 3
  commits: 3
---

# Phase 2 Plan 2: Frontend Infrastructure for JD Management

Install all Phase 2 frontend dependencies and shadcn components, create JD domain TypeScript type definitions, API call functions, and TanStack Query wrapper hooks. Establishes non-UI infrastructure so subsequent UI components (Plans 03 and 04) can directly consume typed APIs and hooks.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] shadcn form component unavailable in base-nova registry**
- **Found during:** Task 1
- **Issue:** `npx shadcn@latest add form -y` succeeds (exit 0) but does not create `form.tsx`. The registry API for base-nova style returns a skeleton entry without files content. The form component was silently skipped.
- **Fix:** Created `form.tsx` manually following shadcn v4 base-nova patterns (data-slot attributes, cn utility, use client directive). Installed required Radix UI peer dependencies (`@radix-ui/react-label`, `@radix-ui/react-slot`).
- **Files modified:** `frontend/src/components/ui/form.tsx`, `frontend/package.json`, `frontend/package-lock.json`
- **Commit:** e251596

### Scope Boundary

- `@radix-ui/react-label` and `@radix-ui/react-slot` were installed as peer dependencies of the form component. These are not listed in the plan's npm packages but are required for the form to function. No other files outside the plan scope were modified.

## Key Decisions

1. **shadcn v4 base-nova form component manually created** -- The form component was not available via the shadcn CLI for the base-nova style. Created manually following the same conventions as other installed v4 components (data-slot attributes, cn import from @/lib/utils, "use client" directive). Per D-05 through D-08, form must be available for Plan 03 JD create/edit forms.

## Success Criteria Verification

| Criterion | Status |
|-----------|--------|
| `npx tsc --noEmit` from frontend/ exits with code 0 | PASSED |
| All 10 shadcn component files exist in frontend/src/components/ui/ | PASSED |
| All 4 new npm packages listed in frontend/package.json dependencies | PASSED |
| TypeScript types, API functions, and hooks compile without errors | PASSED |
| Locked decisions (D-05 through D-11) infrastructure ready | PASSED |

## Plan Completion Summary

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Install npm packages and shadcn/ui components | e251596 | 13 files (10 new shadcn components + input-group + package.json + package-lock.json) |
| 2 | Create TypeScript types and API functions | 293c1ef | 2 new files (src/types/jd.ts, src/api/jd.ts) |
| 3 | Create TanStack Query hooks | f5d75b8 | 1 new file (src/hooks/useJDs.ts) |

## Threat Surface Scan

No new threat surface introduced. All changes are type definitions, client-side API call wrappers, and client-side hooks -- no network endpoints, auth paths, or schema modifications.
