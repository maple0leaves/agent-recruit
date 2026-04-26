---
phase: 03-resume-candidate-management
plan: 04
subsystem: frontend
tags: [candidate-detail, inline-editing, pipeline-status, match-history-placeholder]
provides:
  - CandidateDetail component (single-page scroll layout)
  - PipelineActions component (status transition controls)
  - Candidates page list/detail navigation switch
requires:
  - 03-01 (Backend: Candidate CRUD, status PATCH)
  - 03-02 (Frontend: Candidate hooks, API client)
  - 03-03 (Frontend: CandidateTable, PipelineStatusBadge)
affects:
  - frontend/src/hooks/useCandidates.ts (Rule 2: added individual candidate query invalidation)
tech-stack:
  added:
    - react-hook-form (indirectly via base-ui primitives)
  patterns:
    - Inline edit toggle using controlled form state (not react-hook-form for inline form)
    - Dialog-controlled status transitions with validation
    - Conditional list/detail view rendering
key-files:
  created:
    - frontend/src/components/Candidates/CandidateDetail.tsx
    - frontend/src/components/Candidates/PipelineActions.tsx
  modified:
    - frontend/src/pages/Candidates.tsx
    - frontend/src/hooks/useCandidates.ts
decisions:
  - Inline edit uses controlled component state (useState + Input/Textarea) instead of react-hook-form, simpler for a flat form
  - Pipeline visualization uses simple color-coded labels with arrow separators instead of a complex stepper component
  - useUpdateCandidate and useUpdateCandidateStatus now invalidate both list and individual candidate queries
metrics:
  duration: ~12 min
  completed_date: 2026-04-26
---

# Phase 03 Plan 04: Candidate Detail Page with Inline Editing, Match History Placeholder, and Pipeline Status Controls

构建候选人详情页：单页滚动布局展示解析数据、支持点击即编辑、配备匹配历史占位区域（Phase 4 填充）和 Pipeline 状态变更操作。

## Completed Tasks

### Task 1: Create CandidateDetail and PipelineActions components

**Files created:**
- `frontend/src/components/Candidates/PipelineActions.tsx` -- Pipeline status transition component with:
  - VALID_TRANSITIONS state machine (D-14): new -> screening -> interview -> hired/rejected
  - Pipeline flow visualization with color-coded stage labels
  - Clickable transition buttons for valid next statuses
  - Dialog-based status_note input with required validation
  - Error display on mutation failure
  - Terminal state (hired/rejected) handler showing "已终态，不可变更"
- `frontend/src/components/Candidates/CandidateDetail.tsx` -- Single-page scroll detail component with:
  - Section 1 (D-12): Parsed data area with InfoField display + InlineEditForm toggle
  - Section 2 (D-13): Match history placeholder with clock icon and "暂无匹配记录"
  - Section 3 (D-12): Pipeline status area with PipelineActions integration
  - Loading state with Skeleton placeholders
  - Error state with "候选人不存在" + return button

**Files modified:**
- `frontend/src/hooks/useCandidates.ts` -- Rule 2 deviation: `useUpdateCandidate` and `useUpdateCandidateStatus` now invalidate individual candidate queries (`["candidates", id]`) in addition to list queries

**Commit:** `510eb8e`

### Task 2: Integrate detail view into Candidates.tsx with list/detail navigation

**File modified:**
- `frontend/src/pages/Candidates.tsx` -- Added:
  - `CandidateDetail` import
  - `handleBackToList` handler (sets selectedCandidateId to null)
  - Conditional rendering: detail view when selectedCandidateId is set, list view otherwise
  - Existing handleSelect in CandidateTable already wires to selectedCandidateId (from Plan 03)

**Commit:** `ddbcfde`

## Deviations from Plan

### Rule 2 - Missing Critical Functionality

**1. Individual candidate query invalidation in mutation hooks**

- **Found during:** Task 1
- **Issue:** `useUpdateCandidate` and `useUpdateCandidateStatus` only invalidated `["candidates", "list"]` on success, meaning the CandidateDetail page would not refresh after editing or status change
- **Fix:** Updated both `onSuccess` callbacks to also invalidate `["candidates", variables.id]` using mutation variables
- **Files modified:** `frontend/src/hooks/useCandidates.ts`
- **Commit:** `510eb8e`

## Verification Results

1. TypeScript compilation: `npx tsc --noEmit` exits with code 0 -- PASS
2. CandidateDetail renders three sections: parsed data (editable inline), match history placeholder, pipeline status controls -- PASS
3. PipelineActions shows valid next transitions as clickable buttons -- PASS
4. Status change dialog validates status_note is non-empty -- PASS
5. Terminal states (hired/rejected) show no transition buttons -- PASS
6. Candidates.tsx conditionally renders list or detail view based on selectedCandidateId -- PASS
7. "Back to list" returns to candidate list view -- PASS
8. Inline edit toggles between read-only and edit modes -- PASS

## Self-Check: PASSED

All created files exist and all commits are verified.
