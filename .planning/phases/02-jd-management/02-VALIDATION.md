---
phase: 2
slug: jd-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-26
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 + pytest-asyncio 1.3.0 |
| **Config file** | `pytest.ini` (from Phase 1) |
| **Quick run command** | `python -m pytest tests/ -x -q -k "jd"` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** `python -m pytest tests/ -x -q -k "jd"`
- **After every plan wave:** `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|----------|-----------|-------------------|-------------|--------|
| *TBD by planner* | 01 | 1 | JD-01 | Create JD with valid fields returns 200 + JD object | integration | `pytest tests/test_jd.py::test_create_jd_success -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 01 | 1 | JD-01 | Create JD with missing required fields returns 422 | integration | `pytest tests/test_jd.py::test_create_jd_validation -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 01 | 1 | JD-01 | Create JD without auth returns 401 | integration | `pytest tests/test_jd.py::test_create_jd_unauthorized -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 01 | 1 | JD-02 | Edit JD updates fields correctly | integration | `pytest tests/test_jd.py::test_update_jd -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 01 | 1 | JD-02 | Close JD changes status to closed | integration | `pytest tests/test_jd.py::test_close_jd -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 01 | 1 | JD-02 | Reactivate closed JD changes status back to active | integration | `pytest tests/test_jd.py::test_reactivate_jd -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 01 | 1 | JD-02 | Invalid status transition returns 400 | integration | `pytest tests/test_jd.py::test_invalid_status_transition -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 02 | 1 | JD-03 | List JDs returns paginated results | integration | `pytest tests/test_jd.py::test_list_jds_pagination -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 02 | 1 | JD-03 | Filter JDs by status returns filtered results | integration | `pytest tests/test_jd.py::test_list_jds_filter_status -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 02 | 1 | JD-03 | Search JDs by keyword returns matching results | integration | `pytest tests/test_jd.py::test_list_jds_search_keyword -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 02 | 1 | JD-03 | Empty filter returns all JDs paginated | integration | `pytest tests/test_jd.py::test_list_jds_no_filters -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 01 | 1 | JD-04 | GET /jd/templates returns list of presets | integration | `pytest tests/test_jd.py::test_list_templates -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_jd.py` — JD CRUD + filter + template tests (use existing conftest.py from Phase 1)
- [ ] No new conftest needed — Phase 1 already provides `test_client`, `test_session`, `db_path` fixtures

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| shadcn Table renders with server data in browser | JD-03 | Browser rendering not suited to unit tests | Start dev server, verify `/jd` page shows table with data |
| JD form validation shows field-level errors | JD-01 | Visual UX validation | Open create dialog, submit empty form, verify error messages appear |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
