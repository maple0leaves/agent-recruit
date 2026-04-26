---
phase: 03-resume-candidate-management
plan: 03
subsystem: frontend-candidate-ui
tags: [react, tanstack-table, shadcn-ui, candidate-list, file-upload]

# Dependency graph
requires:
  - phase: 03-01
    provides: backend candidate API routes and model
  - phase: 03-02
    provides: Candidate TypeScript types, Axios API, TanStack Query hooks
provides:
  - Candidate list page with paginated TanStack Table
  - Pipeline status badge component (5 statuses with color coding)
  - Candidate filter bar with debounced keyword search and status dropdown
  - Resume upload widget with drag-drop, progress bar, and client-side validation
affects:
  - Plan 03-04: Candidate detail and pipeline management UI

# Tech tracking
tech-stack:
  added:
    - "@tanstack/react-table" (already installed)
  patterns:
    - "TanStack Table wrapper following JDTable pattern"
    - "Debounced search input using useRef + setTimeout (300ms)"
    - "Status badge component with shadcn Badge variant mapping"
    - "Inline pagination component (no separate Pagination component for candidates)"
    - "Upload widget with FormData via hook (no direct FormData usage in component)"

key-files:
  created:
    - frontend/src/components/Candidates/PipelineStatusBadge.tsx
    - frontend/src/components/Candidates/CandidateTable.tsx
    - frontend/src/components/Candidates/CandidateFilterBar.tsx
    - frontend/src/components/Candidates/CandidateUpload.tsx
  modified:
    - frontend/src/pages/Candidates.tsx (fully replaced placeholder)

key-decisions:
  - "PipelineStatusBadge uses green tint overrides (bg-green-100) for 'hired' status instead of default blue"
  - "CandidateFilterBar uses separate searchInput state with debounce (matching JDFilterBar pattern), not direct prop binding"
  - "CandidateUpload uses hidden file input with clickable styled zone + drag-drop, not a shadcn dialog"
  - "Pagination is inline in Candidates.tsx (not a separate component) since it is page-specific"
  - "Upload resets filter page to 1 on success to show the newly uploaded candidate"

patterns-established:
  - "Candidate components follow same patterns as JD components (status badge, table, filter bar) for consistent UX"
  - "Upload widget handles 4 states (idle, uploading, success, error) with visual feedback for each"
  - "Page composition follows JDManagement pattern: header + filter + content (loading/empty/data) + pagination"

requirements-completed:
  - RES-01
  - RES-02
  - RES-04

# Metrics
duration: 5min
completed: 2026-04-26
---

# Phase 03 Plan 03: Candidate List Page with Table, Filter, Upload, and Pagination Summary

**Five UI components replacing the placeholder candidates page: TanStack Table with sorting, filter bar with debounced search and status dropdown, pipeline status badge, resume upload widget, and inline pagination**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-26T18:35:00Z
- **Completed:** 2026-04-26T18:39:28Z
- **Tasks:** 3
- **Files created:** 4
- **Files modified:** 1

## Accomplishments
- Created PipelineStatusBadge component with 5 status configs (new=screening, screening=secondary, interview=default, hired=green, rejected=destructive) using shadcn Badge
- Created CandidateTable with @tanstack/react-table: 4 columns (name/skills/status/created_at), client-side sorting, clickable rows, empty state
- Created CandidateFilterBar with debounced keyword search (300ms using useRef + setTimeout), status filter dropdown, and reset button
- Created CandidateUpload with drag-drop zone, hidden file input fallback, client-side file type validation (.pdf/.docx), client-side size validation (10MB limit), upload progress bar with percentage, success state auto-reset (3s), and error state with retry
- Replaced Candidates.tsx placeholder page with full implementation: header with toggle upload button, filter bar, upload widget (conditionally shown), loading skeleton state, empty state with guidance, CandidateTable with data, and inline pagination with page number buttons
- All components pass TypeScript compilation with zero errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Create PipelineStatusBadge, CandidateTable, CandidateFilterBar** - `e08768f` (feat)
2. **Task 2: Create CandidateUpload component** - `61a11aa` (feat)
3. **Task 3: Replace Candidates.tsx with full list page** - `52c4563` (feat)

**Plan metadata:** *(to be committed)*

## Files Created
- `frontend/src/components/Candidates/PipelineStatusBadge.tsx` - Colored shadcn Badge for candidate pipeline status (new/screening/interview/hired/rejected)
- `frontend/src/components/Candidates/CandidateTable.tsx` - TanStack Table wrapper with 4 columns, sorting, clickable rows, empty state
- `frontend/src/components/Candidates/CandidateFilterBar.tsx` - Debounced keyword search input + status filter Select + reset button
- `frontend/src/components/Candidates/CandidateUpload.tsx` - Drag-drop upload zone with 4-state machine (idle/uploading/success/error), progress bar, client-side validation, auto-reset on success

## Files Modified
- `frontend/src/pages/Candidates.tsx` - Fully replaced placeholder (Card with "功能开发中") with complete list page integrating all 4 sub-components plus inline pagination

## Decisions Made
- PipelineStatusBadge uses green tint overrides for "hired" status (bg-green-100 text-green-800 border-green-200) to distinguish from the default blue "interview" badge
- CandidateFilterBar uses internal searchInput state with debounce rather than direct two-way binding, matching the JDFilterBar pattern and preventing excessive API calls on every keystroke
- CandidateUpload's success state auto-resets to idle after 3 seconds to allow repeated uploads without manual dismissal
- Pagination is built inline in the Candidates.tsx page rather than as a reusable component since the pagination pattern is page-specific
- Upload success handler resets the page filter to 1 to ensure the newly uploaded candidate appears in the first page of results

## Deviations from Plan

None - plan executed as written.

### Acceptance Criteria Verification

| Criterion | Result | Evidence |
|---|---|---|
| PipelineStatusBadge.tsx imports Badge from ui/badge | PASS | `import { Badge } from "@/components/ui/badge"` |
| All 5 status configs present | PASS | STATUS_CONFIG has new, screening, interview, hired, rejected |
| CandidateTable.tsx imports useReactTable | PASS | `import { useReactTable, ... } from "@tanstack/react-table"` |
| Clickable rows with onSelect | PASS | `onClick={() => onSelect(row.original)}` on TableRow |
| CandidateFilterBar debounced (300ms) | PASS | `setTimeout(() => ..., 300)` pattern in handleSearchChange |
| CandidateUpload uses useUploadCandidate | PASS | `const uploadMutation = useUploadCandidate()` |
| CandidateUpload has onUploadProgress usage | PASS | `onProgress: (pct) => setUploadProgress(pct)` |
| CandidateUpload no direct FormData | PASS | 0 occurrences of FormData (handled by hook) |
| CandidateUpload accepts .pdf,.docx | PASS | `accept=".pdf,.docx"` on file input |
| CandidateUpload validates file size | PASS | `file.size > 10 * 1024 * 1024` check |
| Candidates.tsx uses useCandidates | PASS | 2 matches (import + usage) |
| Candidates.tsx imports sub-components | PASS | CandidateFilterBar(2), CandidateTable(2), CandidateUpload(4) |
| Old placeholder strings absent | PASS | 0 matches for "功能开发中" or "敬请期待" |
| Skeleton loading state | PASS | `<Skeleton>` in loading branch |
| Empty state | PASS | Users icon + "暂无候选人数据，请上传简历" |
| Pagination with page numbers | PASS | getPageNumbers() with prev/next buttons |
| tsc --noEmit succeeds | PASS | Exit code 0, zero errors |

## Issues Encountered

None - all tasks completed as planned.

## Threat Surface Scan

No new threat surface introduced. All file upload validation (type and size) is done client-side before transmission. Search/filter parameters are plain text query params. No new network endpoints added.

## Risk Items
- The `selectedCandidateId` state is set on row click but not yet used for navigation. Plan 03-04 is expected to handle detail view navigation using this state.

## Next Phase Readiness
- All candidate list UI components ready for Plan 03-04 (candidate detail view and pipeline status management)
- CandidateTable.onSelect handler wired to setSelectedCandidateId -- Plan 03-04 can build detail view navigation on top
- CandidateUpload.onSuccess callback resets page to 1 and triggers invalidateQueries via the hook, ensuring the list auto-refreshes

## Self-Check: PASSED

- All 5 source files exist and compile
- All 3 task commits verified (e08768f, 61a11aa, 52c4563)
- SUMMARY.md written with full deviation, threat, and stub documentation

---
*Phase: 03-resume-candidate-management*
*Completed: 2026-04-26*
