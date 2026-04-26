---
phase: 1
slug: backend-foundation-auth
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-26
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio + httpx |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_auth.py -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| *TBD by planner* | 01 | 1 | AUTH-01 | T-1-01 | Login with valid credentials returns JWT in HTTP-only cookie | integration | `pytest tests/test_auth.py::test_login_success -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 01 | 1 | AUTH-01 | T-1-02 | Login with wrong password returns 401 | integration | `pytest tests/test_auth.py::test_login_wrong_password -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 02 | 1 | AUTH-02 | T-1-03 | Protected endpoint returns 403 for wrong role | integration | `pytest tests/test_auth.py::test_role_check -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 03 | 2 | AUTH-03 | T-1-04 | /auth/me returns user from cookie session | integration | `pytest tests/test_auth.py::test_session_persistence -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 03 | 2 | AUTH-03 | T-1-05 | Logout clears cookie and invalidates session | integration | `pytest tests/test_auth.py::test_logout -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 01 | 1 | AUTH-01/03 | T-1-06 | Unauthenticated request returns 401 | integration | `pytest tests/test_auth.py::test_unauthenticated -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 04 | 2 | D-09 | T-1-07 | SqliteSaver persists checkpoint across restart | integration | `pytest tests/test_checkpointer.py -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 05 | 3 | D-15 | T-1-08 | SSE endpoint sends [DONE] on timeout | integration | `pytest tests/test_sse.py::test_timeout_sentinel -x` | ❌ W0 | ⬜ pending |
| *TBD by planner* | 05 | 3 | D-15 | T-1-09 | SSE endpoint handles client disconnect | integration | `pytest tests/test_sse.py::test_disconnect -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_auth.py` — auth login/logout/role tests (AUTH-01, AUTH-02, AUTH-03)
- [ ] `tests/test_checkpointer.py` — SqliteSaver persistence test (D-09)
- [ ] `tests/test_sse.py` — SSE timeout and disconnect tests (D-15)
- [ ] `tests/conftest.py` — async test fixtures (test DB, test client)
- [ ] pytest install: `pip install pytest pytest-asyncio httpx`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tailwind v4 CSS build produces valid output | D-10 | Build tool output verification not suited to unit tests | `npx tailwindcss -i src/index.css -o /tmp/test.css` exits 0 |
| Vite build produces valid dist/ for FastAPI hosting | D-14 | Build artifact verification needs real build | `npm run build && test -f dist/index.html` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
