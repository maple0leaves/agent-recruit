---
phase: 3
slug: resume-candidate-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-26
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `tests/conftest.py` (existing) |
| **Quick run command** | `python -m pytest tests/test_candidate.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~25 seconds |

## Sampling Rate

- **After every task commit:** `python -m pytest tests/test_candidate.py -x -q`
- **After every plan wave:** `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|----------|-----------|-------------------|-------------|--------|
| *TBD* | 01 | 1 | RES-01 | Upload valid PDF returns 201 | integration | `pytest tests/test_candidate.py::TestUpload::test_upload_pdf_success -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-01 | Upload valid .docx returns 201 | integration | `pytest tests/test_candidate.py::TestUpload::test_upload_docx_success -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-01 | File >10MB returns 400 | integration | `pytest tests/test_candidate.py::TestUpload::test_file_too_large -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-01 | Invalid format returns 400 | integration | `pytest tests/test_candidate.py::TestUpload::test_invalid_format -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-01 | Unauthenticated returns 401 | integration | `pytest tests/test_candidate.py::TestUpload::test_requires_auth -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-02 | Parse populates name/skills/education/experience | integration | `pytest tests/test_candidate.py::TestUpload::test_parse_success -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-02 | Parse failure returns 201 with warnings | integration | `pytest tests/test_candidate.py::TestUpload::test_parse_failure -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-03 | GET candidate by id | integration | `pytest tests/test_candidate.py::TestCRUD::test_get_candidate -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-03 | PUT update candidate fields | integration | `pytest tests/test_candidate.py::TestCRUD::test_update_candidate -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-04 | Search by name filters correctly | integration | `pytest tests/test_candidate.py::TestList::test_search_by_name -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-04 | Filter by status | integration | `pytest tests/test_candidate.py::TestList::test_filter_status -x` | ❌ W0 | ⬜ pending |
| *TBD* | 01 | 1 | RES-04 | Pagination works | integration | `pytest tests/test_candidate.py::TestList::test_pagination -x` | ❌ W0 | ⬜ pending |
| *TBD* | 02 | 1 | RES-05 | Valid status transition with note | integration | `pytest tests/test_candidate.py::TestStatus::test_valid_transition -x` | ❌ W0 | ⬜ pending |
| *TBD* | 02 | 1 | RES-05 | Terminal state irreversible | integration | `pytest tests/test_candidate.py::TestStatus::test_terminal_irreversible -x` | ❌ W0 | ⬜ pending |
| *TBD* | 02 | 1 | RES-05 | Missing note returns 422 | integration | `pytest tests/test_candidate.py::TestStatus::test_requires_note -x` | ❌ W0 | ⬜ pending |
| *TBD* | 02 | 1 | RES-05 | Invalid transition returns 400 | integration | `pytest tests/test_candidate.py::TestStatus::test_invalid_transition -x` | ❌ W0 | ⬜ pending |
| *TBD* | 02 | 1 | D-17 | DELETE returns 405 | integration | `pytest tests/test_candidate.py::TestLifecycle::test_no_delete -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

## Wave 0 Requirements

- [ ] `tests/test_candidate.py` — upload, CRUD, status, lifecycle tests (pattern follows test_jd.py)
- [ ] Test PDF fixture: minimal valid PDF for upload tests
- [ ] Test .docx fixture: minimal Word document for upload tests

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Upload progress spinner UI | RES-01 | Visual UX rendering | Upload a file, verify spinner + "正在智能解析简历..." message appears |
| Detail page 3-section scroll layout | RES-03 | Browser layout testing | Open candidate detail, verify 3 sections render correctly |

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
