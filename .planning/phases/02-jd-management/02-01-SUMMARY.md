---
phase: 02-jd-management
plan: 01
subsystem: api, database, testing
tags: jd-crud, sqlalchemy, alembic, fastapi, pytest, status-machine

# Dependency graph
requires:
  - phase: 01-backend-foundation-auth
    provides: User model, async SQLAlchemy engine, Alembic migrations, FastAPI auth deps, JWT helpers, test fixtures
provides:
  - JD ORM model (jds table) with EducationLevel and JDStatus enums
  - Alembic migration 002 creating the jds table
  - 3 hardcoded JD templates (software-engineer, product-manager, sales-manager)
  - Full CRUD API (list/create/get/update/status + templates) at /jd
  - 14 integration tests covering all endpoints, filtering, pagination, templates, auth
affects:
  - 03-resume-candidate-management (resume-JD matching will consume JD model)
  - 04-ai-matching-approval (matching pipeline will read JDs from API)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "JD model follows User model pattern: Enum + Base subclass with __tablename__"
    - "JD routes follow auth routes pattern: APIRouter with prefix + Depends(get_current_user)"
    - "Status transitions enforced via dict mapping (explicit state machine)"
    - "Date filtering uses string comparison for SQLite compatibility"
    - "Pydantic field_validator for input validation (non-empty title)"

key-files:
  created:
    - tests/test_jd.py
    - backend/db/models/jd.py
    - backend/db/migrations/versions/7600d2f53813_create_jds_table.py
    - backend/config/templates.py
    - backend/api/routes/jd.py
  modified:
    - backend/db/migrations/env.py
    - api/server.py

key-decisions:
  - "Date filtering uses direct string comparison instead of cast(..., Date) because SQLite DATE cast is unreliable"
  - "JDSchema.title validated with field_validator to reject empty/whitespace-only strings"
  - "Status transition map is a dict lookup: draft->active, active->closed, closed->active"
  - "TEMPLATES stored in dedicated config module (backend/config/templates.py) following D-09"

patterns-established:
  - "New feature endpoints: APIRouter(prefix='/jd', tags=['jd']) registered via app.include_router()"
  - "Alembic migration: import model in env.py, then autogenerate"
  - "Test pattern: _auth_header helper creates JWT for authenticated tests"

requirements-completed:
  - JD-01
  - JD-02
  - JD-03
  - JD-04

# Metrics
duration: 9min
completed: 2026-04-26
---

# Phase 2 Plan 01: JD Model + Templates + Migrations + CRUD API + Tests

**JD CRUD backend with SQLAlchemy model, Alembic migration, three hardcoded templates, six REST endpoints, and 14 integration tests**

## Performance

- **Duration:** 9 min
- **Started:** 2026-04-26T17:18:03Z
- **Completed:** 2026-04-26T17:27:00Z
- **Tasks:** 3 (all executed as sequential commits)
- **Files created:** 5
- **Files modified:** 2

## Accomplishments

- JD ORM model (`JD(Base)`) with `EducationLevel` and `JDStatus` enums, mapped to `jds` table
- Alembic migration 002 creates the `jds` table with indexes on `title` and `status`
- Three hardcoded JD templates (软件工程师, 产品经理, 销售经理) in `backend/config/templates.py`
- Six API endpoints at `/jd`: list (paginated with filters), create (201), get, update, status PATCH, templates listing
- D-12 status state machine enforced: draft->active->closed->active (400 on invalid transitions)
- Server-side keyword search (title, department, skills via `ilike`), status filter, date range filter
- 14 integration tests: create/validation/unauthorized, update/close/reactivate/invalid-transition, pagination/status-filter/keyword-search/date-filter/no-filters, templates listing, all-endpoints-require-auth
- All endpoints require `Depends(get_current_user)` per D-14

## Task Commits

1. **Task 1: Create JD integration test file** - `c33f162` (test)
2. **Task 2: Create JD ORM model + Alembic migration** - `1625061` (feat)
3. **Task 3: Create template config + JD API routes + register router** - `645d7f5` (feat)
   - Fixes: title validation + SQLite date filter + test timezone - `9104a41` (fix)

**Plan metadata:** (to follow)

## Files Created
- `tests/test_jd.py` — 14 integration tests covering JD CRUD, filtering, pagination, templates, and auth
- `backend/db/models/jd.py` — JD ORM model with EducationLevel and JDStatus enums
- `backend/db/migrations/versions/7600d2f53813_create_jds_table.py` — Alembic migration creating jds table
- `backend/config/templates.py` — Three hardcoded JD templates as TypedDict list
- `backend/api/routes/jd.py` — Six JD API endpoints with Pydantic schemas and status state machine

## Files Modified
- `backend/db/migrations/env.py` — Added JD model import for autogenerate detection
- `api/server.py` — Added `jd_router` import and `app.include_router(jd_router)`

## Decisions Made

- **Date filtering uses string comparison for SQLite compatibility** — SQLite's `CAST(..., DATE)` does not correctly extract the date portion from datetime strings. Changed to direct string comparison (`column >= date_from`, `column <= "date_to 23:59:59"`), which works because SQLite datetime columns store ISO-formatted text and lexicographic comparison is correct for ISO format.

- **Title validation via Pydantic field_validator** — Added `@field_validator("title")` to `JDSchema` to reject empty/whitespace-only titles with a Chinese error message, returning 422. This matches the test expectation and prevents blank-title JDs.

- **Status transition as dict lookup** — Rather than a full state machine library, transitions are enforced via a simple dict: `{DRAFT: [ACTIVE], ACTIVE: [CLOSED], CLOSED: [ACTIVE]}`. Invalid transitions return 400 with descriptive message.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added title validation to JDSchema**
- **Found during:** Task 1 verification (test_create_jd_validation failed)
- **Issue:** JDSchema defined `title: str` with no constraints. Sending `{"title": "", "department": "技术部"}` returned HTTP 201 instead of 422, because an empty string is a valid `str`.
- **Fix:** Added `@field_validator("title")` that rejects empty/whitespace-only strings with `raise ValueError("职位名称不能为空")`
- **Files modified:** `backend/api/routes/jd.py`
- **Verification:** `test_create_jd_validation` now passes (returns 422)
- **Committed in:** `9104a41` (fix commit)

**2. [Rule 1 - Bug] Fixed SQLite date filter incompatibility**
- **Found during:** Task 3 verification (test_list_jds_date_filter failed)
- **Issue:** `cast(JD.updated_at, Date)` uses SQLite `CAST()` which treats `DATE` as NUMERIC affinity and does not correctly extract the date portion from `YYYY-MM-DD HH:MM:SS.xxxxxx` datetime strings.
- **Fix:** Replaced `cast(column, Date)` with direct string comparison: `JD.updated_at >= date_from` and `JD.updated_at <= f"{date_to} 23:59:59"`
- **Files modified:** `backend/api/routes/jd.py`
- **Verification:** `test_list_jds_date_filter` now passes (13/14 tests passed after this fix)
- **Committed in:** `9104a41` (fix commit)

**3. [Rule 1 - Bug] Fixed timezone mismatch in date filter test**
- **Found during:** Same Task 3 verification (the test used local TZ instead of UTC)
- **Issue:** Test used `datetime.date.today()` which returns local date (CST, UTC+8). `func.now()` in SQLite returns UTC datetime. When timezone offset crosses date boundary, the test date doesn't match the stored UTC date.
- **Fix:** Changed to `datetime.now(timezone.utc).date().isoformat()` and moved `from datetime import datetime, timezone` to module level
- **Files modified:** `tests/test_jd.py`
- **Verification:** `test_list_jds_date_filter` passes with UTC-aligned date
- **Committed in:** `9104a41` (fix commit)

**4. [Rule 1 - Bug] Fixed keyword search test data collision**
- **Found during:** Task 3 verification (test_list_jds_search_keyword failed)
- **Issue:** Both "Python工程师" and "Java工程师" JDs used `SAMPLE_JD` defaults which include `skills: "Python, FastAPI, SQL"`. Searching for "Python" matched both because the skills field contained "Python".
- **Fix:** Gave the "Java工程师" JD distinct skills via `skills="Java, Spring, MySQL"`
- **Files modified:** `tests/test_jd.py`
- **Verification:** Keyword search now correctly returns only 1 result
- **Committed in:** `9104a41` (fix commit)

---

**Total deviations:** 4 auto-fixed (2 Rule 1 bugs, 1 Rule 2 missing critical, 1 test data)
**Impact on plan:** All fixes essential for correctness and security. No scope creep.

## Issues Encountered

- **SQLite DATE CAST incompatibility** — Initially used `cast(JD.updated_at, Date)` following the plan, but SQLite's `CAST` doesn't properly handle datetime-to-date extraction like PostgreSQL does. Resolved by switching to direct string comparison.
- **Timezone boundary issue** — `func.now()` in SQLite returns UTC time, but `datetime.date.today()` returns local time. Resolved in test by aligning to UTC.

## Stub Tracking

No stubs found. All endpoints return real data from the database or hardcoded templates.

## Threat Surface Scan

No new threat surface identified beyond the plan's `<threat_model>`. All endpoints are protected by `Depends(get_current_user)`. Status transitions are enforced server-side. Pydantic validation prevents mass assignment (T-JD-01). SQLAlchemy ORM provides parameterized queries (T-JD-02). Page size is limited to 100 (T-JD-04).

## Known Stubs

None.

## Threat Flags

No new threat flags. All implemented surface is covered by the plan's threat register (T-JD-01 through T-JD-05).

## Next Phase Readiness

- JD data model and API are complete and tested (14/14 tests passing)
- Ready for Phase 2 Plan 02 (JD management frontend UI)
- Alembic migration is at head, ready for Phase 3 (resume management) to add new tables
- The 6 JD endpoints provide a stable contract for frontend consumption

---

*Phase: 02-jd-management*
*Completed: 2026-04-26*
