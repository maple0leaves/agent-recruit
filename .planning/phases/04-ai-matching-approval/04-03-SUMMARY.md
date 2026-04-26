---
phase: 04-ai-matching-approval
plan: 03
subsystem: frontend
tags: [types, api-client, react-hooks, sse, tanstack-query, ui-components, shadcn-ui, matching]
requires:
  - phase: 04-01
    provides: MatchSession model, per-candidate approval flow
  - phase: 04-02
    provides: HITL streaming endpoints (POST /recruit/hitl/stream, POST /recruit/hitl/resume)
provides:
  - Matching TypeScript types (MatchResult, PipelineStep, MatchingState, etc.)
  - API client functions (startMatchingStream, submitReview, fetchDashboardStats)
  - useMatchingSSE hook with 9-state SSE state machine
  - useDashboardStats TanStack Query hook with staleTime: Infinity
  - PipelineSteps 4-step visualization component
  - MatchCandidateCard component with score/badges/actions
  - ReviewNoteDialog with enforced rejection note
  - CancelMatchDialog confirmation dialog
  - StatsCard dashboard metric card component
affects:
  - 04-04: Matching and Dashboard pages will consume these building blocks
tech-stack:
  added: ["@tanstack/react-query (already present, new usage pattern)"]
  patterns:
    - "SSE consumption via fetch + ReadableStream with 9-state machine (useMatchingSSE)"
    - "staleTime: Infinity for page-load-only dashboard data (useDashboardStats)"
    - "Per-candidate approve/reject UI with required rejection note validation"
    - "Pipeline visualization with CSS pulse animation on active step"
key-files:
  created:
    - frontend/src/types/matching.ts
    - frontend/src/api/matching.ts
    - frontend/src/api/dashboard.ts
    - frontend/src/hooks/useMatchingSSE.ts
    - frontend/src/hooks/useDashboard.ts
    - frontend/src/components/Matching/PipelineSteps.tsx
    - frontend/src/components/Matching/MatchCandidateCard.tsx
    - frontend/src/components/Matching/ReviewNoteDialog.tsx
    - frontend/src/components/Matching/CancelMatchDialog.tsx
    - frontend/src/components/Dashboard/StatsCard.tsx
  modified:
    - frontend/src/components/ui/progress.tsx (installed via shadcn)
key-decisions:
  - "startMatchingStream accepts optional AbortSignal for SSE cancellation via AbortController"
  - "useMatchingSSE uses startMatchingStream API function (not raw fetch) to avoid unused import and follow API layer pattern"
  - "useDashboardStats uses staleTime: Infinity to prevent automatic refetch on page navigation"
  - "ReviewNoteDialog enforces non-empty feedback only for rejection (isRejection === true); approval notes are optional"
patterns-established:
  - "TanStack Query hook pattern: named export, explicit return type via useQuery<T> generic"
  - "SSE consuming hook pattern: 9-state state machine with useCallback + useRef + useEffect cleanup"
  - "Component pattern: default export, interface Props, shadcn/ui v4 base-nova components"
requirements-completed:
  - MATCH-01
  - MATCH-02
  - MATCH-03
  - APRV-01
  - APRV-02
  - DASH-01
duration: 8min
completed: 2026-04-26
---

# Phase 4 Plan 3: Frontend Infrastructure for Matching and Dashboard

**Matching types, SSE state management hook, per-candidate review UI, and dashboard stats component built for Phase 4 consumption.**

## Tasks Completed

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | Create matching types, API functions, and dashboard API functions | Done | `d5c0a8f` |
| 2 | Create useMatchingSSE and useDashboard hooks | Done | `a5e9743` |
| 3 | Create matching and dashboard UI components | Done | `62a8580` |

### Task 1: Types + API Layer

**Files created:**
- `frontend/src/types/matching.ts` (30 lines) — 6 interfaces + 1 type alias + 1 const array
- `frontend/src/api/matching.ts` (20 lines) — `startMatchingStream` (fetch SSE) + `submitReview` (axios POST)
- `frontend/src/api/dashboard.ts` (9 lines) — `fetchDashboardStats` (axios GET)

**Key details:**
- `MatchingState` = 9 union states (IDLE through CANCELLED)
- `MatchResult` includes `candidate_name`, `match_score`, `matched_skills`, `missing_skills`, `recommendation`, `should_proceed`
- `startMatchingStream` accepts optional `signal?: AbortSignal` for cancellation via AbortController
- `DashboardStats` captures `active_jds`, `total_candidates`, `pending_approvals`

### Task 2: State Management Hooks

**Files created:**
- `frontend/src/hooks/useMatchingSSE.ts` (193 lines) — Full SSE state machine
- `frontend/src/hooks/useDashboard.ts` (14 lines) — TanStack Query hook

**Key details:**
- `useMatchingSSE` manages 9-state machine: IDLE/CONNECTING/STREAMING/PAUSED/REVIEWING/SUBMITTING/DONE/ERROR/CANCELLED
- SSE consumption via `fetch` + `ReadableStream.getReader()` + `TextDecoder` (POST endpoint requires fetch, not EventSource)
- Progressive candidate accumulation sorted descending by `match_score` (D-08)
- LangGraph node name mapping: `triage_router` -> triage, `planner_agent` -> search, `worker_agent` -> score, `reviewer_agent` -> review
- `hitl_pause` event sets thread_id, sorts candidates, transitions to PAUSED
- `AbortController` cleanup on unmount via `useEffect`
- `useDashboardStats` uses `staleTime: Infinity` for page-load-only refresh (D-14)

### Task 3: UI Components

**Files created:**
- `frontend/src/components/Matching/PipelineSteps.tsx` (54 lines)
- `frontend/src/components/Matching/MatchCandidateCard.tsx` (101 lines)
- `frontend/src/components/Matching/ReviewNoteDialog.tsx` (107 lines)
- `frontend/src/components/Matching/CancelMatchDialog.tsx` (44 lines)
- `frontend/src/components/Dashboard/StatsCard.tsx` (32 lines)

**Key details:**
- `PipelineSteps`: 4-step horizontal visualization with completed (checkmark/green), active (pulse/blue), pending (gray) states
- `MatchCandidateCard`: Candidate name, match score %, matched/missing skill badges (green/red with Check/X icons), AI recommendation, per-candidate approve/reject buttons
- `ReviewNoteDialog`: Required feedback textarea for rejection (validates non-empty), optional note for approval
- `CancelMatchDialog`: Confirmation dialog before stream cancellation
- `StatsCard`: Lucide icon + title + value with optional onClick navigation
- shadcn Progress component installed for potential future use

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking Issue] Fixed unused import of startMatchingStream in useMatchingSSE**
- **Found during:** Task 2
- **Issue:** The plan's code for useMatchingSSE.ts imported `startMatchingStream` from `"../api/matching"` but used raw `fetch()` instead inside the `start` callback. With `noUnusedLocals: true` in tsconfig.app.json, this would cause a TypeScript compilation error ("imported but never used").
- **Fix:** 
  - Added `signal?: AbortSignal` parameter to `startMatchingStream` in `api/matching.ts`
  - Modified `useMatchingSSE` to call `startMatchingStream(jdId, abortRef.current.signal)` instead of raw `fetch()`
- **Files modified:** `frontend/src/api/matching.ts`, `frontend/src/hooks/useMatchingSSE.ts`
- **Commit:** `d5c0a8f`

## Known Stubs

None. All components have full implementations with no placeholder data or TODO patterns.

## Threat Flags

None. The implementation follows the plan's threat model:
- T-04-08 (DoS): AbortController implemented for stream cancellation
- T-04-09 (Information Disclosure): Data only flows through authenticated API calls
- T-04-10 (Tampering): Decisions submitted to authenticated endpoint, no local persistence

## Files Created/Modified

```
NEW    frontend/src/types/matching.ts                          30 lines
NEW    frontend/src/api/matching.ts                             20 lines
NEW    frontend/src/api/dashboard.ts                             9 lines
NEW    frontend/src/hooks/useMatchingSSE.ts                    193 lines
NEW    frontend/src/hooks/useDashboard.ts                       14 lines
NEW    frontend/src/components/Matching/PipelineSteps.tsx       54 lines
NEW    frontend/src/components/Matching/MatchCandidateCard.tsx 101 lines
NEW    frontend/src/components/Matching/ReviewNoteDialog.tsx   107 lines
NEW    frontend/src/components/Matching/CancelMatchDialog.tsx   44 lines
NEW    frontend/src/components/Dashboard/StatsCard.tsx          32 lines
NEW    frontend/src/components/ui/progress.tsx                  (shadcn installed)
```

Total: 11 files, ~608 lines added across 3 commits.

## Self-Check

### Files exist check

All 10 new files confirmed on disk plus the SUMMARY itself.

### Commits verified

| Commit | Message | Status |
|--------|---------|--------|
| `d5c0a8f` | feat(04-ai-matching-approval): create matching types, API functions, and dashboard API | Found |
| `a5e9743` | feat(04-ai-matching-approval): create useMatchingSSE and useDashboard hooks | Found |
| `62a8580` | feat(04-ai-matching-approval): create matching and dashboard UI components | Found |

## Self-Check: PASSED
