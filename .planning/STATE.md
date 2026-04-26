# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-26)

**Core value:** HR can quickly and accurately find matching candidates; AI assists but human approves
**Current focus:** Phase 3 -- Resume & Candidate Management

## Current Position

Phase: 3 of 5 (Resume & Candidate Management)
Plan: 0 of TBD in current phase
Status: Context gathered -- ready for planning
Last activity: 2026-04-26 -- Phase 3 context discussion completed

Progress: [████████░░░░] 80%

## Performance Metrics

**Velocity:**
- Total plans completed: 10
- Average duration: 6.4 min
- Total execution time: 64.2 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 6 | 32.0 min | 5.3 min |
| 2. JD Management | 4 | 32.2 min | 8.1 min |
| 3. Resume Management | TBD | - | - |
| 4. AI Matching & Approval | TBD | - | - |
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
- Plan 01-05: SSE timeout set to 120 seconds as a hardcoded constant (TIMEOUT_SECONDS), not configurable via env var for Phase 1
- Plan 01-05: SqliteSaver reuses the same data/dev.db file as application tables (D-09); tables coexist in SQLite namespaces
- Plan 01-05: HITL session UUIDs generated with `uuid4().hex` (shorter hex string vs full UUID with dashes)
- Plan 01-06: Use file-based temp SQLite for test isolation (not :memory:) so test data is shared across sessions
- Plan 01-06: Use FastAPI app.dependency_overrides to inject test DB engine (not module patching)
- Plan 02-01: JD EducationLevel enum with Chinese values (高中, 大专, 本科, 硕士, 博士, 不限)
- Plan 02-02: shadcn v4 form component manually created (base-nova registry has empty form entry; radix-ui/react-label and react-slot peer deps installed manually)
- Plan 02-02: useJDs hook uses `placeholderData: keepPreviousData` (imported function, v5 API) not boolean (v4 API)
- Plan 02-01: JDStatus three-state lifecycle: draft -> active -> closed -> active
- Plan 02-01: JD status transitions enforced via dict lookup (not state machine library)
- Plan 02-01: Date filtering uses direct string comparison instead of cast(..., Date) for SQLite compatibility
- Plan 02-01: Title validation via Pydantic field_validator (min_length=1)
- Plan 02-01: 3 hardcoded templates stored in backend/config/templates.py (software-engineer, product-manager, sales-manager)
- Plan 02-04: JDForm uses locally inferred FormValues type from Zod schema (not importing JDFormValues from types/jd.ts) to avoid type drift
- Plan 02-04: Create flow: Dialog -> template selection -> form. Edit flow: Dialog -> form directly.
- Plan 02-04: Error display uses inline state-based banner (submitError) rather than sonner toast library

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-04-26
Stopped at: Phase 3 context gathered
Resume file: .planning/phases/03-resume-candidate-management/03-CONTEXT.md
