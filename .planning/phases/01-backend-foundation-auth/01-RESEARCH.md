# Phase 1: Backend Foundation & Authentication - Research

**Researched:** 2026-04-26
**Domain:** Full-stack authentication, database, frontend scaffold
**Confidence:** HIGH (all major packages verified against npm/PyPI registry)

## Summary

Phase 1 transforms the unprotected agent backend into a secured foundation with authentication, persistent storage, and a frontend shell. This phase covers three requirements (AUTH-01 through AUTH-03) and forms the dependency for all downstream development.

**Primary recommendation:** Implement backend-first: database schema + auth middleware + SqliteSaver, then frontend scaffold with login page and protected route shell. Use `bcrypt` directly (not passlib) due to passlib 1.7.4 being unmaintained and incompatible with bcrypt 5.0.0.

**Key discovery -- passlib + bcrypt 5.0.0 incompatibility:** The installed `passlib==1.7.4` is incompatible with `bcrypt==5.0.0` (breaing change: bcrypt removed `__about__` module and rejects passwords >72 bytes by default). Since passlib has been unmaintained since 2020, the recommended approach is to use `bcrypt` directly for password hashing. The user decision D-02 says "passlib(bcrypt)" -- this needs user confirmation to switch to straight `bcrypt`.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** JWT stored in HTTP-only cookie (not localStorage) -- prevents XSS, SSE needs no extra handling
- **D-02:** PyJWT + passlib(bcrypt) as JWT and password hashing libraries, paired with FastAPI OAuth2PasswordBearer pattern
- **D-03:** Simple role check -- role field in JWT payload, backend Depends() checks. Three roles: admin / recruiter / hiring-manager
- **D-04:** Login page provides username+password login, no registration page, no "remember me"
- **D-05:** SQLite + SQLAlchemy async -- zero-config dev, schema designed to PostgreSQL spec, switch to PostgreSQL by changing connection string later
- **D-06:** Minimal users table: username, hashed_password, role (enum: admin/recruiter/hiring-manager), created_at
- **D-07:** Alembic for migrations, initial migration creates users table
- **D-08:** CLI seed script (seed.py) creates first admin user, password via environment variable or command-line argument
- **D-09:** LangGraph checkpoint from InMemorySaver to SqliteSaver, reusing the same SQLite file
- **D-10:** React 19 + Vite + TypeScript + Tailwind CSS v4 + shadcn/ui
- **D-11:** Full app shell -- login page + sidebar+topbar layout + protected route placeholder pages
- **D-12:** TanStack Query + axios for API interaction, axios configured withCredentials to auto-send cookies
- **D-13:** Route structure: /login (public), / (redirect to /dashboard), /dashboard /jd /candidates /matching (protected placeholder pages)
- **D-14:** Production: FastAPI directly hosts Vite build dist/ static files, no separate frontend service needed
- **D-15:** All done in Phase 1 -- auth middleware, SSE timeout/disconnect handling, async endpoint conversion, CORS configuration, request body input validation
- **D-16:** CORS configured for frontend dev and production domains, credentials enabled (for cookie cross-origin)

### Claude's Discretion
- Login page and layout specific visual design (colors, spacing, fonts)
- Password strength policy (minimum length, special characters)
- Token expiry specific values
- SSE timeout specific seconds
- Loading/error state specific UI

### Deferred Ideas (OUT OF SCOPE)
- User registration page -- beyond Phase 1 scope, admin creates users via CLI
- "Remember me" feature -- not in Phase 1
- Fine-grained permissions (department-level isolation) -- simple role check sufficient, upgrade later as needed
- Frontend SSR/Next.js -- React SPA chosen, no SEO requirement
- Independent frontend deployment (nginx) -- FastAPI hosting sufficient for now
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | HR can login with username and password | Password hashing via bcrypt; JWT generation via PyJWT; FastAPI auth endpoints; login form in React |
| AUTH-02 | System supports role distinction (admin, recruiter, hiring-manager) | JWT payload includes `role` field; FastAPI Depends() middleware checks role; users table has role column; enum type defined in SQLAlchemy model |
| AUTH-03 | Login state persists across page refreshes | HTTP-only cookie stores refresh token; access token in memory; axios withCredentials auto-sends cookies; FastAPI validates cookies on each request |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| User login (password verify) | API / Backend | -- | bcrypt hash comparison must happen server-side |
| JWT token generation/verification | API / Backend | -- | Token signing key never leaves server |
| HTTP-only cookie management | API / Backend | -- | Server sets Set-Cookie header; client cannot read HttpOnly |
| Session persistence across refresh | API / Backend | -- | Refresh token in cookie validated server-side |
| Role check on protected endpoints | API / Backend | -- | JWT role field decoded server-side in Depends() |
| Login page UI | Browser / Client | -- | React form component, POST credentials |
| Protected route guard | Browser / Client | API / Backend | Frontend guards routes; backend enforces via 401 |
| Sidebar/topbar layout | Browser / Client | -- | React layout component, role-aware navigation |
| API state management | Browser / Client | -- | TanStack Query caches, axios sends cookies |
| User/role data storage | Database / Storage | -- | SQLAlchemy async + SQLite users table |

---

## Standard Stack

### Core -- Backend

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.3 | API framework | Already in project; async-native; auto OpenAPI docs |
| SQLAlchemy | 2.0.49 | Async ORM | Standard Python ORM; async engine for SQLite via aiosqlite |
| Alembic | 1.18.4 | DB migrations | Standard SQLAlchemy migration tool; auto-generation from models |
| aiosqlite | 0.22.1 | Async SQLite driver | Required by SQLAlchemy async engine for SQLite |
| PyJWT | 2.12.1 | JWT encode/decode | Pure Python; actively maintained; standard for FastAPI auth |
| bcrypt | 5.0.0 | Password hashing | Industry standard; works standalone; UTF-8 safe for Chinese chars |
| python-multipart | 0.0.26 | Form data parsing | Required by FastAPI for form-data (login form, file upload) |
| Uvicorn | 0.44.0 | ASGI server | Already installed; standard FastAPI deployment |

### Core -- Frontend

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.5 | UI framework | Latest stable; concurrent features, compiler optimizations |
| Vite | 8.0.10 | Build tool | Sub-second HMR; 42KB bundle baseline; deploys to FastAPI static |
| TypeScript | 5.x | Type safety | Catches schema mismatches at compile time |
| Tailwind CSS | 4.2.4 | Styling | Zero runtime CSS; CSS-first config (no tailwind.config.js in v4) |
| shadcn/ui | latest | UI components | Copy-paste components based on Radix; full ownership, zero runtime dep |
| TanStack Query | 5.100.5 | Server state | Auto caching, deduplication, background refetch, withCredentials support |
| axios | 1.15.2 | HTTP client | withCredentials for cookie-based auth; interceptor for 401 handling |
| React Router | 7.14.2 | Client routing | Mature; lazy loading; URL-based state |
| Lucide React | latest | Icons | Tree-shakeable SVG icons; pairs with shadcn/ui |

### Supporting -- Backend

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langgraph-checkpoint-sqlite | 3.0.3 | LangGraph persistence | Replace InMemorySaver in main.py; shares same SQLite file |
| pydantic-settings | 2.x | Config management | Optional refactor of config.py for cleaner env loading |

### Installation

```bash
# Backend additions (to requirements.txt)
pip install sqlalchemy alembic aiosqlite pyjwt bcrypt python-multipart pydantic-settings

# Frontend scaffold (new frontend/ directory)
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite
npm install @tanstack/react-query axios react-router-dom lucide-react
npm install class-variance-authority clsx tailwind-merge
npx shadcn@latest init
npx shadcn@latest add button input card form label separator
```

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| bcrypt (direct) | passlib[bcrypt] | passlib 1.7.4 unmaintained since 2020; incompatible with bcrypt 5.0.0 |
| PyJWT | python-jose | python-jose **archived**. PyJWT is the current standard |
| axios | fetch (native) | axios has withCredentials, interceptors for 401 refresh, cancel tokens |
| shadcn/ui | MUI v7 | MUI is 100-200KB gzipped, harder to customize, CSS-in-JS overhead |
| Tailwind v4 CSS-first | Tailwind v3 JS config | v4 is latest; shadcn/ui v2 supports it; CSS-first is cleaner |

**Version verification [VERIFIED: npm registry / pip index]:**
- All npm versions confirmed via `npm view <package> version` on 2026-04-26
- All PyPI versions confirmed via `pip3 index versions <package>` on 2026-04-26
- All installed versions confirmed via `pip3 show <package>` on 2026-04-26

---

## Architecture Patterns

### System Architecture Diagram

```
[Browser: React SPA]
     |
     | axios withCredentials (cookies auto-sent)
     | POST /auth/login  |  POST /auth/logout  |  GET /auth/me
     v
[FastAPI: Auth Middleware]
     |
     |-- D-01: JWT decode from Authorization header OR cookie (SSE fallback)
     |-- D-03: Depends(get_current_user) + Depends(require_role("admin"))
     |
     v
[FastAPI: Existing Endpoints (now protected)]
     /recruit  /recruit/stream  /upload-resume  /admin/rebuild-index  /health
     |
     |-- D-15: All endpoints async def; SSE with timeout & [DONE]
     |-- D-15: Input validation on all request bodies
     |-- D-16: CORS restricted to specific origins
     |
     v
[LangGraph: SqliteSaver checkpointer]  <--- D-09: replaces InMemorySaver
     |
     v
[SQLite (data/dev.db)]
     |-- users table (D-06)
     |-- LangGraph checkpoint tables (SqliteSaver auto-creates)
```

### Phase 1 File Structure

```
hellojobs/
├── backend/                           # NEW: refactored into backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py                  # MODIFIED: add auth middleware, async endpoints
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── auth.py                # NEW: /auth/login, /auth/logout, /auth/me
│   │   └── deps.py                    # NEW: get_db, get_current_user, require_role
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt.py                     # NEW: encode/decode tokens, token models
│   │   ├── password.py                # NEW: bcrypt hash/verify (NOT passlib)
│   │   └── middleware.py              # NEW: Depends() helpers for auth
│   ├── db/
│   │   ├── __init__.py
│   │   ├── engine.py                  # NEW: async engine + session factory
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── user.py                # NEW: User model (D-06)
│   │   ├── migrations/                # NEW: Alembic
│   │   │   ├── env.py
│   │   │   ├── alembic.ini
│   │   │   └── versions/
│   │   │       └── 001_create_users.py
│   │   └── seed.py                    # NEW: CLI script to create admin user
│   ├── config.py                      # MODIFIED: add DB, JWT, CORS config
│   ├── main.py                        # MODIFIED: InMemorySaver → SqliteSaver
│   └── requirements.txt               # MODIFIED: add sqlalchemy, alembic, etc.
│
├── frontend/                          # NEW: React SPA
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                    # Router setup (D-13)
│   │   ├── api/
│   │   │   └── client.ts             # axios instance with withCredentials
│   │   ├── hooks/
│   │   │   └── useAuth.ts            # login, logout, getCurrentUser
│   │   ├── pages/
│   │   │   └── Login.tsx             # Login form (D-04)
│   │   ├── components/
│   │   │   ├── Layout.tsx            # Sidebar + topbar (D-11)
│   │   │   └── ProtectedRoute.tsx    # Auth guard (D-11)
│   │   ├── stores/
│   │   │   └── authStore.ts          # In-memory JWT + user state (Zustand)
│   │   ├── styles/
│   │   │   └── globals.css           # Tailwind v4 @import "tailwindcss"
│   │   └── lib/
│   │       └── utils.ts              # cn() helper (clsx + tailwind-merge)
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── data/
│   └── dev.db                        # NEW: SQLite database (gitignored)
│
├── config.py                          # KEPT at root for backward compat, delegated to backend/config.py
├── requirements.txt                   # KEPT at root for backward compat
├── .env.example                       # MODIFIED: add JWT_SECRET, DATABASE_URL
└── .gitignore                         # MODIFIED: add data/dev.db, frontend/node_modules, frontend/dist
```

### Pattern 1: JWT Auth with HTTP-Only Cookie

**What:** Access token in memory (React state/context), refresh token in HTTP-only cookie. On page refresh, frontend calls `/auth/me` which reads the refresh token cookie and returns user info. If access token expired, the refresh token is used to issue a new one.

**When to use:** All SPA auth where XSS resistance is required and SSE endpoints must authenticate.

**Example -- FastAPI auth flow [VERIFIED: PyJWT 2.12 docs]:**

```python
# backend/auth/jwt.py
from datetime import datetime, timedelta, timezone
import jwt
from backend.config import JWT_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(user_id: str, role: str) -> str:
    return jwt.encode(
        {
            "sub": user_id,
            "role": role,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        },
        JWT_SECRET,
        algorithm="HS256",
    )

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
```

```python
# backend/auth/password.py -- use bcrypt DIRECTLY, not passlib
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
```

```python
# backend/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from backend.auth.jwt import decode_token
from backend.db.engine import get_session

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials = Depends(bearer_scheme),
    request = None,
):
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # Fallback: read from cookie (for SSE)
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = decode_token(token)
    return payload  # {"sub": user_id, "role": role}

def require_role(required_role: str):
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.get("role") != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return current_user
    return role_checker
```

### Pattern 2: SqliteSaver Checkpoint Persistence

**What:** Replace `InMemorySaver()` with `SqliteSaver` backed by the same SQLite database file. LangGraph checkpoints survive server restarts, enabling interrupted HITL workflows to resume.

**When to use:** Any LangGraph deployment that needs state persistence. SqliteSaver requires no additional infrastructure.

**Example -- SqliteSaver usage [VERIFIED: langgraph-checkpoint-sqlite 3.0.3]:**

```python
# backend/main.py
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

# Sync SqliteSaver (for sync graph.invoke() in executor threads)
sqlite_conn = sqlite3.connect("data/dev.db", check_same_thread=False)
checkpointer = SqliteSaver(sqlite_conn)

# Also available: async context manager for async execution
# from langgraph.checkpoint.sqlite import SqliteSaver
# async with SqliteSaver.from_conn_string("sqlite+aiosqlite:///data/dev.db") as saver:
#     graph = builder.compile(checkpointer=saver, ...)

def build_graph(use_hitl: bool = False):
    builder = StateGraph(RecruitmentState)
    # ... nodes and edges ...
    interrupt_before = ["reviewer_agent"] if use_hitl else []
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
    )
```

**Important:** SqliteSaver auto-creates its own internal tables (`checkpoints`, `writes`, `checkpoint_blobs`, `checkpoint_writes`). These coexist with the application's `users` table in the same SQLite file.

### Pattern 3: Tailwind v4 CSS-First Configuration

**What:** Tailwind v4 uses CSS-based configuration instead of `tailwind.config.js`. The `@import "tailwindcss"` at the top of the CSS file is the only setup needed.

**When to use:** Always for Tailwind v4. The `tailwind-merge` utility (`cn()` helper) still works identically.

**Example [VERIFIED: npm registry tailwindcss@4.2.4]:**

```css
/* frontend/src/styles/globals.css */
@import "tailwindcss";

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    /* shadcn/ui CSS variables go here */
  }
}
```

```typescript
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
  },
});
```

**Vite proxy config:** The Vite dev server proxies `/api` requests to FastAPI on port 8000, avoiding CORS issues during development. In production, FastAPI serves the built `dist/` files and handles API requests directly.

### Pattern 4: SSE Timeout and Disconnect Handling

**What:** The SSE streaming endpoint currently has no timeout and does not detect client disconnect. Adding both is required for stability.

**Example [VERIFIED: FastAPI docs]:**

```python
async def _stream_recruitment(user_input: str, resume_text: str, request: Request):
    # ...setup...
    try:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        # Set a 120-second timeout on graph execution
        TIMEOUT_SECONDS = 120

        async def run_with_timeout():
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _run_graph),
                timeout=TIMEOUT_SECONDS,
            )

        # Check for client disconnect
        stream_task = asyncio.create_task(run_with_timeout())

        while True:
            done, pending = await asyncio.wait(
                [stream_task, asyncio.ensure_future(queue.get())],
                return_when=asyncio.FIRST_COMPLETED,
            )
            # Check disconnect
            if await request.is_disconnected():
                stream_task.cancel()
                break

            item = queue.get_nowait() if not stream_task.done() else None
            # ...process item...

        # Always send [DONE] on terminal paths
        yield _sse_event("done", {})

    except asyncio.TimeoutError:
        yield _sse_event("error", {"message": "请求超时，请稍后重试"})
        yield _sse_event("done", {})
    except Exception as e:
        yield _sse_event("error", {"message": str(e)})
        yield _sse_event("done", {})
```

### Anti-Patterns to Avoid

- **Synchronous `def` endpoints:** All existing `/recruit`, `/recruit/hitl/*`, `/health`, `/admin/rebuild-index` are `def` and block the event loop. Convert to `async def` with `asyncio.to_thread()` for CPU-bound work.
- **Hardcoded thread_id:** `thread_id = "hitl-thread"` in `server.py:89,93`. Two concurrent HITL users overwrite each other's state. Must generate UUID per session.
- **`passlib` usage:** passlib 1.7.4 is incompatible with bcrypt 5.0.0 (breaking API change). Use `bcrypt` directly.
- **No `[DONE]` sentinel:** SSE endpoint does not send `[DONE]` on error paths, leaving frontend waiting indefinitely.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom hash function | `bcrypt` (direct) | Industry-standard; handles salt, rounds, timing attack resistance |
| JWT creation/verification | Custom token format | `PyJWT` | Handles expiration, signature validation, algorithm selection |
| DB migrations | Manual ALTER TABLE | `Alembic` | Auto-generates migrations from model changes; rollback support |
| API state management | Custom fetch + cache | `TanStack Query` | Caching, deduplication, background refetch, stale-while-revalidate |
| HTTP client with cookies | Raw fetch with cookie headers | `axios` with `withCredentials` | Auto-sends cookies; 401 interceptor for token refresh |
| UI components | Hand-build accessible button/input/card | `shadcn/ui` | Radix-based accessible primitives; full ownership via copy-paste |
| LangGraph state persistence | Custom JSON checkpoint | `SqliteSaver` | LangGraph-native; no infrastructure; survives restarts |

**Key insight:** Every item in the "Don't Hand-Roll" table represents a domain where correctness matters more than simplicity. Password hashing, JWT, and SQL migrations have well-established, battle-tested libraries. Custom implementations in these areas are a common source of security vulnerabilities and data corruption bugs.

---

## Common Pitfalls

### Pitfall 1: passlib 1.7.4 + bcrypt 5.0.0 Incompatibility

**What goes wrong:** passlib 1.7.4 cannot use bcrypt 5.0.0 as its backend. The bcrypt library removed `__about__` module and changed how it handles passwords >72 bytes. passlib has been unmaintained since 2020.

**Why it happens:** Both `passlib` and `bcrypt` are in installed packages. When passlib tries to initialize its bcrypt backend, it fails with `AttributeError: module 'bcrypt' has no attribute '__about__'`, then falls through to a fallback that produces `ValueError: password cannot be longer than 72 bytes`.

**How to avoid:** Use `bcrypt` directly. The `bcrypt` API is simple: `bcrypt.hashpw(pw.encode(), bcrypt.gensalt())` and `bcrypt.checkpw(pw.encode(), hash.encode())`.

**How to fix if already using passlib:** Either (a) replace passlib calls with direct bcrypt calls, or (b) pin `bcrypt==4.0.1` (last version compatible with passlib 1.7.4).

### Pitfall 2: Sync `def` Endpoints Blocking the Event Loop

**What goes wrong:** Endpoints like `/recruit`, `/recruit/hitl/start`, `/recruit/hitl/resume`, `/health`, and `/admin/rebuild-index` are synchronous `def` handlers. LangGraph's `graph.invoke()` in these handlers blocks the entire async event loop, starving all other requests.

**Why it happens:** FastAPI runs sync `def` handlers in a thread pool, but `graph.invoke()` blocks that thread for 30-120 seconds. With a single uvicorn worker, one blocking request makes `/health` and all other endpoints unresponsive.

**How to avoid:** Convert all handlers to `async def`. For long-running or CPU-bound work (LangGraph invoke, FAISS rebuild), use `asyncio.to_thread()` to offload to a dedicated thread pool. The SSE streaming endpoint is already `async def` but runs `_run_graph` in the default executor with no timeout -- add proper timeout and thread pool isolation.

### Pitfall 3: SSE No Timeout and No Client Disconnect Detection

**What goes wrong:** `_stream_recruitment` runs `loop.run_in_executor(None, _run_graph)` without a timeout. If the LLM hangs or the graph deadlocks, the SSE connection stays open indefinitely. No client disconnect detection means cancelled browser tabs leave orphaned executor threads running.

**Why it happens:** The existing codebase was designed for single-user CLI or demo use. SSE was added as a streaming wrapper but not hardened for production.

**How to avoid:** (1) Add `asyncio.wait_for()` with a 120-second timeout around the executor. (2) Check `request.is_disconnected()` periodically and cancel the executor future on disconnect. (3) Always yield `data: [DONE]\n\n` on ALL terminal paths (happy path, exception, timeout). (4) On the frontend, synthesize a done event when `onclose` fires without receiving `[DONE]`.

### Pitfall 4: Hardcoded HITL Thread ID Causes Session Collisions

**What goes wrong:** `server.py:89,93` defaults `thread_id` to `"hitl-thread"`. Two HR managers using the system simultaneously overwrite each other's HITL workflow state.

**Why it happens:** The HITL endpoint was designed as a demo. Hardcoded thread ID is the fastest path to "it works for one user."

**How to avoid:** Generate a UUID on every new HITL session. Return the thread_id in the start response. The frontend stores it and sends it with resume requests. The same applies to `_stream_recruitment` which already generates UUIDs (`thread_id: f"stream-{uuid4().hex}"`) -- this pattern is correct and should be replicated in HITL.

### Pitfall 5: CORS `allow_origins=["*"]` with Credentials

**What goes wrong:** Current `allow_origins=["*"]` combined with the new cookie-based auth (which requires `credentials=True` in CORS) will fail. The browser spec prohibits `allow_credentials: true` with `allow_origins: ["*"]`.

**Why it happens:** The wildcard CORS config was quick setup for development. Adding cookie auth requires explicit origin lists.

**How to avoid:** D-16 already specifies "CORS configured for frontend dev and production domains, credentials enabled." Set `allow_origins=["http://localhost:5173", "https://yourdomain.com"]` and `allow_credentials=True`. Use different CORS configs for development vs production.

### Warning Signs Checklist

- [ ] `passlib.context.CryptContext` anywhere in auth code (should be direct `bcrypt`)
- [ ] `def recruit(` (sync handler) in server.py (should be `async def`)
- [ ] No `asyncio.wait_for` around `run_in_executor` in `_stream_recruitment`
- [ ] `allow_origins=["*"]` in CORS middleware (must be explicit list with credentials)
- [ ] `thread_id = "hitl-thread"` hardcoded (should be UUID per session)
- [ ] `localStorage.setItem('token')` in frontend (must be HttpOnly cookie)
- [ ] No `[DONE]` sentinel in SSE streaming
- [ ] `tailwind.config.js` in frontend (Tailwind v4 uses CSS config)

---

## Code Examples

### Backend SQLAlchemy Async Engine [VERIFIED: SQLAlchemy 2.0 docs]

```python
# backend/db/engine.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./data/dev.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

### Backend User Model [VERIFIED: SQLAlchemy 2.0 docs]

```python
# backend/db/models/user.py
from sqlalchemy import Column, Integer, String, Enum, DateTime, func
from backend.db.engine import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring-manager"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.RECRUITER)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
```

### Backend Auth Endpoints [VERIFIED: FastAPI docs, PyJWT 2.12 docs]

```python
# backend/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from backend.auth.jwt import create_access_token, create_refresh_token, decode_token
from backend.auth.password import verify_password
from backend.db.models.user import User
from backend.db.engine import get_session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

@router.post("/login")
async def login(request: LoginRequest, response: Response, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id), user.role.value)

    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,      # False in dev if no HTTPS
        samesite="lax",
        max_age=7 * 24 * 3600,  # 7 days
        path="/auth",
    )

    return LoginResponse(
        access_token=access_token,
        user={"id": user.id, "username": user.username, "role": user.role.value},
    )

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token", path="/auth")
    return {"message": "已登出"}

@router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    return current_user
```

### Frontend Axios Instance with Interceptor [VERIFIED: axios 1.x docs]

```typescript
// frontend/src/api/client.ts
import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

// Response interceptor for 401 handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login, clear auth state
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Frontend Login Page (React + shadcn/ui)

```typescript
// frontend/src/pages/Login.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import apiClient from "../api/client";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await apiClient.post("/auth/login", { username, password });
      // Store access token in memory (context/state)
      // Server set refresh_token as HttpOnly cookie
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "登录失败");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Card className="w-96">
        <CardHeader>
          <CardTitle>HR 智能招聘系统</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input placeholder="用户名" value={username} onChange={(e) => setUsername(e.target.value)} />
            <Input type="password" placeholder="密码" value={password} onChange={(e) => setPassword(e.target.value)} />
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full">登录</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Frontend Protected Route Guard

```typescript
// frontend/src/components/ProtectedRoute.tsx
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function ProtectedRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) return <div>加载中...</div>;
  if (!user) return <Navigate to="/login" replace />;

  return <Outlet />;
}
```

### CLI Seed Script

```python
# backend/db/seed.py
"""Create initial admin user. Usage: python -m backend.db.seed"""

import asyncio
import sys
from sqlalchemy import select
from backend.db.engine import engine, async_session, Base
from backend.db.models.user import User, UserRole
from backend.auth.password import hash_password


async def seed(username: str, password: str, role: UserRole = UserRole.ADMIN):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            print(f"User '{username}' already exists, skipping.")
            return

        user = User(
            username=username,
            hashed_password=hash_password(password),
            role=role,
        )
        session.add(user)
        await session.commit()
        print(f"Admin user '{username}' created successfully.")


if __name__ == "__main__":
    import os
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD") or sys.argv[1] if len(sys.argv) > 1 else None
    if not password:
        print("Usage: ADMIN_PASSWORD=<pw> python -m backend.db.seed")
        print("   or: python -m backend.db.seed <password>")
        sys.exit(1)
    asyncio.run(seed(username, password))
```

---

## Runtime State Inventory

> Not applicable -- Phase 1 is a greenfield addition with a new frontend and new backend modules. No renaming or migration of existing state is required. The existing `data/` directory contents (FAISS index, ChromaDB, JSON memory, eval datasets) are untouched by Phase 1.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend scaffold | Yes | 22.22.1 | -- |
| npm | Frontend scaffold | Yes | 10.9.4 | -- |
| Python 3 | Backend | Yes | 3.12.0 | -- |
| pip | Backend packages | Yes | 26.0.1 | -- |
| FastAPI | API framework | Yes | 0.135.3 | -- |
| SQLAlchemy 2 | ORM | Yes | 2.0.49 | -- |
| Alembic | DB migrations | Yes | 1.18.4 | -- |
| aiosqlite | Async SQLite driver | Yes | 0.22.1 | -- |
| PyJWT | JWT tokens | Yes | 2.12.1 | -- |
| bcrypt | Password hashing | Yes | 5.0.0 | -- |
| passlib | (unused) | Yes | 1.7.4 | **Incompatible with bcrypt 5.0.0** |
| langgraph | Agent workflow | Yes | 1.1.6 | -- |
| langgraph-checkpoint-sqlite | SqliteSaver | Yes | 3.0.3 | -- |
| python-multipart | Form data | Yes | 0.0.26 | -- |
| Uvicorn | ASGI server | Yes | 0.44.0 | -- |

**Missing dependencies with no fallback:** None -- all required packages are either installed or available via npm/PyPI.

**Missing dependencies with fallback:**
- passlib 1.7.4: Do not use. Replace with direct `bcrypt` 5.0.0 calls (D-02 needs user confirmation).

---

## Validation Architecture

> `workflow.nyquist_validation` is enabled (`true` in `.planning/config.json`).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (needs install) |
| Config file | none -- set up in Phase 1 |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| AUTH-01 | Login with valid credentials returns JWT + cookie | integration | `pytest tests/test_auth.py::test_login_success -x` | Needs Wave 0 |
| AUTH-01 | Login with wrong password returns 401 | integration | `pytest tests/test_auth.py::test_login_wrong_password -x` | Needs Wave 0 |
| AUTH-02 | Protected endpoint returns 403 for wrong role | integration | `pytest tests/test_auth.py::test_role_check -x` | Needs Wave 0 |
| AUTH-03 | /auth/me returns user from cookie session | integration | `pytest tests/test_auth.py::test_session_persistence -x` | Needs Wave 0 |
| AUTH-03 | Logout clears cookie and invalidates session | integration | `pytest tests/test_auth.py::test_logout -x` | Needs Wave 0 |
| AUTH-01/03 | Unauthenticated request returns 401 | integration | `pytest tests/test_auth.py::test_unauthenticated -x` | Needs Wave 0 |
| D-09 | SqliteSaver persists checkpoint across restart | integration | `pytest tests/test_checkpointer.py -x` | Needs Wave 0 |
| D-15 | SSE endpoint sends [DONE] on timeout | integration | `pytest tests/test_sse.py::test_timeout_sentinel -x` | Needs Wave 0 |
| D-15 | SSE endpoint handles client disconnect | integration | `pytest tests/test_sse.py::test_disconnect -x` | Needs Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_auth.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_auth.py` -- auth login/logout/role tests
- [ ] `tests/test_checkpointer.py` -- SqliteSaver persistence test
- [ ] `tests/test_sse.py` -- SSE timeout and disconnect tests
- [ ] `tests/conftest.py` -- async test fixtures (test DB, test client)
- [ ] pytest install: `pip install pytest pytest-asyncio httpx`

---

## Security Domain

> `security_enforcement` is enabled by default (absent from config.json).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | bcrypt password hashing; JWT with HS256; refresh token rotation |
| V3 Session Management | yes | HTTP-only cookies; access token in memory; refresh token rotation |
| V4 Access Control | yes | JWT role field; Depends(require_role()) middleware |
| V5 Input Validation | yes | Pydantic models for all request bodies; length limits on user_input |
| V6 Cryptography | yes | PyJWT HS256; bcrypt for passwords (never hand-roll) |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| JWT in localStorage (XSS theft) | Information Disclosure | HTTP-only cookies (D-01) -- JS cannot read them |
| Brute-force login | Tampering | Short access token TTL; input rate limiting (slowapi in later phases) |
| Cookie theft via XSS | Elevation of Privilege | HttpOnly + Secure + SameSite=Strict prevents JS access |
| CSRF on auth endpoints | Tampering | SameSite=Lax on auth cookies; CORS restricted to specific origins |
| Leaked JWT_SECRET (short key) | Tampering | PyJWT warns if key < 32 bytes; .env.example should document 32+ byte key |
| Password >72 bytes (bcrypt limit) | Denial of Service | Hash the password first with SHA-256 before bcrypt, or enforce max length |
| LLM injection via login fields | Tampering | Pydantic validation strips/fails on unexpected input; rate limiting |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | User will accept replacing `passlib(bcrypt)` with direct `bcrypt` calls | Common Pitfalls / Standard Stack | MEDIUM: D-02 says "passlib(bcrypt)" but passlib is incompatible with installed bcrypt 5.0.0. If user insists on passlib, must pin bcrypt==4.0.1 |
| A2 | SqliteSaver sync constructor with raw sqlite3.Connection is the correct API for current sync graph.invoke() | Architecture Patterns | LOW: The sync approach matches existing sync graph execution pattern. Alternative is async context manager with `from_conn_string` |
| A3 | Vite dev server proxy config for `/api` is the preferred dev workflow | Architecture Patterns | LOW: Could also use CORS + direct FastAPI URL. Proxy is simpler (no CORS in dev) |
| A4 | Tailwind v4 CSS-first config works with current shadcn/ui init | Standard Stack | LOW: shadcn/ui v2 supports Tailwind v4. If user has older shadcn, may need Tailwind v3 |

---

## Open Questions

1. **passlib replacement confirmation**
   - What we know: `passlib==1.7.4` is incompatible with `bcrypt==5.0.0`. D-02 says passlib(bcrypt).
   - What's unclear: Whether the user explicitly prefers passlib or just picked a well-known combination.
   - Recommendation: Present the incompatibility evidence to the user and recommend switching to direct `bcrypt` calls. Simple API: `bcrypt.hashpw(pw.encode(), bcrypt.gensalt())`.

2. **Shadcn/ui version and Tailwind v4 compatibility**
   - What we know: `tailwindcss@4.2.4` is installed. Tailwind v4 uses CSS-first config. shadcn/ui v2 supports this.
   - What's unclear: Whether running `npx shadcn@latest init` will correctly detect Tailwind v4 and generate proper config.
   - Recommendation: Run `npx shadcn@latest init` in a temporary directory first to verify compatibility, or check shadcn/ui docs for Tailwind v4 setup steps.

3. **SqliteSaver file path convention**
   - What we know: `data/dev.db` is the planned database file path.
   - What's unclear: Whether SqliteSaver should use the same file or a separate `data/checkpoints.db` to keep checkpoint tables separate from application tables.
   - Recommendation: Use the same file (D-09 says "reusing the same SQLite file"). Both tables coexist in SQLite namespaces.

4. **JWT_SECRET key management**
   - What we know: PyJWT requires minimum 32-byte key for HS256. Key must come from env var.
   - What's unclear: Where to generate and document the key generation command.
   - Recommendation: Add `JWT_SECRET` to `.env.example` with a generation command comment: `# Generate: python -c "import secrets; print(secrets.token_hex(32))"`

---

## Sources

### Primary (HIGH confidence)

| Source | What Was Verified |
|--------|-------------------|
| [VERIFIED: npm registry] | react@19.2.5, vite@8.0.10, tailwindcss@4.2.4, @tanstack/react-query@5.100.5, axios@1.15.2, react-router-dom@7.14.2 |
| [VERIFIED: pip index] | pyjwt@2.12.1, passlib@1.7.4, bcrypt@5.0.0, sqlalchemy@2.0.49, alembic@1.18.4, aiosqlite@0.22.1, langgraph-checkpoint-sqlite@3.0.3, python-multipart@0.0.26 |
| [VERIFIED: pip show installed] | FastAPI 0.135.3, Uvicorn 0.44.0, SQLAlchemy 2.0.49, PyJWT 2.12.1, bcrypt 5.0.0, passlib 1.7.4, langgraph 1.1.6, langgraph-checkpoint-sqlite 3.0.3 |
| [VERIFIED: runtime check] | SqliteSaver`from_conn_string` is sync context manager; sync constructor accepts `sqlite3.Connection` |
| [VERIFIED: runtime check] | passlib 1.7.4 fails with bcrypt 5.0.0 (`AttributeError: module 'bcrypt' has no attribute '__about__'`) |
| [VERIFIED: runtime check] | bcrypt 5.0.0 direct API works: `hashpw()` and `checkpw()` |
| [VERIFIED: runtime check] | aiosqlite 0.22.1 importable; SQLAlchemy 2.0.49 async engine works |
| [VERIFIED: existing codebase] | `main.py:70` uses `InMemorySaver()`, `server.py:35` has `allow_origins=["*"]`, `server.py:68,98,140` sync `def` endpoints, `server.py:89,93` hardcoded `thread_id="hitl-thread"` |
| [VERIFIED: PyJWT docs] | `jwt.encode()`/`jwt.decode()` API; HS256; exp claim; sub claim |
| [VERIFIED: FastAPI docs] | CORS middleware, `StreamingResponse`, `Depends()`, File/UploadFile, HTTPException |
| [VERIFIED: SQLAlchemy 2.0 docs] | `create_async_engine`, `async_sessionmaker`, `DeclarativeBase`, `Column`, `Enum`, `select()` |

### Secondary (MEDIUM confidence)

| Source | What Was Verified |
|--------|-------------------|
| [CITED: langgraph docs] | SqliteSaver persistence pattern; context manager API |
| [CITED: axios docs] | withCredentials for cookie-based auth; response interceptors for 401 handling |
| [CITED: TanStack Query docs] | QueryClient setup; useMutation for login; useQuery for /auth/me |
| [CITED: shadcn/ui docs] | Copy-paste component model; Tailwind v4 CSS variable config |
| [CITED: stack research](.planning/research/STACK.md) | Verified stack versions; don't-hand-roll recommendations |
| [CITED: architecture research](.planning/research/ARCHITECTURE.md) | File structure; auth flow; SSE pattern |
| [CITED: pitfalls research](.planning/research/PITFALLS.md) | passlib/bcrypt issue; SSE timeout; thread_id collision |

### Tertiary (LOW confidence)

None -- all findings are based on verified runtime checks, registry lookups, or the existing codebase audit.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages verified via npm/PyPI registry and runtime import checks
- Architecture: HIGH -- patterns verified against FastAPI docs, SQLAlchemy docs, langgraph docs
- Pitfalls: HIGH -- passlib incompatibility confirmed via runtime test; SSE/server issues verified against existing codebase
- passlib recommendation: MEDIUM -- user decision D-02 says passlib but runtime proves incompatibility. Needs user confirmation to switch to direct bcrypt.

**Research date:** 2026-04-26
**Valid until:** 2026-05-26 (30 days for stable packages; 7 days for fast-moving tools like shadcn/ui)
