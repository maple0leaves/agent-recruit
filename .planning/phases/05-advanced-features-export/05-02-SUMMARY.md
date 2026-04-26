---
phase: 05-advanced-features-export
plan: 02
type: execute
completed_requirements: [APRV-03]
subsystem: "matching"
tags: ["feedback", "HITL", "SSE", "agent-feedback", "APRV-03"]
provides:
  - "Feedback loop: HR can send feedback during review, triggering agent re-adjustment with SSE re-stream"
affects:
  - api/server.py: HITLResumeRequest extended, hitl_resume endpoint with SSE mode
  - frontend/src/pages/Matching.tsx: integrated feedback flow
requires: [01]  # reverse matching (plan 05-01)
tech-stack:
  added:
    - "FastAPI StreamingResponse for feedback re-run SSE"
    - "React FeedbackDialog component (shadcn/ui Dialog + Textarea pattern)"
  patterns:
    - "Same SSE event format as _stream_hitl_recruitment"
    - "Same dialog pattern as ReviewNoteDialog"
key-files:
  created:
    - frontend/src/components/Matching/FeedbackDialog.tsx
  modified:
    - api/server.py
    - frontend/src/api/matching.ts
    - frontend/src/hooks/useMatchingSSE.ts
    - frontend/src/pages/Matching.tsx
    - frontend/src/components/Matching/MatchCandidateCard.tsx
decisions:
  - "Use Approach A for frontend SSE: submitFeedbackAndStream returns raw Response, hook reads SSE directly"
  - "Create separate SSE generator (_stream_feedback_rerun) instead of parameterizing _stream_hitl_recruitment"
  - "Copy jd_id/candidate_id from original MatchSession for the re-run session"
metrics:
  duration: "2 min"
  completed: "2026-04-26"
  tasks: 3
  files: 6 (1 new + 5 modified)
---

# Phase 05 Plan 02: Agent Feedback with SSE Re-stream (APRV-03)

Full feedback loop: HR clicks feedback button on a candidate card during review, enters free-text feedback in a dialog, submits to trigger agent re-adjustment with SSE re-streaming of updated results.

## Tasks

### Task 1: Backend feedback support (commit `12a73cf`)
- Added `feedback_rerun: bool` and `global_feedback: str` to `HITLResumeRequest`
- Modified `hitl_resume` endpoint: when `feedback_rerun=True`, returns SSE `StreamingResponse` instead of JSON
- Created `_stream_feedback_rerun` generator: creates new graph thread with feedback context, streams updated results via SSE
- Copies `jd_id`/`candidate_id` from original `MatchSession` for the re-run session
- Backward compatible: `feedback_rerun=False` (default) returns JSON as before

### Task 2: FeedbackDialog and MatchCandidateCard (commit `9231101`)
- Created `FeedbackDialog.tsx`: shadcn/ui Dialog with free-text Textarea, validation (non-empty required), submit/cancel buttons
- Added `onFeedback` prop to `MatchCandidateCard` interface
- Renders feedback button in card footer when `onFeedback` is provided, disabled for reviewed cards

### Task 3: Frontend feedback flow integration (commit `936693d`)
- Added `submitFeedbackAndStream` API function (fetch-based SSE for re-run results)
- Added `submitFeedback` callback to `useMatchingSSE` hook: sends feedback, resets state and candidates, reads SSE stream for updated results, transitions to PAUSED for re-review
- Integrated `FeedbackDialog` in `Matching.tsx`: feedback button on candidate cards, `handleFeedbackSubmit` clears review map on success

## Verification

- Backend: `feedback_rerun` (5), `global_feedback` (3), `_stream_feedback_rerun` (2) all present
- Frontend: `FeedbackDialog.tsx` exists, `onFeedback` in `MatchCandidateCard` (4 refs), `submitFeedback` in `useMatchingSSE` (4 refs)
- TypeScript: compiles with no errors
- Python: `api.server` module imports successfully

## Deviations from Plan

None -- plan executed exactly as written.

## Threat Surface Scan

No new threat surface introduced beyond what the plan's threat model covers:
- T-05-04: feedback_rerun/global_feedback via Pydantic BaseModel (mitigated)
- T-05-05: 120s timeout on SSE stream (accepted)
- T-05-06: JWT auth on endpoint (mitigated)

## Known Stubs

None.

## Self-Check: PASSED
