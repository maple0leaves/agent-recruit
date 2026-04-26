# Project Research Summary

**Project:** hellojobs — AI-Powered Recruitment System
**Domain:** Full-stack AI recruitment agent productized into an HR dashboard
**Researched:** 2026-04-26
**Confidence:** HIGH across all research areas (stack verified against registries, features cross-referenced with 10+ competitors, architecture validated against codebase analysis, pitfalls audited against existing code)

## Executive Summary

hellojobs is an AI-assisted, human-judged recruitment matching system. It consists of an existing multi-agent LangGraph backend (agent pipeline, FAISS vector index, ChromaDB candidate memory, SSE streaming) and a new React SPA frontend that gives HR teams a full dashboard. The core value proposition is transparent AI matching: unlike black-box ATS products (Moka, Beisen, Manatal), hellojobs shows step-by-step agent reasoning with explainable match scores and an interrupt-based human-in-the-loop (HITL) review flow.

The recommended approach is a 5-phase build: (1) Backend Foundation -- auth, relational DB, and critical security hardening before any frontend work; (2) Core Data Management -- JD creation and resume upload, the two content pillars matching depends on; (3) Matching and Streaming -- the core product loop where HR creates a JD, runs AI matching via SSE, and approves/rejects candidates; (4) Advanced Features -- explainable scores, HITL review, conversational AI inbox, skills gap analysis, and export; (5) Production Hardening -- email integration, persistent checkpoints, deployment config, and the remaining P3 features.

The key risk is building frontend polish before backend stability. The backend has critical issues (InMemorySaver losing state on restart, no auth, no input validation, SSE without timeout/sentinel, sync blocking in async handlers) that must be fixed before Phase 2. The second major risk is PII exposure: candidate data flows to the LLM without redaction, and there is no schema-level separation between PII and evaluation data. Both risks are well-understood and have clear mitigations documented in the pitfalls research.

## Key Findings

### Recommended Stack

**Frontend (React SPA + Vite):** The stack is a standard 2026 production dashboard toolkit. React 19 with Vite 8 provides fast HMR and concurrent rendering for SSE token streams without blocking the UI. Tailwind CSS 4 with shadcn/ui gives zero-runtime, tree-shakeable styling with full component ownership (no version lock-in). TanStack Query 5 eliminates manual API state management with caching, dedup, and background refetch. Zustand 5 handles the minimal client-side state at ~3KB gzipped. React Hook Form + Zod provides type-safe, performant forms. TanStack Table 8 delivers headless data tables for candidate lists and match results.

**Backend additions (Python):** PyJWT + passlib[bcrypt] for auth (with HTTP-only cookies, never localStorage). ReportLab for server-side PDF report generation (handles CJK fonts properly, unlike client-side react-pdf). openpyxl for Excel exports. slowapi for rate limiting. python-multipart for file uploads.

**SSE streaming layer:** No library needed for consumption -- native `fetch + ReadableStream` with `AbortController` handles POST-based SSE streaming. The backend already produces correct SSE events; the frontend only needs a thin custom hook. `@microsoft/fetch-event-source` is the recommended alternative if auto-reconnect on POST SSE is desired.

**Key exclusions:** No Next.js (SSR is unnecessary for an internal auth-gated tool). No Redux (Zustand + TanStack Query covers all state management). No Material UI (too heavy at 100-200KB gzipped, CSS-in-JS overhead). No localStorage for tokens (XSS-vulnerable). No EventSource (does not support POST, which the SSE endpoint requires).

### Expected Features

**Must have (P1, initial full-stack release -- validates core loop):**
- User Authentication and Roles (JWT with admin/recruiter/hiring-manager roles)
- JD Creation and Editing (structured fields with rich text editor)
- Resume Upload and Parsing (PDF/DOCX upload, LLM-based extraction)
- Candidate Detail View (parsed resume, tags, notes, match scores)
- AI Matching Results Display (ranked candidates with scores, triggerable from UI)
- Match Approval (Pass/Reject with optional feedback)
- Basic Dashboard (active JDs, pending reviews, recent candidates)
- Candidate Status Tracking (pipeline status per candidate-per-JD)

Core loop: JD created -> AI matching -> ranked results -> HR approves/rejects

**Should have (P2, add when core interaction is stable):**
- Explanatory Match Scores (skill-by-skill breakdown with evidence snippets from resume)
- HITL Review Flow (agent pauses before finalizing, HR gives feedback, agent revises)
- Conversational AI Inbox (natural language chat interface to the agent)
- Skills Gap Analysis (matched vs missing skills matrix per candidate)
- Export Results (PDF and Excel report generation)
- JD Template Library (reusable structured templates)
- Bidirectional Matching (find JDs for a candidate)

**Defer (P3/v2+):** JD Approval Workflow, Department-Facing Hiring Portal, Candidate-JD Score Explorer, AI-Suggested Interview Questions, Reporting and Analytics Dashboard, Candidate Re-engagement.

**Will not build (anti-features):** Full automation of candidate rejection (compliance risk), multi-board JD posting (low strategic value), built-in video interviewing (commodity, many better tools), employee onboarding (scope creep), full HRIS integration (infinite surface), candidate self-service portal (doubles attack surface), auto-scheduling interviews (low ROI), collaboration chat (solved by WeCom/DingTalk/Feishu), custom report builder (shipping 5-10 pre-built reports instead), multi-tenant infrastructure (single-tenant per PROJECT.md).

### Architecture Approach

The system follows a standard FastAPI + SPA architecture with SSE streaming bridging the agent backend to the frontend. The frontend is a React SPA built with Vite; the backend extends the existing FastAPI server with new modules for auth, relational database, API schemas, and file storage. The key architectural pattern is OpenAPI contract-first development: FastAPI auto-generates an OpenAPI spec from Pydantic models, and a codegen tool produces TypeScript types and typed fetch clients, eliminating an entire class of API mismatch bugs.

**Major components:**
1. **React SPA (frontend/)** -- HR user interface: JD management, matching dashboard, HITL review, file upload, admin settings. Communicates with backend via REST + SSE. State managed by TanStack Query (server data) + Zustand (client/auth state).
2. **FastAPI Server (backend/api/)** -- REST endpoints for CRUD operations, auth middleware with JWT validation (hybrid bearer + cookie for SSE), SSE streaming endpoint for agent progress. Route handlers are thin wrappers around service layer calls.
3. **Relational Database (backend/db/)** -- New module with SQLAlchemy async ORM models, Alembic migrations, and repository pattern. SQLite for dev, PostgreSQL for prod. Models: users, job_descriptions, candidates, match_sessions, match_results, uploaded_files.
4. **Existing Agent Engine (backend/agent/ + rag/)** -- LangGraph multi-agent workflow, FAISS vector index, ChromaDB memory store. No structural changes needed. The SSE endpoint already bridges agent streaming to the frontend.
5. **File Storage (backend/storage/)** -- Abstract FileStorage interface with local filesystem implementation. S3 implementation deferred. Uploads trigger background FAISS rebuild via FastAPI BackgroundTasks.

### Critical Pitfalls

1. **SSE streaming without timeout, sentinel, or disconnect handling** -- The existing SSE endpoint has no timeout, no `[DONE]` sentinel on error paths, and no client disconnect detection. Mitigation: add 120s hard timeout, yield `[DONE]` on every terminal path, detect client disconnect via `request.is_disconnected()`, and never send HTTP errors mid-stream. **Address in Phase 1.**

2. **InMemorySaver for HITL state (all lost on restart)** -- `main.py:70` uses InMemorySaver(), and `thread_id` is hardcoded to `"hitl-thread"`. Two concurrent users overwrite each other; a server restart loses all pending approvals. Mitigation: replace with SqliteSaver, generate UUID per session, add GET endpoint to list pending HITL threads. **Address in Phase 1.**

3. **DIY JWT authentication with localStorage (data breach)** -- No auth on any API endpoint now. The common but dangerous next step is localStorage-based JWT, which is XSS-vulnerable (McHire breach: 64M applicant records). Mitigation: use HTTP-only Secure SameSite=Strict cookies, short access token lifetimes (15 min), refresh token rotation, and CSP headers. **Address in Phase 1.**

4. **No PII boundary between candidate data and LLM inference** -- Full resumes (name, phone, email, address) are sent to the LLM without redaction. In regulated contexts this is a GDPR/CCPA violation risk. Mitigation: implement a PII redaction layer (spaCy NER) before prompt construction, split candidate storage into evaluation tier (anonymized) and PII tier (encrypted, separately stored). **Address in Phase 2 (schema design) and Phase 3 (redaction pipeline).**

5. **Boolean flag explosion for AI streaming state on frontend** -- Using individual `useState` booleans (isLoading, isStreaming, isComplete, error) creates impossible states and race conditions. Mitigation: use a state machine with discriminated union (idle | connecting | streaming | complete | error), guaranteed transitions via try/finally, AbortController for cancellation, and token batching. **Address in Phase 2 (frontend foundation).**

6. **Over-engineering the frontend before the backend is stable** -- The most dangerous project management pitfall. Polished UI while backend has InMemorySaver, no auth, no input validation, and print-based logging leads to frontend rewrites. Mitigation: strict phase ordering with a backend stability checklist that must pass before Phase 2 starts. **Address in Phase ordering/roadmap.**

## Implications for Roadmap

Based on combined research, the following 5-phase structure is recommended. Phases are ordered by dependency: backend stability precedes frontend, data management precedes matching, and core features precede advanced enhancements.

### Phase 1: Backend Foundation (Critical)

**Rationale:** Every feature depends on auth and database. Multiple critical pitfalls (SSE timeout, InMemorySaver, JWT in localStorage, FAISS deserialization, sync blocking, no input validation, no file upload limits) must be fixed before any frontend work. This phase addresses the top 10 critical and moderate pitfalls simultaneously.

**Delivers:** A secure, stable backend that frontend development can depend on. Auth working, database operational, SSE streaming hardened, API endpoints secured.

**Addresses features:** User Authentication and Roles (P1).

**Avoids pitfalls:** Pitfall 1 (SSE timeout/sentinel), Pitfall 2 (InMemorySaver -> SqliteSaver), Pitfall 3 (JWT in localStorage -> HttpOnly cookies), Pitfall 6 (hardcoded thread ID -> UUID), Pitfall 7 (FAISS deserialization -> HMAC signing), Pitfall 8 (sync blocking -> async def), Pitfall 9 (LLM injection -> input validation), Pitfall 11 (file upload -> size/MIME limits).

**Stack additions:** PyJWT, passlib[bcrypt], python-multipart, slowapi (backend). Zustand + React Query + React Router (frontend scaffold).

**Architecture additions:** backend/db/ (SQLAlchemy models, migrations), backend/auth/ (JWT, password hashing, middleware), backend/schemas/ (Pydantic API schemas), backend/storage/ (file abstraction). Frontend scaffold (Vite + React + Tailwind + shadcn/ui).

**Architecture anti-patterns to fix:** Convert sync `def` handlers to `async def` with `asyncio.to_thread()` for agent work. Add SSE timeout and `[DONE]` sentinel. Replace InMemorySaver with SqliteSaver. Generate UUID per HITL session. HMAC-sign FAISS index.

**Research flag:** MEDIUM confidence on hybrid auth pattern (bearer + cookie for SSE). This is a documented but niche pattern. Needs verification during implementation that auth middleware handles both paths correctly without complexity.

### Phase 2: Core Data Management

**Rationale:** JD and resume management are the two content pillars. AI matching cannot produce results without source data. These features have no dependency on the matching/streaming code from Phase 3, so they can be built in parallel or immediately after Phase 1.

**Delivers:** Full CRUD for job descriptions and resume upload with parsing. The candidate database populated with structured data.

**Addresses features:** JD Creation and Editing (P1), Resume Upload and Parsing (P1), Candidate Detail View (P1), JD Template Library (P2 -- if time allows).

**Avoids pitfalls:** Pitfall 12 (PII not separated in schema -- this phase implements the two-tier data architecture). Pitfall 4 (PII boundary) -- schema separation starts here, full redaction pipeline in Phase 3.

**Stack additions:** Zod schemas (mirroring Pydantic models for type safety), React Hook Form (JD editor form), shadcn/ui form components.

**Architecture additions:** JD CRUD endpoints + UI, upload endpoint + UI, candidate record management. Repository pattern for DB access. Background task for FAISS rebuild on upload.

**Key decision:** Start with SQLite for development (Schema is simple, SQLAlchemy async makes PostgreSQL migration trivial). Do NOT skip the relational DB -- FAISS+ChromaDB cannot model JD management, user accounts, or audit trails.

### Phase 3: Matching and Streaming (Core Loop)

**Rationale:** The core product loop that validates the value proposition. A JD exists, candidates exist -- now run the agent pipeline and show results. This phase delivers the primary user-facing feature.

**Delivers:** HR can create a JD, trigger AI matching, watch agent progress via SSE in real-time, see ranked candidate results, and approve/reject candidates.

**Addresses features:** AI Matching Results Display (P1), Match Approval (P1), Basic Dashboard (P1), Candidate Status Tracking (P1).

**Avoids pitfalls:** Pitfall 5 (boolean flag explosion -- use state machine pattern from Phase 1 planning). Pitfall 10 (mock email tools -- email integration is Phase 5, not touched here).

**Stack additions:** TanStack Table (candidate results table), shadcn/ui table/dialog components, @microsoft/fetch-event-source (if auto-reconnect needed) or native fetch ReadableStream.

**Architecture additions:** Real SSE consumption replacing fake timer simulation. Pipeline visualization component showing agent progress. Candidate card rendering from SSE result events. Match result persistence in relational DB. Match approval (pass/reject) UI.

**Research flag:** HIGH confidence on SSE streaming pattern -- backend already produces correct events, frontend consumption pattern is well-documented. No additional research needed beyond implementation.

### Phase 4: Advanced Matching and HITL

**Rationale:** Features that enhance the core matching loop but depend on stable matching infrastructure from Phase 3. HITL review, explanatory scores, and skills gap analysis turn matching from a black box into a transparent, collaborative process.

**Delivers:** HR sees skill-by-skill breakdown, interacts with the agent conversationally, engages in HITL review with feedback, and exports results.

**Addresses features:** Explanatory Match Scores (P2), HITL Review Flow (P2), Conversational AI Inbox (P2), Skills Gap Analysis (P2), Export Results (P2), Bidirectional Matching (P2).

**Stack additions:** ReportLab (PDF), openpyxl (Excel), charts library for skills visualization (radar charts, skill bars).

**Architecture additions:** HITL review UI (approval card with candidate context, feedback form, resume from interruption). Conversational AI Inbox (chat-like interface, streaming text, action suggestions). Skills gap matrix visualization. Export endpoints (server-side PDF/Excel generation).

**Research flag:** LOW-MEDIUM confidence on HITL review UX pattern. The interrupt-based flow (agent pauses, HR gives feedback, agent revises) is novel -- no competitor implements this. The frontend UX for interruption needs custom design thinking. Recommend `/gsd-research-phase` during Phase 4 planning to validate the interaction design against real HR users.

### Phase 5: Production Hardening

**Rationale:** Transition from working prototype to deployable system. Real email, production-grade checkpoints, deployment config, and the remaining P3 features.

**Delivers:** A system ready for real HR teams to use. Email notifications work, HITL state survives deployments, system is containerized and deployable.

**Addresses features:** JD Approval Workflow (P3), Department-Facing Hiring Portal (P3), remaining anti-features avoidance.

**Avoids pitfalls:** Pitfall 10 (mock email tools -- replace with real email backend with SMTP/SendGrid integration). Pitfall 2 (InMemorySaver already replaced in Phase 1, now upgrade to PostgresSaver for production).

**Stack additions:** Docker Compose (production deployment), PostgreSQL migration, email integration (SMTP or SendGrid), rate limiting for production.

**Deferred to v2+:** Candidate-JD Score Explorer (novel visualization, wait for user demand), AI-Suggested Interview Questions (requires mature gap analysis), Reporting and Analytics Dashboard (needs baseline data from real usage), Candidate Re-engagement/Talent Pool (needs critical mass of candidates).

**Research flag:** MEDIUM confidence on email integration in LangGraph. Mock email tools currently exist. The production pattern (EmailBackend abstraction, config toggle, forced HITL for outbound communication) needs implementation research during Phase 5 planning. Recommend `/gsd-research-phase`.

### Phase Ordering Rationale

- **Backend must precede frontend.** Multiple pitfalls (PITFALLS.md) and the architecture dependency graph (ARCHITECTURE.md) agree: auth, database, SSE hardening, and API contract stability are prerequisites for frontend development. Skipping this order means frontend rewrites when the API changes.
- **Data management precedes matching.** FEATURES.md dependency notes are explicit: "JD + Resume management are foundational. AI matching cannot produce results without source data." Phases 1-2 deliver the data pipeline before Phase 3 consumes it.
- **Core matching precedes advanced features.** Explanatory scores, HITL review, and conversational AI all depend on stable matching infrastructure. Building them in parallel increases risk of late-stage integration friction.
- **PII separation in Phase 2, not Phase 1.** The schema redesign is a larger effort that benefits from the auth/DB foundation in Phase 1. PITFALLS.md maps it to Phase 2, which aligns with the data management focus.

### Research Flags

Phases needing deeper research during planning:
- **Phase 4 (Advanced Matching/HITL):** The interrupt-based HITL review flow is novel. No competitor implements agent-pause-HR-feedback-agent-revises. Needs UX design research and validation with real HR users before implementation.
- **Phase 5 (Production Hardening):** Email integration in LangGraph is niche. The current mock tools need replacement with a proper EmailBackend abstraction. Needs research on the best integration pattern (SMTP vs SendGrid vs SES), template management, and forced-HITL for outbound communication.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Backend Foundation):** JWT auth with HttpOnly cookies, SQLAlchemy async + Alembic, SSE timeout/sentinel -- all well-documented, established patterns. Standard implementation.
- **Phase 2 (Core Data Management):** CRUD operations with FastAPI + SQLAlchemy + React Hook Form + TanStack Query -- standard full-stack pattern across thousands of production apps.
- **Phase 3 (Matching and Streaming):** SSE consumption via fetch ReadableStream, React component rendering from streamed events -- established pattern for LLM/agent interfaces.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Versions verified against npm registry and PyPI. Multiple corroborating sources on stack appropriateness. Alternatives considered and documented with rationale. |
| Features | HIGH | Cross-referenced against 10+ competitor products (Moka, Beisen, Manatal, Greenhouse, Lever, Workable, BambooHR, Bullhorn), market reports (G2, SHRM, LinkedIn), and anti-feature analysis (Lever.co, Tribepad, 4SpotConsulting). Clear P1/P2/P3 prioritization with explicit dependency mapping. |
| Architecture | HIGH | Verified against existing codebase analysis. Established patterns (OpenAPI contract-first, SSE bridging, JWT auth, repository pattern) are production-validated across thousands of deployments. Build order derived from concrete dependency graph. |
| Pitfalls | HIGH | 13 pitfalls identified with specific codebase references (file paths, line numbers). Cross-referenced against existing CONCERNS.md, LangGraph production guides, FastAPI docs, and industry incident reports (McHire breach). Each mapped to a prevention phase with verification criteria. |

**Overall confidence:** HIGH

### Gaps to Address

- **Chinese resume parsing accuracy.** FEATURES.md notes the existing LLM-based parsing needs verification for Chinese resumes. This is not a research gap (the parser exists) but needs testing with real Chinese resumes during Phase 2. Flag: add Chinese resume fixture suite to tests.

- **CJK font setup for ReportLab PDF generation.** STACK.md documents the font registration pattern (Noto Sans SC) but the actual font file must be bundled or downloaded. Implementation detail, requires no additional research. Flag: add font download step to setup documentation or Dockerfile in Phase 4.

- **FAISS incremental indexing for large corpora.** The current approach rebuilds the full FAISS index on each upload. For small HR teams (<1000 resumes) this is acceptable (<30s). The scaling research in ARCHITECTURE.md and PITFALLS.md flags this as a future concern. Flag: document the limit and revisit only when corpus exceeds 1000 resumes.

- **HITL review UX interaction design.** As noted in research flags, the novel interrupt-based HITL flow has no established UX pattern to follow. This is the highest-risk gap because it affects the core differentiator. Flag: requires `/gsd-research-phase` during Phase 4 planning with real HR user testing.

- **LangGraph checkpointer migration path.** SqliteSaver is the Phase 1 mitigation for InMemorySaver, but the long-term production choice (PostgresSaver vs DynamoDBSaver vs custom) depends on deployment environment. Flag: decide during Phase 5 planning based on whether PostgreSQL is chosen for production.

## Sources

### Primary (HIGH confidence)
- npm registry (confirmed versions: Zustand 5.0.12, TanStack Query 5.100.5, TanStack Table 8.21.3, React Hook Form 7.74.0, Zod 4.3.6, Vite 8.0.10, Tailwind 4.2.4, React Router 7.14.2)
- PyPI registry (confirmed versions: ReportLab 4.4.10, openpyxl 3.1.5, PyJWT 2.12.1, passlib 1.7.4, bcrypt 5.0.0, slowapi 0.1.9, python-multipart 0.0.26)
- Existing codebase analysis (`.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md`)
- LangGraph official documentation on checkpointing, persistence, and production pitfalls
- FastAPI official documentation on CORS, static files, streaming, and deployment

### Secondary (MEDIUM confidence)
- Dev.to: Zustand + TanStack Query state management pattern validation
- DesignRevision: Vite vs Next.js SPA/SSR decision framework (2026)
- Vintasoftware: OpenAPI codegen for FastAPI monorepos
- David Crimi: FastAPI JWT auth for SPAs with HttpOnly cookies
- Competitor analysis: Moka (mokahr.com), Beisen (beisen.com), Manatal (manatal.com), Greenhouse (greenhouse.io), Lever (lever.co), Workable (workable.com), BambooHR (bamboohr.com), Bullhorn (bullhorn.com)
- Market reports: G2 Spring 2025 ATS Grid Report, SHRM AI in Recruiting Report 2025, LinkedIn Global Talent Trends
- AWS Blog: Build durable AI agents with LangGraph and DynamoDB
- Diagrid: Take LangGraph to Production
- MojoAuth: Secure JWT Token Management in Browser Apps
- Duende Software: Best Practices Using JWTs
- ISACA: Avoiding AI Pitfalls in 2026

### Tertiary (LOW confidence, needs validation)
- Eightfold AI engineering blog (explainability patterns)
- MDPI research paper on explainable job hiring (Electronics 2025)
- CSDN comparison articles and Zhihu HR SaaS discussions (Chinese market analysis)
- C# Corner: State Management in React 2026 (single-source article)
- Dev.to: PDF Generation in Python FastAPI + DocuForge

---

*Research completed: 2026-04-26*
*Ready for roadmap: yes*
