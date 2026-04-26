# Feature Landscape: AI-Powered Recruitment System (hellojobs)

**Domain:** AI recruitment / HR SaaS (enterprise HR-side, single-tenant)
**Researched:** 2026-04-26
**Confidence:** HIGH (based on cross-referenced research across 10+ competitors and market analysis)

## Feature Landscape

### Table Stakes (Users Expect These)

Features that users assume exist. Missing these = the product feels incomplete or non-credible.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **JD Creation & Editing** | HR needs to define hiring needs. Rich text editor, structured fields (title, department, location, skills, experience level, salary range). | LOW | Rich text can be lightweight (TipTap/Quill). Structured fields feed the AI matching pipeline. |
| **JD Template Library** | HR teams reuse common role templates. Saves time on repetitive roles. | LOW | Store as structured JSON templates. E.g., "Senior Python Engineer" template pre-populates skills, experience, salary band. |
| **JD Approval Workflow** | Hiring managers draft -> HR reviews -> Director approves. Needed for budget compliance. | MEDIUM | Multi-stage sequential approval with role-based routing. Requires user roles/permissions system. |
| **JD Search & Filter** | HR manages dozens of active JDs. Must search by title, department, status, date. | LOW | Full-text search + facet filters (department, status, creator, date range). |
| **Resume Upload (PDF/DOCX)** | Core input mechanism. HR uploads resumes from candidates. | MEDIUM | PDF parsing requires proper text extraction (PyMuPDF, python-docx). Must handle Chinese encoding. Already partially supported. |
| **Resume Parsing & Structuring** | Extracting name, phone, email, education, experience, skills from unstructured resumes. | MEDIUM | Existing LLM-based parsing works. Need to verify accuracy for Chinese resumes. |
| **Candidate Search** | Search across entire candidate database by name, skill, experience, status. | LOW | Full-text + vector search. ChromaDB already provides semantic search. Add keyword filters. |
| **Candidate Status Tracking** | Every candidate has a pipeline status (New, Screening, Interview, Offer, Hired, Rejected). | MEDIUM | Requires status management per candidate-per-JD. Kanban board view is industry standard. |
| **Candidate Detail View** | See full parsed resume, match scores, history, notes, tags in one place. | MEDIUM | Aggregated view combining ChromaDB memory + current match results. |
| **AI Matching Results Display** | Present ranked candidates with scores for a given JD. | MEDIUM | Already have match results from backend. Need UI to display scores, candidate details, and evidence. |
| **Match Approval (Pass/Reject)** | HR reviews AI-matched candidates and decides. Core HITL workflow already built. | LOW | Backend HITL interrupt already exists. Needs frontend approval UI. |
| **User Authentication & Roles** | HR users must log in. Different roles (HR admin, hiring manager, recruiter). | MEDIUM | Add JWT auth. Roles: admin, recruiter, hiring-manager. Protects API endpoints. |
| **Basic Dashboard** | HR managers expect a home screen showing open JDs, new candidates, recent matches. | MEDIUM | Aggregate counts (active JDs, total candidates, pending reviews). |
| **Export Results (PDF/Excel)** | HR needs to share matching results with hiring managers offline. | LOW | Server-side PDF generation (ReportLab/WeasyPrint) + Excel export (openpyxl). |

### Differentiators (Competitive Advantage)

Features that set hellojobs apart from existing ATS products (Moka, Beisen, etc.). These align with the project's core value: "AI-assisted but human-judged matching."

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Multi-Agent Workflow Transparency** | Unlike black-box AI matching, hellojobs shows the step-by-step reasoning pipeline (triage -> plan -> search -> score -> review). Builds trust in AI decisions. | MEDIUM | Frontend displays the agent chain as a visual progress timeline (already streamed via SSE). Each step shows what the agent did and found. |
| **Explainable Match Scores** | Not just a number -- show skill-by-skill breakdown, evidence snippets from resume, gap analysis. Critical for HR trust and compliance. | MEDIUM | Each MatchResult already has structured scores. Needs rich UI: radar/skill bars, highlighted resume excerpts, "matched" vs "missing" skills. |
| **Bidirectional Matching** | Both JD-to-candidates (find candidates for a role) AND candidate-to-JDs (find roles for a candidate). Existing AI can already do both. | MEDIUM | Backend agent supports both directions. UI needs separate entry points and result views. |
| **HITL (Human-in-the-Loop) Review Flow** | Agent pauses before finalizing, presents results for HR review, HR gives feedback, agent incorporates feedback. More collaborative than Moka/Beisen. | MEDIUM | Backend flow is built (interrupt_before=reviewer). Frontend needs: review page, feedback form, approve/reject with comments. |
| **Conversational AI Inbox** | HR can interact with the AI agent conversationally ("Find me senior Python devs with cloud experience"). More natural than form-based search. | HIGH | SSE streaming already supports this. Need a chat-like UI. Text input + streaming responses + action suggestions. |
| **Skills Gap Analysis Per Candidate** | AI highlights what skills a candidate is missing vs what they have -- helps HR make informed decisions about "close enough" candidates. | MEDIUM | MatchResult schema can surface gap analysis. UI shows skills matrix: matched skills (green), candidate has but not needed (blue), missing but needed (red). |
| **Candidate-JD Score Explorer** | Interactive dashboard where HR can see all candidates for a JD on a scatter plot (score vs experience vs education), drill into each. | HIGH | Novel UX. Helps HR quickly find "hidden gems" -- candidates with slightly lower scores but unique strengths. D3.js or ECharts visualization. |
| **AI-Suggested Interview Questions** | Based on gap analysis, generate targeted interview questions to probe the candidate's specific weaknesses/strengths. | MEDIUM | LLM-generated questions based on skill gaps. Simple text generation with prompt engineering. |
| **Department-Facing Hiring Portal** | Department heads can submit hiring requests, view matching progress, and approve/reject candidates without needing full HR system access. | HIGH | Separate view with limited scope. Department-only dashboard showing only their JDs and candidates. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems in practice. Deliberately do NOT build these.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Full Automation of Candidate Rejection** | "Save HR time by auto-rejecting low-scorers" | Destroys candidate experience. Compliance risk (bias in automated rejection). Misses "close enough" candidates who might be great for other roles. | Always require human review before rejection. AI can flag "low match" but never auto-reject. |
| **One-Click Multi-Board JD Posting** | "Post to 15 job boards from one UI" | Massive integration burden (15+ APIs). Low strategic value -- hellojobs is an internal matching engine, not a job board distributor. | Focus on internal candidate matching. If needed later, simple manual export + paste integration. |
| **Built-in Video Interviewing** | "End-to-end hiring platform" | Extremely complex (WebRTC, recording, storage, streaming). Commodity feature -- many better tools exist. Moka/Beisen don't build their own. | Integrate with existing tools (Tencent Meeting, Zoom). Share calendar link. |
| **Employee Onboarding Module** | "From candidate to employee in one system" | Scope creep. Onboarding is a completely different domain (IT provisioning, benefits enrollment, e-signatures). | Export hire data. Onboarding is out of scope per PROJECT.md. |
| **Full HRIS Integration** | "Sync with payroll, attendance, org charts" | Every company has different HRIS (SAP, Workday, Yonyou, Kingdee). Infinite integration surface. | Keep as standalone matching engine. Use CSV/API exports for data exchange. |
| **Candidate Self-Service Portal** | "Let candidates upload their own resumes and track status" | Doubles the surface area (candidate-facing UX, security, spam, abuse handling). Scope creep. | HR uploads resumes. Candidate facing is explicitly out of scope. |
| **AI Auto-Scheduling Interviews** | "Let AI negotiate time slots" | Incredibly complex (calendar sync, timezone handling, multi-participant, rescheduling). Low ROI for a matching-focused tool. | Manual scheduling. HR handles communication. |
| **Real-Time Collaboration Chat** | "Team can discuss candidates in-app" | Already solved by WeCom/DingTalk/Feishu. Building an in-app chat is enormous effort (WebSocket, presence, message history, notifications). | Link candidates in external chat. Use the existing ecosystem. |
| **Custom Report Builder** | "Let HR build any report they want" | Infinite UX complexity. Every report is a potential bug farm. Most HR teams use 3-5 standard reports. | Ship 5-10 pre-built reports. If custom needed, export CSV for Excel/PowerBI. |
| **Multi-Tenant SaaS Infrastructure** | "Sell to many companies" | Massive complexity: org isolation, per-tenant configs, billing, SLA management, data segregation, multi-region deployment. Per PROJECT.md: single-tenant. | Stay single-tenant. If pivot needed later, architect tenant isolation at that point. |

## Feature Dependencies

```
User Authentication & Roles
    └──requires──> User database + JWT implementation

JD Approval Workflow
    └──requires──> User Authentication & Roles (role-based routing)
    └──requires──> JD Creation & Editing (JDs must exist)

Candidate Status Tracking (Kanban)
    └──requires──> Resume Upload & Parsing
    └──requires──> JD Creation & Editing (candidate belongs to JD pipeline)

AI Matching Results Display
    └──requires──> JD Creation & Editing
    └──requires──> Resume Upload & Parsing
    └──enhances──> Candidate Status Tracking (scores feed into pipeline decisions)

HITL Review Flow
    └──requires──> AI Matching Results Display
    └──requires──> User Authentication & Roles (who approves)
    └──enhances──> Match Approval

Explanatory Match Scores
    └──requires──> AI Matching Results Display

Conversational AI Inbox
    └──requires──> SSE streaming (already built)
    └──requires──> User Authentication & Roles

Department-Facing Hiring Portal
    └──requires──> JD Approval Workflow
    └──requires──> AI Matching Results Display
    └──requires──> User Authentication & Roles

Skills Gap Analysis
    └──requires──> AI Matching Results Display

Candidate-JD Score Explorer
    └──requires──> AI Matching Results Display
    └──requires──> Skills Gap Analysis

AI-Suggested Interview Questions
    └──requires──> Skills Gap Analysis

Basic Dashboard
    └──requires──> JD Creation & Editing (stats about JDs)
    └──requires──> Candidate Status Tracking (stats about candidates)

Reporting & Analytics
    └──requires──> Basic Dashboard
    └──requires──> Candidate Status Tracking (pipeline data)
    └──requires──> AI Matching Results Display (match rate data)

Export Results (PDF/Excel)
    └──requires──> AI Matching Results Display

Bidirectional Matching
    └──requires──> AI Matching Results Display (JD->candidate is primary)
    └──requires──> Candidate Search (candidate->JD needs indexed candidates)
```

### Dependency Notes

- **Authentication is the root dependency.** Every feature requires a logged-in user. Must be built first.
- **JD + Resume management are foundational.** AI matching cannot produce results without source data. These are the two content pillars.
- **HITL review requires matching results to exist.** The review is about matches, not raw candidates.
- **The Department Portal is a downstream feature** because it depends on both JD approval workflows and matching results being mature.
- **AI Interview Questions are a v1.2 differentiator.** Requires gap analysis to be stable first.

## MVP Definition

### Launch With (v1) -- Full-Stack Release

The minimum viable product that validates the core value proposition: "AI-assisted hiring matching with human review."

- [x] **User Authentication & Roles** -- Login with admin/recruiter/hiring-manager roles. Gate all API endpoints.
- [ ] **JD Creation & Editing** -- Create, edit, list, search JDs with structured fields.
- [ ] **Resume Upload & Parsing** -- Upload PDF/DOCX, extract structured candidate info via existing AI pipeline.
- [ ] **Candidate Detail View** -- View parsed resume, tags, notes.
- [ ] **AI Matching Results Display** -- Run the agent pipeline from the UI, see ranked candidates with scores.
- [ ] **Match Approval (Pass/Reject)** -- HR approves/rejects each matched candidate with optional feedback.
- [ ] **Basic Dashboard** -- Overview page: active JDs, pending reviews, recent candidates.
- [ ] **Candidate Status Tracking** -- Simple pipeline status per candidate per JD (New -> Screening -> Approved -> Rejected).

These 8 features form the core loop:
```
JD created --(triggers)--> AI matching --(produces)--> ranked results --(HR reviews)--> approve/reject
```

### Add After Validation (v1.x)

Features to add once the core loop is working and feedback is collected.

- [ ] **Explanatory Match Scores** -- Skill-by-skill breakdown, evidence snippets. Turn the match score into an actionable diagnostic.
- [ ] **HITL Review Flow** -- Replace simple approve/reject with the full interrupt-based review: reviewer agent pauses, HR gives feedback, agent revises. (Note: backend already supports this, frontend needs the flow UX.)
- [ ] **Conversational AI Inbox** -- Natural language interaction with the agent system. Input JD descriptions conversationally, refine matches through dialogue.
- [ ] **Skills Gap Analysis** -- Visual matched/missing skills per candidate. Helps HR decide on "close enough" candidates.
- [ ] **Export Results (PDF/Excel)** -- Generate shareable reports. HR needs to send results to hiring managers.
- [ ] **JD Template Library** -- Reusable templates to speed up JD creation.
- [ ] **Bidirectional Matching** -- Find JDs for a candidate (inverse of primary flow).

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **JD Approval Workflow** -- Multi-stage approval chain. Requires understanding real organizational approval patterns.
- [ ] **Department-Facing Hiring Portal** -- A separate product surface for non-HR users. Needs careful scoping.
- [ ] **Candidate-JD Score Explorer** -- Novel data visualization feature. Wait until users ask for it.
- [ ] **AI-Suggested Interview Questions** -- Valuable but non-essential. Add when gap analysis is mature.
- [ ] **Reporting & Analytics Dashboard** -- Time-to-hire, source effectiveness, funnel conversion. Needs baseline data from real usage.
- [ ] **Candidate Re-engagement (Talent Pool)** -- Proactively match old candidates to new JDs. Powerful but requires a critical mass of candidates.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| User Authentication & Roles | HIGH | MEDIUM | P1 |
| JD Creation & Editing | HIGH | LOW | P1 |
| Resume Upload & Parsing | HIGH | MEDIUM | P1 |
| Candidate Detail View | HIGH | MEDIUM | P1 |
| AI Matching Results Display | CRITICAL | MEDIUM | P1 |
| Match Approval (Pass/Reject) | HIGH | LOW | P1 |
| Basic Dashboard | MEDIUM | MEDIUM | P1 |
| Candidate Status Tracking | HIGH | MEDIUM | P1 |
| Explanatory Match Scores | HIGH | MEDIUM | P2 |
| HITL Review Flow | MEDIUM | MEDIUM | P2 |
| Conversational AI Inbox | HIGH | HIGH | P2 |
| Skills Gap Analysis | HIGH | LOW | P2 |
| Export Results (PDF/Excel) | MEDIUM | LOW | P2 |
| JD Template Library | MEDIUM | LOW | P2 |
| Bi-directional Matching | MEDIUM | MEDIUM | P2 |
| JD Approval Workflow | HIGH | MEDIUM | P3 |
| Department-Facing Portal | MEDIUM | HIGH | P3 |
| Score Explorer Viz | MEDIUM | HIGH | P3 |
| AI Interview Questions | LOW | LOW | P3 |
| Reporting & Analytics | MEDIUM | HIGH | P3 |
| Candidate Re-engagement | MEDIUM | MEDIUM | P3 |

**Priority key:**
- P1: Must have for initial full-stack release (validates core loop)
- P2: Should have, add when core interaction is stable
- P3: Nice to have, defer until product-market fit is established

## Competitor Feature Analysis

| Feature | Moka (China) | Beisen (China) | Manatal (Global) | Our Approach |
|---------|--------------|----------------|------------------|--------------|
| **AI Matching** | Moka Eva, full-flow AI coverage | Limited to assessment | AI Recommendation Engine (0-100%, with justifications) | Multi-agent workflow with transparent chain-of-thought. **Differentiator:** step-by-step reasoning, not black-box. |
| **Explainability** | Basic skill highlights | Weak on non-standard resumes | Line-by-line justifications, gap analysis | Full skill matrix + evidence snippets from resume + gap summary. **Differentiator:** skill-level breakdown. |
| **HITL Flow** | Standard approve/reject | Standard approve/reject | Standard pipeline management | Interrupt-based review: agent pauses, HR gives feedback, agent revises. **Differentiator:** collaborative AI, not just approval. |
| **JD Management** | Full-featured | Full-featured | Rich JD creation + templates | Structured JD with AI-optimized fields for matching. Template library. |
| **Resume Parsing** | Industry-leading accuracy (complex formats) | Standard format OK, non-standard weak | Multi-format parsing | LLM-based parsing (current). Needs Chinese resume verification. |
| **Conversational AI** | No conversational interface | No | No | SSE streaming chat interface. **Differentiator:** natural language interaction with the agent. |
| **Analytics** | Conversational BI (dialog-based) | Management cockpit | Standard reports | P3 -- wait for usage data before building. |
| **Collaboration** | Team notes, @mentions, interviewer assignment | Complex org hierarchy support | Standard team collaboration | Keep minimal -- notes + status changes. External tools for deep collaboration. |
| **Pipeline/Kanban** | Highly configurable | Configurable | Standard kanban | Simple pipeline stages (New -> Screening -> Approved -> Rejected -> Hired). Extend later. |
| **Department Portal** | Full HR + employee self-service | Employee self-service | N/A | P3 -- department heads submit hiring requests and track progress. |

## Sources

- **Competitor analysis:** Moka (mokahr.com), Beisen (beisen.com), Manatal (manatal.com), Greenhouse (greenhouse.io), Lever (lever.co), Workable (workable.com), BambooHR (bamboohr.com), Bullhorn (bullhorn.com)
- **Market reports:** G2 Spring 2025 ATS Grid Report, SHRM AI in Recruiting Report 2025, LinkedIn Global Talent Trends
- **Chinese market analysis:** CSDN comparison articles, Zhihu HR SaaS discussions, Moka/Beisen official feature pages
- **Explainability patterns:** Eightfold AI engineering blog, Manatal AI Recommendation feature page, SkillMatchIQ Greenhouse integration, MDPI research paper on explainable job hiring (Electronics 2025)
- **Kanban/pipeline best practices:** BrightMove Kanban Setup, SenseHQ, PeopleForce Recruit module
- **Anti-feature analysis:** Lever.co adoption gap article, Tribepad recruitment software mistakes, 4SpotConsulting automation pitfalls, Staffing Industry "Frankenstack" article

---

*Feature research for: hellojobs AI Recruitment System*
*Researched: 2026-04-26*
