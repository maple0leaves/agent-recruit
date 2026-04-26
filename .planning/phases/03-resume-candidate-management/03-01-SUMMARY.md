---
phase: 03-resume-candidate-management
plan: 01
type: execute
completed_at: 2026-04-26T18:31:31Z
duration: ~5 min
tasks: 3/3
requirements_met:
  - RES-01: HR can upload resume (PDF/Word) - implemented
  - RES-02: System auto-parses resume via Agent - implemented
  - RES-03: HR can view/update candidate detail - implemented
  - RES-04: HR can search candidate DB (name, skill, status) - implemented
  - RES-05: Candidate status tracking (state machine) - implemented
decisions_implemented:
  - D-01: Reuse analyze_resume tool from agent.tools
  - D-02: Accept PDF and .docx, max 10MB
  - D-03: Sync parsing via asyncio.to_thread
  - D-04: Editable candidate fields via PUT
  - D-05: Parse failure returns partial success with warnings
  - D-06: Standard Candidate model fields
  - D-07: File stored on disk, path in DB
  - D-08: 5-state pipeline enum
  - D-09: status_note required on transitions
  - D-14: State machine: new->screening->interview->hired|rejected
  - D-15: Hired/rejected terminal states, irreversible
  - D-16: status_note required on every transition
  - D-17: No DELETE endpoint
commits:
  - dbc9617: test(03-01): add candidate integration tests
  - 2c529b9: feat(03-01): add Candidate model, Alembic migration, python-docx dependency
  - 6dbc035: feat(03-01): add candidate API routes (upload, CRUD, status machine)
test_results: 29/29 candidate tests pass; 52/52 full suite pass
---

# Phase 03 Plan 01: Backend Candidate Model, Migration, Upload/CRUD/Status API, Tests

**Objective:** Create all backend infrastructure for candidate management: Candidate data model, Alembic migration, resume upload with Agent parsing integration, CRUD API endpoints, server-side search/filter/pagination list API, pipeline status state machine API, and comprehensive integration tests.

**Status:** Complete -- all 3 tasks executed, 29 new tests pass, full suite 52/52 green.

## Files Created

| File | Purpose |
|------|---------|
| `tests/test_candidate.py` | 29 integration tests across 5 test classes (upload, list, CRUD, status, lifecycle) |
| `backend/db/models/candidate.py` | Candidate ORM model with CandidateStatus enum |
| `backend/db/migrations/versions/8ad9bbe9b0ac_create_candidates_table.py` | Alembic migration creating candidates table |
| `backend/api/routes/candidate.py` | 5 API endpoints: upload, list, get, update, status |

## Files Modified

| File | Change |
|------|--------|
| `backend/db/migrations/env.py` | Added Candidate import for autogenerate detection |
| `requirements.txt` | Added python-docx>=1.0.0 |
| `.gitignore` | Added data/resumes/ to prevent committing uploaded resumes |
| `api/server.py` | Added candidate_router import and registration |

## Test Commits

| Task | Commit | Files |
|------|--------|-------|
| 1 - Test file | `dbc9617` | `tests/test_candidate.py` |
| 2 - Model + migration | `2c529b9` | `backend/db/models/candidate.py`, `backend/db/migrations/env.py`, `requirements.txt`, `.gitignore`, migration version file |
| 3 - API routes | `6dbc035` | `backend/api/routes/candidate.py`, `api/server.py` |

## Deviations from Plan

None -- plan executed exactly as written. All tasks completed without deviation.

## Key Decisions Made

- `CandidateResponse` uses `model_config = ConfigDict(from_attributes=True)` for ORM-to-Pydantic conversion (simpler than manual dict conversion used by JD routes)
- `status_note` validation strips whitespace and rejects empty strings in Pydantic validator, matching D-09/D-16
- File save uses `RESUME_DIR` from `config.py` (pre-existing) for absolute path, stores relative `data/resumes/` path in DB
- `.doc` files rejected with specific message suggesting save-as `.docx`
- `analyze_resume.invoke()` wrapped in `await asyncio.to_thread()` to avoid blocking event loop
- `CandidateUpdate` uses `model_dump(exclude_none=True)` for partial updates -- only explicitly provided fields are set

## Threat Mitigations Applied

| Threat | Mitigation |
|--------|-----------|
| T-RES-01 (DoS via large file) | 10MB file size limit; format whitelist; asyncio.to_thread wrapping |
| T-RES-02 (Path traversal) | UUID-based filename; user filename discarded |
| T-RES-03 (Mass assignment) | CandidateUpdate defines exact allowed fields; status changes only via PATCH |
| T-RES-04 (SQL injection) | Parameterized queries via SQLAlchemy ilike() |
| T-RES-05 (Unauthorized access) | All endpoints protected with Depends(get_current_user) |
| T-RES-06 (Status tampering) | Dict-based transition validation; terminal states empty list |
| T-RES-07 (Resume file exposure) | .gitignore prevents committing uploaded files |

## Verification

```
# Candidate tests
python -m pytest tests/test_candidate.py -x -q  # 29 passed

# Full suite
python -m pytest tests/ -v -q                     # 52 passed

# Alembic migration
python -m alembic current                         # 8ad9bbe9b0ac (head)

# Server import
python -c "from api.server import app"            # OK

# python-docx
python -c "from docx import Document"             # OK

# .gitignore
grep -c "data/resumes/" .gitignore                # 1
```

## Self-Check: PASSED

All created files verified: `tests/test_candidate.py`, `backend/db/models/candidate.py`, `backend/db/migrations/versions/8ad9bbe9b0ac_create_candidates_table.py`, `backend/api/routes/candidate.py`. All commits verified in git log. Full test suite 52/52 passes.
