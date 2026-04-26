---
phase: 01-backend-foundation-auth
plan: 05
type: execute
wave: 2
subsystem: backend-auth-hardening
tags:
  - backend
  - auth-middleware
  - async-endpoints
  - sse-timeout
  - disconnect-detection
  - sqlite-saver
  - cors
  - hitl-thread-id
requires:
  - "01-02-backend-auth"
provides:
  - "Auth middleware on all protected API endpoints (Depends(get_current_user))"
  - "All sync def endpoints converted to async def with asyncio.to_thread()"
  - "SSE streaming with 120s timeout, client disconnect detection, [DONE] sentinel"
  - "SqliteSaver persistent checkpoints replacing InMemorySaver"
  - "UUID-per-session HITL thread IDs (no hardcoded hitl-thread)"
affects:
  - api/server.py
  - main.py
  - requirements.txt
tech-stack:
  added:
    - "langgraph-checkpoint-sqlite>=3.0.0"
  patterns:
    - "async def endpoints with Depends(get_current_user) for auth"
    - "asyncio.to_thread() for CPU-bound LangGraph graph.invoke() calls"
    - "asyncio.wait_for + asyncio.FIRST_COMPLETED for SSE timeout and disconnect detection"
    - "finally block yields _sse_event('done', {}) on ALL terminal paths"
    - "UUID generation per HITL session (f'hitl-{uuid4().hex}')"
key-files:
  created: []
  modified:
    - "api/server.py"
    - "main.py"
    - "requirements.txt"
decisions: []
metrics:
  duration: 8m
  completed: "2026-04-26T16:20:27Z"
  tasks: 3
  files: 3
  commits: 3
---

# Phase 1 Plan 5: Completed — Backend Hardening (Auth, Async, SSE, Checkpoints)

**One-liner:** Hardened the entire backend: protected all endpoints with `Depends(get_current_user)`, converted all sync `def` handlers to `async def` with `asyncio.to_thread()` for CPU-bound graph invoke, added 120-second timeout and client disconnect detection to SSE streaming with `[DONE]` sentinel on all terminal paths, replaced `InMemorySaver` with `SqliteSaver` for persistent LangGraph checkpoints, and fixed hardcoded HITL thread IDs to UUID-per-session.

## Summary

Executed plan 01-05 across 3 atomic tasks, each committed separately. All modified files import cleanly. No deviations were needed -- the plan was executed exactly as written.

### Task 1: Auth middleware, sync-to-async conversion, CORS fix, HITL thread_id (`2a39e8c`)

Modified `api/server.py`:

- Added `Depends`, `Request` to FastAPI imports; added `from backend.api.deps import get_current_user`
- Converted all 10 endpoint handlers to `async def` (previously 9 were sync `def`)
- Protected 7 endpoints with `Depends(get_current_user)`: `POST /recruit`, `POST /recruit/hitl/start`, `POST /recruit/hitl/resume`, `POST /recruit/stream`, `GET /skills`, `POST /upload-resume`, `POST /admin/rebuild-index`
- Left `/` and `/health` public (SPA entry and monitoring)
- Wrapped all `graph.invoke()` calls with `asyncio.to_thread()` to prevent event loop blocking
- Updated `HITLStartRequest.thread_id` from `str = "hitl-thread"` to `Optional[str] = None` with UUID generation per session
- Updated `HITLResumeRequest.thread_id` from `str = "hitl-thread"` to required `str` with no default
- CORS already configured with explicit `CORS_ORIGINS` and `allow_credentials=True` (from Plan 01-02)

### Task 2: SSE timeout, disconnect detection, [DONE] sentinel (`0624ab8`)

Modified `_stream_recruitment` async generator in `api/server.py`:

- Added `request: Request` parameter for disconnect detection
- Added `TIMEOUT_SECONDS = 120` with `asyncio.wait_for` around the graph executor
- Added client disconnect detection via `await request.is_disconnected()` with task cancellation
- Added `[DONE]` sentinel (`yield _sse_event("done", {})`) via `finally` block and explicit yields on timeout/disconnect paths
- Explicit `except asyncio.TimeoutError` catch for timeout error reporting
- Updated `recruit_stream` endpoint to pass `http_request: Request` to `_stream_recruitment`

### Task 3: SqliteSaver in main.py (`52f1833`)

Modified `main.py`:

- Replaced `from langgraph.checkpoint.memory import InMemorySaver` with `import sqlite3` and `from langgraph.checkpoint.sqlite import SqliteSaver`
- Replaced `InMemorySaver()` instantiation with `sqlite3.connect("data/dev.db", check_same_thread=False)` + `SqliteSaver(sqlite_conn)`
- Added `langgraph-checkpoint-sqlite>=3.0.0` to `requirements.txt`
- Both `recruitment_graph` and `recruitment_graph_hitl` verify with `SqliteSaver` checkpointer type

## Deviations from Plan

None -- plan executed exactly as written.

## Threat Coverage

All mitigated threats from the plan's threat model are addressed:

| Threat ID | Category | Mitigation | Status |
|-----------|----------|------------|--------|
| T-1-12 | Denial of Service (SSE) | 120s timeout + disconnect detection | Implemented (Task 2) |
| T-1-13 | Elevation of Privilege | `Depends(get_current_user)` on all endpoints | Implemented (Task 1) |
| T-1-14 | Denial of Service (Event loop) | `async def` + `asyncio.to_thread()` | Implemented (Task 1) |
| T-1-15 | Tampering (DB file) | Accepted (local filesystem only) | Documented |
| T-1-16 | Elevation of Privilege (Session collision) | UUID per HITL session | Implemented (Task 1) |

## Key Links

| From | To | Via |
|------|----|------|
| api/server.py | backend/api/deps.py | `Depends(get_current_user)` |
| api/server.py | asyncio | `asyncio.wait_for`, `asyncio.to_thread()`, `request.is_disconnected()` |
| api/server.py | main.py | `recruitment_graph.stream()`, `recruitment_graph_hitl.invoke()` |
| main.py | data/dev.db | `sqlite3.connect("data/dev.db")` |

## Self-Check: PASSED

- [x] `python -c "from api.server import app; print('Server loads')"` exits 0
- [x] `python -c "from main import recruitment_graph; print('Graph loads')"` exits 0
- [x] `python -c "from backend.api.deps import get_current_user; print('Auth deps available')"` exits 0
- [x] `asyncio.wait_for` present in `api/server.py`
- [x] `is_disconnected` present in `api/server.py`
- [x] `[DONE]` sentinel (`_sse_event("done", {})`) on all terminal paths (3 occurrence sites covering disconnect, timeout, exception, and normal completion via `finally`)
- [x] `SqliteSaver` present in `main.py`
- [x] No `InMemorySaver` remaining in `main.py`
- [x] `langgraph-checkpoint-sqlite` in `requirements.txt`
- [x] All endpoints are `async def` (10 async def vs 2 helper sync def)
- [x] Commits: `2a39e8c`, `0624ab8`, `52f1833` all present in git log
