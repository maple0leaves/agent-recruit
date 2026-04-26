---
phase: 04-ai-matching-approval
plan: 02
type: execute
subsystem: backend-api
tags:
  - sse
  - hitl
  - streaming
  - dashboard
  - approvals
  - langgraph
requires:
  - 04-01 (MatchSession model, CandidateApproval schema, per-candidate reviewer_agent)
provides:
  - POST /recruit/hitl/stream (SSE streaming HITL endpoint)
  - POST /recruit/hitl/resume (per-candidate approvals)
  - GET /dashboard/stats (aggregated dashboard metrics)
affects:
  - api/server.py
  - .planning/STATE.md
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
tech-stack:
  added:
    - pydantic.Field (validation metadata for API schemas)
    - sqlalchemy.ext.asyncio.AsyncSession (async DB session dependency)
  patterns:
    - SSE streaming with asyncio Queue + thread-safe graph execution
    - MatchSession lifecycle: created on stream, updated on resume
key-files:
  created: []
  modified:
    - api/server.py
decisions:
  - Inline JD import in hitl_stream endpoint (not top-level) to avoid circular import issues
  - MatchSession status set to "approved" if any candidate is approved, "rejected" if all rejected
  - MatchSession created inside _stream_hitl_recruitment generator (not in the endpoint handler)
metrics:
  duration: 8.2 min
  completed: 2026-04-26
---

# Phase 4 Plan 2: Backend API -- Streaming HITL Endpoint, Per-Candidate Resume, Dashboard Stats

Build the streaming HITL API endpoint (POST /recruit/hitl/stream) that provides real-time SSE streaming for AI matching with the HITL graph, pausing at the reviewer interrupt for HR per-candidate review. Per-candidate approve/reject is supported via the modified POST /recruit/hitl/resume. GET /dashboard/stats aggregates JD count, candidate count, and pending MatchSession approvals.

## Completed Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Create POST /recruit/hitl/stream with HITL streaming SSE | `5c05b1a` | api/server.py |
| 2 | Modify POST /recruit/hitl/resume for per-candidate approvals + add GET /dashboard/stats | `bc40e86` | api/server.py |

## Key Changes

### Task 1: POST /recruit/hitl/stream

- **Added imports**: `Field` (pydantic), `AsyncSession` (sqlalchemy), `get_db` (deps), `MatchSession` (db model)
- **Added `HITLStreamRequest`**: Request schema with `jd_id: int` for specifying which JD to match candidates against
- **Added `_stream_hitl_recruitment`**: Async generator using `recruitment_graph_hitl.stream()` with 120-second timeout, client disconnect detection, progressive `match_result` SSE events, and `hitl_pause` event at reviewer interrupt
- **Added `hitl_stream` endpoint**: POST /recruit/hitl/stream that fetches the JD, constructs user_input, and returns a StreamingResponse with SSE events
- **MatchSession creation**: After streaming completes, creates a `MatchSession` record with `status="pending"` and `total_candidates` count for dashboard tracking

### Task 2: Per-candidate resume + Dashboard stats

- **Updated `HITLResumeRequest`**: Changed from `hr_approved: bool` to `approvals: list[CandidateApproval]` for per-candidate decisions
- **Updated `hitl_resume` endpoint**: Builds `candidate_decisions` dict from approvals, updates MatchSession with approved/rejected counts, sets status to "approved" if any candidate approved
- **Added `dashboard_stats` endpoint**: GET /dashboard/stats returns `active_jds` (JD count where status="active"), `total_candidates` (all candidates), `pending_approvals` (MatchSession count with status="pending")
- **Updated imports**: `CandidateApproval`, `JD`, `Candidate` added to top-level imports

## Deviations from Plan

None - plan executed exactly as written.

## Auth Gates

None.

## Known Stubs

None.

## Threat Flags

None.

## Threat Model Compliance

| Threat ID | Category | Component | Verification |
|-----------|----------|-----------|-------------|
| T-04-04 | DoS | POST /recruit/hitl/stream | 120s timeout via asyncio.wait_for; disconnect detection implemented |
| T-04-05 | Spoofing | POST /recruit/hitl/resume | thread_id is random uuid4.hex; endpoint requires JWT auth |
| T-04-06 | Tampering | dashboard/stats SQL | SQLAlchemy parameterized queries (no string interpolation) |
| T-04-07 | Information Disclosure | GET /dashboard/stats | JWT auth required; no PII in response |

## Verification

### Automated checks

```
# Task 1 acceptance criteria
$ grep -c "_stream_hitl_recruitment" api/server.py          -> 2 (PASS)
$ grep -c "hitl_stream" api/server.py                       -> 1 (PASS)
$ grep -c "HITLStreamRequest" api/server.py                 -> 2 (PASS)
$ grep -c "MatchSession" api/server.py                      -> 4 (PASS)
$ grep -c "get_db" api/server.py                            -> 4 (PASS)

# Task 2 acceptance criteria
$ grep -c "CandidateApproval" api/server.py                 -> 2 (PASS)
$ grep -c "approvals.*list\[CandidateApproval\]" api/server.py -> 1 (PASS)
$ grep -c "dashboard_stats" api/server.py                   -> 1 (PASS)
$ grep -c "pending_approvals" api/server.py                 -> 2 (PASS)

# Route registration
POST /recruit/hitl/stream  (PASS)
POST /recruit/hitl/resume  (PASS)
GET  /dashboard/stats      (PASS)

# HITLResumeRequest uses approvals (not hr_approved)
new class has approvals: list[CandidateApproval]             (PASS)

# _stream_hitl_recruitment uses recruitment_graph_hitl.stream()
grep -c "recruitment_graph_hitl.stream" api/server.py -> 1   (PASS)
```

### Success Criteria

- [x] `python -c "from api.server import app"` imports cleanly
- [x] All four routes identifiable: `/recruit/hitl/stream [POST]`, `/recruit/hitl/resume [POST]`, `/dashboard/stats [GET]`
- [x] `HITLResumeRequest` has `approvals: list[CandidateApproval]` (not hr_approved boolean)
- [x] `_stream_hitl_recruitment` uses `recruitment_graph_hitl.stream()`
- [x] Dashboard endpoint returns valid JSON with all 3 keys

## Requirements Progress

| Requirement | Status | Plan |
|-------------|--------|------|
| MATCH-01 | Pending | 04-02, 04-04 |
| MATCH-03 | Complete | 04-02 |
| APRV-01 | Complete | 04-02 |
| DASH-01 | Complete | 04-02 |

## Self-Check: PASSED

All created/modified files verified, all commit hashes confirmed, all acceptance criteria met.
