---
phase: 04-ai-matching-approval
plan: 04
type: execute
subsystem: frontend
tags:
  - matching
  - dashboard
  - review
  - sse
  - stats
requires:
  - 04-03 (hooks, components, types)
provides:
  - Full Matching page with SSE integration and review workflow
  - Full Dashboard page with stats cards
  - Matching trigger from JD table
affects:
  - frontend/src/pages/Matching.tsx
  - frontend/src/pages/Dashboard.tsx
  - frontend/src/pages/JDManagement.tsx
  - frontend/src/components/JDs/JDTable.tsx
  - frontend/src/App.tsx
tech-stack:
  added: []
  patterns:
    - "SSE-driven progressive UI with 9-state machine"
    - "Per-candidate review with review map state"
    - "Stats dashboard with TanStack Query staleTime: Infinity"
key-files:
  created: []
  modified:
    - "frontend/src/components/JDs/JDTable.tsx -- Added onStartMatching prop and dropdown item"
    - "frontend/src/pages/JDManagement.tsx -- Added useNavigate and handleStartMatching"
    - "frontend/src/pages/Matching.tsx -- Replaced placeholder with full matching page"
    - "frontend/src/App.tsx -- Added /matching/:jdId route"
    - "frontend/src/pages/Dashboard.tsx -- Replaced placeholder with stats dashboard"
metrics:
  duration: ""
  completed_date: "2026-04-26"
decisions: []
---

# Phase 4 Plan 04: Frontend Pages -- Matching and Dashboard

Wire frontend pages to complete Phase 4 user experience. JD table triggers matching navigation. Matching page integrates SSE state machine, pipeline visualization, progressive candidate cards, per-candidate review with notes, batch submission, and final report display. Dashboard displays 3 aggregate metric cards.

## Tasks

### Task 1: Add "start matching" button to JD table and page

**Commit:** `7bf4ff5`

Modified `JDTable.tsx`:
- Added `onStartMatching` prop to `JDTableProps` interface
- Added `onStartMatching` to component destructuring
- Added "开始匹配" `DropdownMenuItem` in the actions column, conditionally rendered when `onStartMatching` is provided
- Added `onStartMatching` to `useMemo` dependency array

Modified `JDManagement.tsx`:
- Added `useNavigate` from `react-router-dom`
- Added `handleStartMatching` callback that navigates to `/matching/${jd.id}`
- Passed `onStartMatching={handleStartMatching}` to `JDTable`

### Task 2: Replace Matching.tsx with full matching page

**Commit:** `cbf7e34`

Replaced placeholder `Matching.tsx` with a full implementation:
- Reads `jdId` from URL params via `useParams`; auto-starts matching on mount
- Manages 9-state UI: IDLE, CONNECTING, STREAMING, PAUSED, REVIEWING, SUBMITTING, DONE, ERROR, CANCELLED
- Integrates `PipelineSteps`, `MatchCandidateCard`, `ReviewNoteDialog`, `CancelMatchDialog`
- Review state managed as `reviewMap: Record<string, ReviewEntry>` per candidate
- "完成审核" button appears only when all candidates have been reviewed
- Final report display in DONE state alongside review summary cards
- Back button to JD list in all states

Modified `App.tsx`:
- Added `/matching/:jdId` route before `/matching` so both paths work

### Task 3: Replace Dashboard.tsx with stats dashboard

**Commit:** `96658d7`

Replaced placeholder `Dashboard.tsx`:
- Fetches stats via `useDashboardStats` hook
- Renders 3 `StatsCard` components: "活跃 JD" (Briefcase), "候选人总数" (Users), "待审核" (ClipboardCheck)
- Loading state: 3 `Skeleton` placeholders
- Pending approvals alert banner when `data.pending_approvals > 0`
- Each card navigates to respective page on click

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None.

## Threat Model Compliance

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-04-11 | jdId URL param validated with parseInt | Compliant -- `parseInt(jdId, 10)` with `isNaN()` guard in Matching.tsx |
| T-04-12 | AbortController cleanup on unmount | Compliant -- `useMatchingSSE` cleanup effect aborts on unmount; cancel button uses same AbortController |
| T-04-13 | In-memory only, no localStorage persistence | Compliant -- candidate data in React state only |

## Verification

- TypeScript compilation passes with strict mode: no errors
- `JDTable` has "开始匹配" action, calls `onStartMatching` callback
- `JDManagement` navigates to `/matching/:jdId` via `useNavigate`
- `Matching.tsx` handles all 9 states
- `Dashboard.tsx` renders 3 StatsCards with loading/error/data states
- Total: 5 files modified, 3 commits

## Self-Check: PASSED

All 5 modified files verified on disk. All 3 commits verified in git log.
