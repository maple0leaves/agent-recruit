# Roadmap: hellojobs — AI Recruitment System

## Overview

hellojobs is an AI-assisted, human-judged recruitment matching system. It starts as a backend-only prototype with multi-agent LangGraph orchestration and becomes a full-stack product with a React SPA frontend, role-based auth, JD and resume management, real-time AI matching with SSE streaming, approval workflows, and reporting. Backend stability is hardened before any frontend work begins. The build is organized into 5 phases: Foundation, JD Management, Resume Management, Matching & Approval, and Advanced Features.

## Phases

- [x] **Phase 1: Backend Foundation & Authentication** - Secure backend with auth, relational DB, and frontend scaffold
- [ ] **Phase 2: JD Management** - Full CRUD for job descriptions with templates and search
- [ ] **Phase 3: Resume & Candidate Management** - Resume upload, parsing, candidate search, and status tracking
- [ ] **Phase 4: AI Matching & Approval** - Core matching loop with SSE streaming, results display, and approve/reject
- [ ] **Phase 5: Advanced Features & Export** - Bi-directional matching, agent feedback, and PDF/Excel export

## Phase Details

### Phase 1: Backend Foundation & Authentication
**Goal**: HR can securely access the system with role-based access. Backend is stable and secure for all downstream development.
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03
**Success Criteria** (what must be TRUE):
  1. HR can log in with username and password from a dedicated login page
  2. HR stays logged in across page refreshes (session persists via HTTP-only cookies)
  3. System distinguishes between admin, recruiter, and hiring manager roles on protected pages
  4. HR can log out from any page; session is fully terminated
  5. Backend API endpoints return 401 for unauthenticated requests; SSE streaming handles timeouts and disconnects gracefully
**Plans**: 6 plans across 3 waves
**UI hint**: yes

Plans:
- [x] 01-01-PLAN.md — Test infrastructure (conftest.py, test skeletons, pytest deps)
- [x] 01-02-PLAN.md — Backend auth core (DB engine, User model, bcrypt/JWT, auth routes, CORS, Alembic, seed script)
- [x] 01-03-PLAN.md — Frontend scaffold (Vite init, Tailwind v4, shadcn/ui, router, api client, auth store+hook)
- [x] 01-04-PLAN.md — Frontend pages (Login page with all states, ProtectedRoute, Layout sidebar, placeholder pages)
- [x] 01-05-PLAN.md — Backend hardening (auth middleware, async conversion, SSE timeout/disconnect, SqliteSaver, UUID thread_id)
- [x] 01-06-PLAN.md — Integration (frontend build wiring, test suite verification, seed admin user)

### Phase 2: JD Management
**Goal**: HR can create, manage, and use templates for job descriptions.
**Depends on**: Phase 1
**Requirements**: JD-01, JD-02, JD-03, JD-04
**Success Criteria** (what must be TRUE):
  1. HR can create a new JD with all structured fields (title, department, skills, experience, salary range)
  2. HR can view a paginated list of JDs with search and filter by department, status, and date
  3. HR can edit any JD field and close (deactivate) a JD
  4. HR can create a new JD from a pre-defined template, pre-populating common fields
**Plans**: TBD
**UI hint**: yes

### Phase 3: Resume & Candidate Management
**Goal**: HR can upload resumes, view parsed candidate data, and track candidates through the pipeline.
**Depends on**: Phase 1
**Requirements**: RES-01, RES-02, RES-03, RES-04, RES-05
**Success Criteria** (what must be TRUE):
  1. HR can upload a PDF or Word resume file and see it accepted with extraction preview
  2. System automatically extracts structured data (name, skills, education, experience) from the resume
  3. HR can view a candidate detail page showing parsed data, match history, and current pipeline status
  4. HR can search the candidate database by name, skill, and pipeline status
  5. HR can update a candidate's pipeline status: New, Screening, Interview, Hired, Rejected
**Plans**: TBD
**UI hint**: yes

### Phase 4: AI Matching & Approval
**Goal**: HR can run AI matching against a JD, see real-time results, and approve or reject candidates.
**Depends on**: Phase 2, Phase 3
**Requirements**: MATCH-01, MATCH-02, MATCH-03, APRV-01, APRV-02, DASH-01
**Success Criteria** (what must be TRUE):
  1. HR can select a JD and trigger AI matching; ranked candidates with match scores are displayed
  2. For each matched candidate, HR sees a skill-by-skill comparison with matched and missing skills highlighted
  3. HR can watch the agent's matching progress in real-time via a streaming pipeline visualization
  4. HR can approve or reject each matched candidate with optional notes
  5. HR sees a dashboard showing active JD count, total candidates, and pending approvals count
**Plans**: TBD
**UI hint**: yes

### Phase 5: Advanced Features & Export
**Goal**: HR can find JDs for a candidate, send feedback to the agent, and export matching reports.
**Depends on**: Phase 4
**Requirements**: MATCH-04, APRV-03, DASH-02
**Success Criteria** (what must be TRUE):
  1. HR can select a candidate and find which existing JDs they match best (reverse matching)
  2. HR can send feedback to the agent during review and request re-adjustment of results
  3. HR can export matching results as a formatted PDF report
  4. HR can export matching results as an Excel spreadsheet
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2/3 (parallel-capable) -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Foundation & Authentication | 6/6 | Complete | 2026-04-26 |
| 2. JD Management | 0/TBD | Not started | - |
| 3. Resume & Candidate Management | 0/TBD | Not started | - |
| 4. AI Matching & Approval | 0/TBD | Not started | - |
| 5. Advanced Features & Export | 0/TBD | Not started | - |
