# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-26)

**Core value:** HR can quickly and accurately find matching candidates; AI assists but human approves
**Current focus:** Phase 1 -- Backend Foundation & Authentication

## Current Position

Phase: 1 of 5 (Backend Foundation & Authentication)
Plan: 4 of 6 (next: 01-04-PLAN.md)
Status: Completed -- Plan 01-03 done
Last activity: 2026-04-27 -- Plan 01-03 frontend scaffold completed

Progress: [████████░░] 50%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 5.8 min
- Total execution time: 17.5 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 6 | 17.5 min | 5.8 min |
| 2. JD Management | TBD | - | - |
| 3. Resume Management | TBD | - | - |
| 4. Matching & Approval | TBD | - | - |
| 5. Advanced Features | TBD | - | - |

*Updated after each plan completion*

## Accumulated Context

### Decisions

- Roadmap: 5 phases, backend-first ordering. Phase 1 must be complete before any frontend feature work begins.
- Phases 2 (JD) and 3 (Resume) can be built in parallel after Phase 1.
- Plan 01-01: Added pytest.ini with asyncio_mode=auto because pytest-asyncio 1.x defaults to Mode.STRICT and would not run the async test skeletons.
- Plan 01-02: Use direct bcrypt instead of passlib (passlib 1.7.4 incompatible with bcrypt 5.0.0)
- Plan 01-02: Alembic uses sync sqlite:// URL while app uses async sqlite+aiosqlite://
- Plan 01-02: Access token 30-min expiry; Refresh token 7-day expiry in HttpOnly cookie
- Plan 01-02: UserRole as str enum with lowercase values (admin, recruiter, hiring-manager)
- Plan 01-02: CORS restricted to explicit origins with credentials=True
- Plan 01-03: shadcn/ui v4 (base-nova style) used instead of classic presets; all components installed cleanly
- Plan 01-03: BrowserRouter placed in main.tsx (standard React pattern), not in App.tsx
- Plan 01-03: Vite build outputs to ../static/ for direct FastAPI serving (D-14)
- Plan 01-03: zustand explicitly installed (not listed in plan dependencies but required by authStore)
- Plan 01-03: static/ added to .gitignore as build artifact output

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-04-27
Stopped at: Plan 01-03 complete (frontend scaffold)
Resume file: .planning/phases/01-backend-foundation-auth/01-03-SUMMARY.md
