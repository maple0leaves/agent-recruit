# Architecture Research

**Domain:** Full-stack AI-powered recruitment system (HR admin dashboard + multi-agent backend)
**Researched:** 2026-04-26
**Confidence:** HIGH (architecture verified against codebase analysis, ecosystem research, and established FastAPI+SPA patterns)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                   Frontend Layer (React SPA + Vite)                   │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐   │
│  │  Auth     │  │  JD      │  │ Matching  │  │  Admin /         │   │
│  │  Pages    │  │  Manager │  │  Dashboard│  │  Settings        │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬──────────┘   │
│       │             │             │                   │              │
│  ┌────┴─────────────┴─────────────┴───────────────────┴──────────┐  │
│  │           API Client Layer (openapi-fetch + React Query)       │  │
│  │           SSE Client (fetch-event-source / ReadableStream)     │  │
│  └──────────────────────────────┬─────────────────────────────────┘  │
│                                  │ HTTP + SSE                        │
└──────────────────────────────────┼───────────────────────────────────┘
                                   │
┌──────────────────────────────────┼───────────────────────────────────┐
│                    API Gateway Layer (FastAPI)                         │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                  Auth Middleware (JWT)                           │  │
│  │  /login /logout /refresh  |  dependency injection for routes    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐   │
│  │  JD      │  │ Upload   │  │ Recruit  │  │  SSE Stream       │   │
│  │  CRUD    │  │ Resume   │  │ REST     │  │  (agent progress)  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬──────────┘   │
│       │             │             │                   │              │
├───────┴─────────────┴─────────────┴───────────────────┴──────────────┤
│                   Business Logic / Service Layer                       │
│                                                                       │
│  ┌───────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │  Relational DB    │  │  Agent Workflow  │  │  File Service   │   │
│  │  (SQLAlchemy)     │  │  (LangGraph)     │  │  (local/S3)     │   │
│  └────────┬──────────┘  └────────┬─────────┘  └────────┬────────┘   │
│           │                      │                      │            │
├───────────┴──────────────────────┴──────────────────────┴────────────┤
│                         Data Stores                                   │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │  PostgreSQL  │  │  FAISS       │  │  ChromaDB    │               │
│  │  / SQLite    │  │  (vector     │  │  (candidate  │               │
│  │  (relational)│  │   index)     │  │   memory)    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │  File System (data/uploads/ — PDF/TXT resume files)           │   │
│  └───────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| **React SPA** | HR user interface: JD creation/management, matching dashboard, HR review workflow, file upload, user auth | React 18+ with TypeScript, Vite, Tailwind CSS, React Router |
| **API Client** | Type-safe HTTP client, auto-generated from OpenAPI spec, React Query hooks for server state management | `@hey-api/openapi-ts` or `orval` codegen from FastAPI OpenAPI spec |
| **SSE Client** | Consume real-time agent progress stream, parse structured events, update UI progressively | `@microsoft/fetch-event-source` (POST-capable SSE client) |
| **Auth Middleware** | JWT token validation, route protection, user session management, refresh token rotation | FastAPI dependency injection with `Depends(get_current_user)` |
| **JD CRUD** | Create, read, update, delete job descriptions with structured fields (skills, requirements, etc.) | FastAPI routers + SQLAlchemy async ORM + Alembic migrations |
| **Upload Resume** | Accept PDF/TXT upload, extract text, persist file to disk, register in FAISS index | FastAPI `UploadFile`, `aiofiles`, existing `rag/vector_store.py` |
| **Agent Workflow** | Multi-agent LangGraph state machine for candidate matching, scoring, reporting | Existing: `agent/`, `main.py` (no changes needed) |
| **SSE Stream** | Bridge LangGraph streaming to HTTP SSE, push node progress, tool calls, results | Existing: `api/server.py:_stream_recruitment()` (no changes needed) |
| **Relational DB** | Structured data: users, JDs, candidates, match history, file metadata, audit logs | SQLAlchemy async + SQLite (dev) / PostgreSQL (prod) |
| **Vector Index** | Semantic search over resume corpus | Existing: FAISS index (no changes needed) |
| **Memory Store** | Long-term candidate evaluation history | Existing: ChromaDB (no changes needed) |
| **File System** | Persistent storage for uploaded PDF/TXT files | `data/uploads/` directory, abstracted behind `FileStorage` interface |

## Recommended Project Structure

```
hellojobs/                              # Monorepo root
├── backend/                            # Python backend (existing + new)
│   ├── api/                            # FastAPI server
│   │   ├── server.py                   # App factory, middleware, lifespan
│   │   ├── routes/                     # Route modules
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                 # /auth/login, /auth/refresh, /auth/logout
│   │   │   ├── jds.py                  # /jds CRUD
│   │   │   ├── candidates.py           # /candidates CRUD
│   │   │   ├── recruit.py              # /recruit, /recruit/stream, /recruit/hitl
│   │   │   ├── upload.py               # /upload-resume, /upload/jd
│   │   │   └── admin.py               # /admin/rebuild-index, /admin/stats
│   │   └── deps.py                     # Shared dependencies (get_db, get_current_user)
│   │
│   ├── agent/                          # Existing — no structural changes
│   ├── rag/                            # Existing — no structural changes
│   ├── skills/                         # Existing — no structural changes
│   │
│   ├── db/                             # NEW: Database layer
│   │   ├── __init__.py
│   │   ├── engine.py                   # Async engine + session factory
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py                 # User model (HR accounts)
│   │   │   ├── job_description.py      # JD model
│   │   │   ├── candidate_record.py     # Candidate metadata model
│   │   │   ├── match_session.py        # Match run history
│   │   │   └── uploaded_file.py        # File upload metadata
│   │   ├── migrations/                 # Alembic migration files
│   │   │   ├── env.py
│   │   │   ├── alembic.ini
│   │   │   └── versions/
│   │   └── repository/                 # Data access pattern (optional)
│   │       ├── user_repo.py
│   │       ├── jd_repo.py
│   │       └── candidate_repo.py
│   │
│   ├── storage/                        # NEW: File storage abstraction
│   │   ├── __init__.py
│   │   ├── base.py                     # Abstract FileStorage interface
│   │   ├── local.py                    # Local filesystem implementation
│   │   └── s3.py                       # S3 implementation (future)
│   │
│   ├── auth/                           # NEW: Authentication
│   │   ├── __init__.py
│   │   ├── jwt.py                      # JWT encode/decode, token models
│   │   ├── password.py                 # Password hashing (bcrypt)
│   │   └── middleware.py               # Auth dependency (get_current_user)
│   │
│   ├── schemas/                        # NEW: API Pydantic schemas (moved from agent/)
│   │   ├── __init__.py
│   │   ├── auth.py                     # LoginRequest, TokenResponse
│   │   ├── jd.py                       # JDCreate, JDUpdate, JDResponse
│   │   ├── candidate.py                # CandidateResponse
│   │   └── common.py                   # Pagination, error responses
│   │
│   ├── main.py                         # Existing LangGraph entry (unchanged)
│   ├── config.py                       # Existing (add DB, auth config keys)
│   ├── requirements.txt                # Existing + add sqlalchemy, alembic, bcrypt, pyjwt
│   └── tests/                          # Existing test structure
│
├── frontend/                           # NEW: React SPA
│   ├── src/
│   │   ├── main.tsx                    # App entry
│   │   ├── App.tsx                     # Router setup
│   │   ├── api/                        # API client layer
│   │   │   ├── client.ts              # Generated HTTP client
│   │   │   ├── types.ts               # Generated TypeScript types from OpenAPI
│   │   │   └── sse.ts                 # SSE connection manager
│   │   ├── hooks/                      # React Query hooks (auto-generated or manual)
│   │   │   ├── useAuth.ts
│   │   │   ├── useJDs.ts
│   │   │   └── useRecruit.ts
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── JDs/
│   │   │   │   ├── JDList.tsx
│   │   │   │   └── JDEditor.tsx
│   │   │   ├── Matching/
│   │   │   │   ├── MatchForm.tsx
│   │   │   │   └── MatchResults.tsx
│   │   │   └── Admin/
│   │   │       └── Settings.tsx
│   │   ├── components/                 # Shared UI components
│   │   │   ├── Layout.tsx
│   │   │   ├── Pipeline.tsx            # Agent progress visualization
│   │   │   ├── CandidateCard.tsx
│   │   │   └── FileUpload.tsx
│   │   ├── stores/                     # Client-side state (Zustand if needed)
│   │   │   └── authStore.ts
│   │   ├── styles/
│   │   │   └── globals.css             # Tailwind base styles
│   │   └── utils/
│   │       ├── format.ts
│   │       └── constants.ts
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── package.json
│   └── openapi-codegen.config.ts       # Codegen config for API types
│
├── scripts/                            # Existing (eval scripts)
├── data/                               # Existing (runtime data)
│   ├── resumes/                        # Existing (source resumes for FAISS)
│   ├── uploads/                        # NEW: Uploaded resume/JD files
│   ├── vector_store/                   # Existing (FAISS index)
│   ├── chroma_memory/                  # Existing (ChromaDB)
│   └── dev.db                          # NEW: SQLite dev database
│
├── docker-compose.yml                  # NEW: PostgreSQL for prod
├── Makefile                            # NEW: Dev commands
├── .env.example                        # Update with DB, auth vars
├── requirements.txt                    # Backend deps (moved to backend/)
└── package.json                        # Root workspace config (pnpm workspaces)
```

### Structure Rationale

- **`backend/` and `frontend/` at top level**: Clear separation of Python and JS/TS ecosystems. Each has its own build system, dependency management, and test framework. Avoids npm/pip conflicts in a single directory.

- **`backend/db/` as a new module**: Relational database is the biggest missing piece. This module owns all ORM models, migrations, and session management. No circular dependency with existing `agent/` or `rag/`.

- **`backend/schemas/` as a new module**: API-facing Pydantic schemas should be separate from internal agent schemas in `agent/schemas.py`. This prevents the API layer from depending on agent internals directly. Agent schemas and API schemas may diverge (e.g., API responses include timestamps, pagination that internal schemas don't need).

- **`backend/auth/` as a new module**: Authentication is a cross-cutting concern. The existing codebase has zero auth — adding a module rather than spraying auth logic across routes.

- **`backend/storage/` with abstract interface**: File storage should be swappable. Start with local filesystem, switch to S3 later without touching business logic.

- **`frontend/src/api/` for generated client**: Never manually write API fetch calls. Use OpenAPI codegen to produce a type-safe client that matches backend Pydantic models exactly. This is the single source of truth for the API contract.

- **`frontend/src/hooks/` for React Query hooks**: TanStack Query (React Query) for all server state. No raw `useEffect` + `fetch` patterns. React Query handles caching, refetching, loading/error states uniformly.

## Architectural Patterns

### Pattern 1: OpenAPI Contract-First Development

**What:** FastAPI auto-generates an OpenAPI 3.1 spec from Pydantic models. A codegen tool watches this spec and produces TypeScript types + a typed fetch client. Frontend imports these types — any backend schema change immediately surfaces as a type error in the frontend.

**When to use:** Any project where Python backend serves a TypeScript frontend. This is the standard pattern for FastAPI + TS stacks in 2025-2026.

**Trade-offs:**
- + Eliminates entire class of "API mismatch" bugs
- + Single source of truth (Pydantic models) for both sides
- + Boilerplate elimination: no manual API client code
- - Requires a file watcher during development to regenerate on schema changes
- - Generated types are "dumb" (no runtime validation on frontend — use Zod if needed)

**Example workflow:**

```
backend/agent/schemas.py       backend/api/schemas/jd.py
         \                           /
          \                         /
           → FastAPI generates OpenAPI JSON ←
                      |
                      ↓
        @hey-api/openapi-ts codegen
                      |
          ┌───────────┴───────────┐
          ↓                       ↓
   frontend/api/types.ts    frontend/api/client.ts
          ↓                       ↓
   TypeScript compiler      React Query hooks
   catches type errors       call typed client
```

**Example codegen config (`frontend/openapi-codegen.config.ts`):**

```typescript
// Trigger: watches backend/openapi.json, regenerates on change
import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: '../backend/openapi.json',
  output: 'src/api',
  client: '@hey-api/client-fetch',
  services: { asClass: false },
  schemas: { export: true },
});
```

### Pattern 2: SSE Bridging via Fetch-Event-Source

**What:** The backend already streams LangGraph agent progress as SSE events via `_stream_recruitment()`. The frontend needs to consume this stream with POST support (native `EventSource` only supports GET). Use `@microsoft/fetch-event-source` to POST to `/recruit/stream` and parse structured SSE events.

**When to use:** Any real-time agent progress visualization. This is the correct pattern for streaming LLM/agent output to a browser.

**Trade-offs:**
- + Reuses existing backend SSE implementation (no changes needed)
- + Supports POST (required for sending the `user_input` payload)
- + Structured events (status, tool_call, progress, result, error) enable rich UI updates
- - SSE connections are long-lived — need proper cleanup on navigation/unmount
- - EventSource auto-reconnect works for GET but not for POST (must implement manual retry)

**Example — frontend SSE consumer (`frontend/src/api/sse.ts`):**

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source';

export interface SSEEvent {
  event: 'status' | 'tool_call' | 'progress' | 'result' | 'error';
  data: Record<string, unknown>;
}

export interface SSEHandlers {
  onStatus?: (node: string) => void;
  onToolCall?: (tool: string, args: Record<string, unknown>) => void;
  onProgress?: (message: string) => void;
  onResult?: (report: string, matches: unknown[]) => void;
  onError?: (message: string) => void;
}

export function streamRecruitment(
  userInput: string,
  resumeText: string | null,
  handlers: SSEHandlers,
  options?: { signal?: AbortSignal },
): Promise<void> {
  return fetchEventSource('/api/recruit/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_input: userInput, resume_text: resumeText }),
    signal: options?.signal,
    onmessage(event) {
      let payload: SSEEvent;
      try {
        payload = JSON.parse(event.data);
      } catch {
        return;
      }
      switch (payload.event) {
        case 'status':
          handlers.onStatus?.(payload.data.node as string);
          break;
        case 'tool_call':
          handlers.onToolCall?.(
            payload.data.tool as string,
            payload.data.args as Record<string, unknown>,
          );
          break;
        case 'progress':
          handlers.onProgress?.(payload.data.message as string);
          break;
        case 'result':
          handlers.onResult?.(
            payload.data.final_report as string,
            payload.data.match_results as unknown[],
          );
          break;
        case 'error':
          handlers.onError?.(payload.data.message as string);
          break;
      }
    },
    onerror(err) {
      // Connection-level error (network, timeout, etc.)
      handlers.onError?.(err.message ?? 'SSE connection lost');
      // Return false to stop reconnection, true to retry
      return false;
    },
  });
}
```

**Backend:** No changes needed — the existing `api/server.py:_stream_recruitment()` generator produces SSE events with the exact structure consumed above.

### Pattern 3: JWT Auth with HTTP-Only Cookies for SSE

**What:** Standard JWT auth for REST endpoints (`Authorization: Bearer` header) plus HTTP-only cookies for SSE connections (which cannot set custom headers via EventSource). Access token lives in memory (React state), refresh token in HTTP-only cookie.

**When to use:** Any SPA that needs both standard API calls and SSE streaming. The hybrid approach solves the "SSE can't set Authorization header" limitation.

**Trade-offs:**
- + More secure than localStorage (no XSS token theft)
- + SSE can carry auth via cookies without custom headers
- - Requires CSRF protection for cookie-based endpoints
- - Token refresh logic is more complex than simple bearer-only

**Example — FastAPI auth flow:**

```python
# backend/auth/jwt.py
from datetime import datetime, timedelta, timezone
import jwt

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: str) -> str:
    return jwt.encode(
        {"sub": user_id, "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
        SECRET_KEY,
        algorithm="HS256",
    )

def create_refresh_token(user_id: str) -> str:
    return jwt.encode(
        {"sub": user_id, "type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)},
        SECRET_KEY,
        algorithm="HS256",
    )
```

```python
# backend/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    # Also check cookie for SSE fallback
):
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # Check cookie (for SSE connections)
        # token = request.cookies.get("access_token")
        pass

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload["sub"]
```

**SSE auth flow:** The frontend sets the access token as an HTTP-only cookie at login time (server sets `Set-Cookie`). The SSE endpoint reads this cookie for authentication, avoiding the custom header limitation.

### Pattern 4: Background Task for FAISS Index Update

**What:** Uploading a resume should: (1) persist the file, (2) register it in the relational DB, (3) update the FAISS index asynchronously. Use FastAPI `BackgroundTasks` to decouple the index rebuild from the upload response.

**When to use:** Any upload that triggers a vector index update (which can take 2-30 seconds depending on corpus size).

**Trade-offs:**
- + Upload returns immediately; API is responsive
- + Index can be batched (debounce multiple uploads before rebuilding)
- - FAISS index is stale until rebuild completes
- - Index rebuild failures need error logging + alerting

**Example:**

```python
from fastapi import BackgroundTasks

def rebuild_index_background():
    """Rebuild FAISS index with debounce (skip if a rebuild is already queued)."""
    from config import RESUME_DIR, VECTOR_STORE_PATH
    from rag.vector_store import build_vector_store
    from rag.retriever import invalidate_vector_store_cache

    build_vector_store(RESUME_DIR, VECTOR_STORE_PATH)
    invalidate_vector_store_cache()

@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
):
    # 1. Validate and persist file
    file_record = await file_service.save_upload(file)

    # 2. Register in DB
    db.add(file_record)
    await db.commit()

    # 3. Queue FAISS rebuild (debounced)
    background_tasks.add_task(rebuild_index_background)

    return {"id": file_record.id, "filename": file_record.filename}
```

### Pattern 5: Repository Layer for DB Access

**What:** Abstract database operations behind repository classes rather than writing raw SQLAlchemy queries in route handlers. Each model gets a repository (`jd_repo.py`, `user_repo.py`) with focused query methods.

**When to use:** When a project has more than 3-4 database models. The repository pattern keeps route handlers thin and testable.

**Trade-offs:**
- + Isolates DB query logic from route handlers
- + Easier to test (mock repository interfaces)
- + Queries are reusable across multiple routes
- - More files to maintain
- - Overkill for very simple CRUD-only models

**Example:**

```python
# backend/db/repository/jd_repo.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models.job_description import JobDescription

class JDRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, jd_id: int) -> JobDescription | None:
        result = await self.session.execute(
            select(JobDescription).where(JobDescription.id == jd_id, JobDescription.is_active == True)
        )
        return result.scalar_one_or_none()

    async def list_by_status(self, status: str, skip: int = 0, limit: int = 20):
        result = await self.session.execute(
            select(JobDescription)
            .where(JobDescription.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(JobDescription.updated_at.desc())
        )
        return result.scalars().all()

    async def create(self, data: dict) -> JobDescription:
        jd = JobDescription(**data)
        self.session.add(jd)
        await self.session.commit()
        await self.session.refresh(jd)
        return jd
```

## Data Flow

### Primary Flow: HR Creates JD and Runs Matching

```
[HR User]
    |
    | 1. Login (POST /auth/login)
    |    → Returns JWT access token (memory) + refresh token (HTTP-only cookie)
    v
[React SPA - Login Page]
    |
    | 2. Create JD (POST /api/jds with auth header)
    |    → Pydantic validated → SQLAlchemy INSERT → Return JDResponse
    v
[FastAPI - JD Route]
    |
    | 3. Navigate to Matching Dashboard
    |    → Fetch JD list (GET /api/jds) → Display in dropdown
    v
[React SPA - MatchForm]
    |
    | 4. Submit matching request (POST /api/recruit/stream)
    |    → Auth middleware validates JWT (from cookie for SSE)
    |    → Starts LangGraph workflow in background thread
    |    → SSE events pushed through asyncio.Queue
    v
[FastAPI - SSE Stream Endpoint]
    |
    | 5. SSE events streamed to frontend:
    |    event: status   → "triage_router completed"
    |    event: progress → "已激活技能: resume_analysis, candidate_matching"
    |    event: tool_call → "{tool: 'search_candidates', args: {...}}"
    |    event: status   → "planner_agent completed"
    |    event: status   → "worker_agent completed"
    |    event: progress → "候选人匹配完成，共 5 位"
    |    event: status   → "reviewer_agent completed"
    |    event: result   → "{final_report, match_results}"
    v
[React SPA - Pipeline Visualization]
    |
    | 6. Update pipeline step indicators (progress bar)
    |    → Show candidate cards as they arrive
    |    → Display final report when done
    v
[HR User sees results]
```

### HITL (Human-in-the-Loop) Flow

```
[User starts matching in HITL mode]
    |
    | POST /api/recruit/hitl/start → Workflow pauses at reviewer_agent
    v
[SSE: waiting_for_review event → UI shows review card]
    |
    | HR reviews candidates, provides feedback
    | POST /api/recruit/hitl/resume with {hr_approved, hr_feedback}
    v
[Workflow resumes → reviewer_agent generates final report]
    |
    | SSE: result event → UI shows final report
    v
[Session recorded in DB: match_session table]
```

### File Upload Flow

```
[HR User drags PDF to upload zone]
    |
    | POST /api/upload-resume (multipart/form-data, auth header)
    v
[FastAPI - Upload Route]
    |
    ├── 1. Validate file type (.pdf/.txt) and size limit
    ├── 2. Generate UUID filename → Save to data/uploads/
    ├── 3. Extract text via pymupdf
    ├── 4. Register in DB: uploaded_files table
    ├── 5. BackgroundTasks: trigger FAISS rebuild
    v
[Response: {id, filename, text, pages, status: "indexing"}]
    |
    v
[React SPA shows success + extracted text preview]
```

### State Management

| State Category | Location | Storage | Notes |
|---------------|----------|---------|-------|
| **Auth state** | Frontend | React context + Zustand | JWT in memory only; refresh in HTTP-only cookie |
| **Server data** (JDs, candidates) | Frontend | React Query cache | Auto-refetch on mutation, stale-while-revalidate |
| **SSE stream state** | Frontend | React ref + state | Not in React Query (streaming, not request-response) |
| **UI state** (form inputs, theme) | Frontend | React state + localStorage | Theme persisted; form state ephemeral |
| **Relational data** | Backend | SQLAlchemy + PostgreSQL/SQLite | Users, JDs, match history, files |
| **Vector index** | Backend | FAISS (file on disk) | Resume embeddings for semantic search |
| **Candidate memory** | Backend | ChromaDB (file on disk) | Long-term evaluation history |
| **HITL checkpoints** | Backend | InMemorySaver (current) | Should migrate to persistent (PostgresSaver or SqliteSaver) |

## Database Schema (Relational)

The current architecture lacks a relational database. Adding one enables:

| Domain | Tables Needed | Purpose |
|--------|--------------|---------|
| **Auth** | `users`, `refresh_tokens` | HR account management, session management |
| **JD Management** | `job_descriptions` | Structured JD storage with skills, requirements |
| **Candidates** | `candidates` | Candidate metadata (name, email, skills from parsed resumes) |
| **Matching** | `match_sessions`, `match_results` | Track who matched what JD when, store results |
| **Files** | `uploaded_files` | Track uploaded PDF/TXT files, storage paths, extraction status |
| **HITL** | `hitl_checkpoints` | Persistent HITL state (replaces InMemorySaver) |

**Recommendation:** Start with SQLite (`aiosqlite`) for development. The schema is simple enough that SQLAlchemy's async engine makes PostgreSQL migration trivial (change connection string). Do NOT skip the relational DB — the existing FAISS+ChromaDB cannot model the relational data needed for JD management, user accounts, and audit trails.

```
users
├── id (PK)
├── email (unique)
├── hashed_password
├── name
├── role (admin | hr)
├── is_active
├── created_at
└── updated_at

job_descriptions
├── id (PK)
├── title
├── department
├── description_text          (full JD text)
├── required_skills           (JSON array)
├── preferred_skills          (JSON array)
├── min_years_experience
├── education_requirement
├── status                    (draft | active | closed)
├── created_by (FK → users)
├── created_at
└── updated_at

candidates                    (metadata, not resume text)
├── id (PK)
├── name
├── email (unique per system)
├── parsed_skills             (JSON array)
├── years_of_experience
├── education
├── resume_file_id (FK → uploaded_files)
├── created_at
└── updated_at

match_sessions                (one matching run)
├── id (PK)
├── jd_id (FK → job_descriptions)
├── initiated_by (FK → users)
├── mode                      (standard | hitl)
├── status                    (running | paused | completed | failed)
├── started_at
└── completed_at

match_results                 (candidate-JD pair score)
├── id (PK)
├── session_id (FK → match_sessions)
├── candidate_id (FK → candidates)
├── match_score (0-100)
├── matched_skills (JSON)
├── missing_skills (JSON)
├── recommendation
├── should_proceed
├── hr_approved (nullable boolean)
├── hr_feedback
└── created_at

uploaded_files
├── id (PK)
├── original_filename
├── storage_path
├── file_type (pdf | txt)
├── file_size
├── extracted_text
├── page_count
├── indexed_in_faiss (boolean)
├── uploaded_by (FK → users)
├── created_at
└── updated_at
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **LLM API** (OpenAI / OpenRouter) | HTTP via `langchain` / `openai` SDK | Existing. Rate limits, retry logic handled. |
| **Embedding API** (OpenAI / HuggingFace) | HTTP via `langchain` | Existing. FAISS index build dependency. |
| **Rerank API** (Cohere-compatible) | HTTP via `rag/reranker.py` | Existing. Falls back gracefully. |
| **LangSmith** (optional) | SDK + env vars | Existing. Tracing for debugging agent runs. |
| **MCP Servers** (external tools) | stdio/SSE via `agent/mcp_tools.py` | Existing. Dynamic tool loading. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Frontend SPA <-> FastAPI** | HTTP REST + SSE | OpenAPI spec is the contract. Auth via JWT. |
| **FastAPI Routes <-> Agent Engine** | Direct Python calls to `main.py:run()` | Routes are thin wrappers around agent invocation. |
| **FastAPI Routes <-> Relational DB** | SQLAlchemy async ORM | All DB access goes through repository classes. |
| **Upload Route <-> FAISS Index** | Background task callback | Upload triggers async index rebuild. |
| **Agent Engine <-> FAISS** | Direct import of `rag/retriever.py` | Existing. No changes needed. |
| **Agent Engine <-> ChromaDB** | Direct import of `agent/memory.py` | Existing. No changes needed. |

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-10 HR users** (current target) | Single server, SQLite, local file storage. The existing agent architecture handles this easily. |
| **10-100 HR users** | Switch to PostgreSQL, add connection pooling via `pgbouncer` or SQLAlchemy pool. Add S3 for file storage. Consider read replicas for the relational DB if report queries become heavy. |
| **100+ HR users / multiple tenants** | Add tenant isolation (separate DB schema per tenant). Cache frequent reads (JD list, candidate list) with Redis. Consider migrating FAISS to pgvector for unified DB management. Separate the agent worker into a background queue (Celery / Arq) so API servers stay responsive. |

### Scaling Priorities

1. **First bottleneck: HITL checkpoint persistence.** The current `InMemorySaver` loses state on server restart. For any production deployment, replace with `SqliteSaver` (same-file, no new dependency) or `PostgresSaver` (for PostgreSQL deployments). This is `langgraph-checkpoint` library support.

2. **Second bottleneck: FAISS index rebuild on upload.** As the resume corpus grows, full index rebuilds take longer. Mitigation: debounce rebuilds (batch multiple uploads), or switch to incremental indexing. For < 1000 resumes, full rebuild is acceptable (< 30s).

3. **Third bottleneck: Concurrent agent runs.** The LangGraph workflow is CPU-bound during candidate scoring (`ThreadPoolExecutor` with 8 threads). Multiple concurrent matching requests could saturate CPU and LLM rate limits. Mitigation: limit concurrent runs via a semaphore, or queue jobs.

## SSE Streaming Architecture (Detailed)

The SSE stream is the most architecturally significant integration between frontend and backend. Here is how it works in detail:

```
Frontend                              Backend
   │                                     │
   │  POST /recruit/stream               │
   │  {user_input, resume_text}          │
   │─────────────────────────────────→   │
   │                                     │  Auth middleware validates JWT
   │                                     │  from cookie (SSE can't set headers)
   │                                     │
   │  event: progress                    │  Skills loaded, matched
   │←─────────────────────────────────   │
   │  event: status (triage)             │  LangGraph stream starts
   │←─────────────────────────────────   │
   │  event: status (planner)            │
   │  event: tool_call                   │
   │←─────────────────────────────────   │
   │  event: status (worker)             │
   │  event: progress (candidate count)  │
   │←─────────────────────────────────   │
   │  event: tool_call × N              │  Parallel candidate scoring
   │←─────────────────────────────────   │
   │  event: status (reviewer)           │
   │←─────────────────────────────────   │
   │  event: result                      │  Final report + matches
   │←─────────────────────────────────   │
   │  Connection closed                  │
   │                                     │
```

**Key design decisions:**
- The backend already uses `StreamingResponse` with `text/event-stream` — this is correct.
- The frontend must consume POST SSE — use `@microsoft/fetch-event-source` (native `EventSource` only supports GET).
- The SSE endpoint should NOT block the auth middleware — use a cookie-based auth check at the start of the stream.
- Nginx/Apache must disable buffering for SSE: `X-Accel-Buffering: no` (already set in backend).
- Browser SSE connection limits (6 per domain) are not an issue for a single-stream internal tool.

## Build Order (Dependency Graph)

```
Phase 1: Foundation
├── Auth system (backend + frontend login)
├── Relational DB setup (SQLite, models, migrations)
├── Frontend scaffold (Vite, React, Router, Tailwind)
├── OpenAPI codegen pipeline
└── API client infrastructure (React Query + SSE client)
    │
    ├── Required by: Everything below
    │
    v
Phase 2: JD Management
├── JD CRUD endpoints (FastAPI routes + SQLAlchemy)
├── JD management UI (list, create, edit, delete)
├── JD form with structured fields (skills, requirements)
└── Department management
    │
    ├── Required by: Matching (needs JDs to match against)
    │
    v
Phase 3: Real SSE Integration
├── Replace fake timer simulation in frontend
├── SSE consumer with fetch-event-source
├── Pipeline visualization (real agent progress)
├── Candidate card rendering from SSE result events
└── Error handling + reconnection
    │
    ├── Required by: Matching Dashboard (Phase 4)
    │
    v
Phase 4: Matching Dashboard
├── Matching form UI (select JD, run matching)
├── Live results display (candidate cards from SSE)
├── Report viewer (markdown rendered)
├── HITL review workflow in UI
└── Match history (sessions list)
    │
    ├── Required by: HR workflow (Phase 5)
    │
    v
Phase 5: File Management
├── Persistent file storage with metadata DB
├── Upload UI improvements (drag-drop, progress)
├── Resume library browser
├── FAISS auto-rebuild on upload (background task)
└── File validation + size limits
    │
    ├── Independent: Can be built alongside Phase 4
    │
    v
Phase 6: Production Hardening
├── Persistent HITL checkpoint saver (SqliteSaver)
├── Rate limiting on agent endpoints
├── Audit logging
├── Report export (PDF/Excel)
└── Deployment config (Docker Compose, nginx)
```

## Anti-Patterns

### Anti-Pattern 1: Fake Timer Simulation Instead of Real SSE

**What the current code does:** `static/index.html` uses `setTimeout` timers to simulate pipeline progress (lines 946-965). No actual SSE consumption.

**Why it's wrong:** The backend has a perfectly good real SSE stream at `/recruit/stream`. Using fake timers means:
- The UI shows progress even when the backend has stalled or errored
- The "timing" display shows fake durations (~1.2s per step), not real wall-clock time
- No actual tool call or progress information reaches the user

**Do this instead:** Use `@microsoft/fetch-event-source` to consume the real SSE stream. Map SSE events to real UI updates. Show actual step durations from backend execution.

### Anti-Pattern 2: Single Static HTML File as Frontend

**What the current code does:** 1150 lines of HTML, CSS, and JavaScript in one `static/index.html` file. No build step, no TypeScript, no component separation.

**Why it's wrong:** Extending this to a multi-page HR dashboard with auth, JD management, matching, and admin pages would be unsustainable. Every feature adds to the same monolithic file. No type safety for API calls (raw `fetch` with manual JSON parsing). No dependency management for frontend libraries.

**Do this instead:** Create a proper React SPA with Vite. Component-per-file organization. TypeScript everywhere. API client auto-generated from OpenAPI spec.

### Anti-Pattern 3: Module-Level Mutable State Across Graph Nodes

**What:** `rag/retriever.py:18` caches FAISS vector store in a module global. LLM singletons in `agent/agent.py:56-60` are module globals. The vector store cache must be explicitly invalidated on rebuild.

**Why it's wrong:** Already identified in the existing `ARCHITECTURE.md` (line 232-236). If two concurrent requests trigger a rebuild, race conditions are possible. While the existing code works for single-user scenarios, adding a multi-user frontend will increase the likelihood of concurrent rebuilds.

**Do this instead:** Add a `asyncio.Lock` for the vector store rebuild operation. The existing `invalidate_vector_store_cache()` and `build_vector_store()` calls should be wrapped in an async lock to prevent concurrent rebuilds.

### Anti-Pattern 4: InMemorySaver for HITL (Unchanged from Current)

**What:** HITL workflows use `InMemorySaver()` (`main.py:70`), which stores checkpoints in process memory only.

**Why it's wrong:** Already identified in the existing `ARCHITECTURE.md` (line 227-231). With a multi-user frontend, multiple concurrent HITL sessions are possible, and process restart loses all pending reviews.

**Do this instead:** Replace with `SqliteSaver` from `langgraph-checkpoint` (no new infrastructure) or `PostgresSaver` (for PostgreSQL deployments). This is a Phase 6 task since HITL works in-memory for development.

## Sources

- [Existing codebase architecture analysis](.planning/codebase/ARCHITECTURE.md) — Verified all existing patterns remain valid
- [FastAPI + Next.js monorepo patterns](https://github.com/vintasoftware/nextjs-fastapi-template) — OpenAPI codegen, Turborepo structure, pre-commit hooks (HIGH confidence, active template)
- [OpenAPI codegen for FastAPI monorepos](https://www.vintasoftware.com/blog/nextjs-fastapi-monorepo) — watchers, generated clients, type safety (HIGH confidence)
- [FastAPI SSE streaming](https://blog.gopenai.com/how-to-stream-llm-responses-in-real-time-using-fastapi-and-sse-d2a5a30f2928) — SSE pattern validation (MEDIUM confidence, cross-referenced with existing code)
- [FastAPI JWT auth for SPAs](https://www.david-crimi.com/blog/user-auth) — HTTP-only cookies, refresh rotation (HIGH confidence)
- [FastAPI + SQLAlchemy async](https://dev.to/rosewabere/building-a-production-grade-async-backend-with-fastapi-sqlalchemy-postgresql-and-alembic-2ca4) — Async DB patterns (HIGH confidence)
- [Recruitment system DB schemas](https://deepwiki.com/omarfarouk311/Recruitment-Management-Platform-Backend/2.2-database-schema) — Reference schema for JD, candidate, match tables (MEDIUM confidence)

---
*Architecture research for: HelloJobs AI recruitment full-stack architecture*
*Researched: 2026-04-26*
