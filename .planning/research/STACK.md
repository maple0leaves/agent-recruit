# Stack Research

**Domain:** Full-stack frontend for AI recruitment system (HR dashboard over Python/FastAPI agent backend)
**Researched:** 2026-04-26
**Confidence:** HIGH (verified versions match current npm/PyPI releases)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **React** | 19.x | UI framework | React Compiler auto-memoizes re-renders; largest ecosystem and hiring pool; natural fit for data-heavy dashboards; React 19's concurrent features handle SSE token streams without blocking UI |
| **Vite** | 8.x | Build tool / dev server | Sub-second HMR, ~42KB bundle baseline, simpler than Next.js for internal tools (no SSR needed), deploys to static CDN or Nginx |
| **TypeScript** | 5.x | Type safety | Enforces Pydantic-like contracts on frontend; catches schema mismatches between FastAPI response models and UI code at compile time |
| **Tailwind CSS** | 4.x | Styling | Zero-runtime CSS (no CSS-in-JS overhead), utility-first makes data-dense layouts fast to build, tree-shakes unused styles to <10KB in production |
| **shadcn/ui** | latest (copy-paste) | UI component library | Based on Radix UI primitives (AAA accessibility) + Tailwind; components copied into source for full ownership, zero runtime dependency, no version lock-in; includes table, dialog, form, select, dropdown, toast, and all dashboard primitives |
| **TanStack Query** | 5.x | Server state management | Eliminates manual API state boilerplate; handles caching, deduplication, background refetch, pagination, optimistic updates automatically; separates server data from UI state entirely |
| **TanStack Table** | 8.x | Data tables | Headless table with server-side sorting/filtering/pagination; compatible with React 19; no DOM assumptions — works with any styling approach including shadcn/ui |
| **React Hook Form + Zod** | 7.x / 4.x | Form state + validation | Minimal re-renders (uncontrolled inputs by default), type-safe validation with Zod schemas that mirror Pydantic models; zero-dependency bundle impact |
| **Zustand** | 5.x | Client UI state | ~3KB gzipped, no providers, no boilerplate; fine-grained subscriptions via selectors prevent cascade re-renders; replaces 90% of Redux use cases |
| **React Router** | 7.x | Client-side routing | Most mature React router; lazy-loading per route for code splitting; URL-based state for table filters/sorts/pagination (bookmarkable) |
| **Vite PWA Plugin** | latest | Offline/progressive | Optional: enables service worker for caching static assets; useful if HR users access dashboard on unreliable networks |

### Backend Additions (server-side, to the existing FastAPI stack)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **PyJWT** | 2.12.x | JWT token creation/verification | Pure Python, actively maintained, supports RS256/HS256; used in FastAPI Depends() auth middleware |
| **passlib[bcrypt]** | 1.7.x + bcrypt 5.x | Password hashing | Industry standard for credential storage; bcrypt handles Chinese character passwords correctly (UTF-8 safe) |
| **python-multipart** | 0.0.26 | File upload parsing | FastAPI requires this for form-data uploads (resume uploads from HR dashboard) |
| **ReportLab** | 4.4.x | Server-side PDF generation | Mature (20+ years), handles CJK fonts natively, supports table layouts and embedded charts; generates PDF recruitment reports server-side so frontend just downloads a file |
| **openpyxl** | 3.1.x | Server-side Excel generation | Best-in-class .xlsx writer for Python; handles styled tables, merged cells, column widths, data validation; frontend triggers export and receives .xlsx file |
| **slowapi** | 0.1.x | Rate limiting | Protects auth endpoints and report generation from abuse; integrates as FastAPI middleware |

### SSE Streaming Layer (bridging frontend and existing backend)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **fetch + ReadableStream** | Web API (native) | SSE stream consumption | No library needed — native `response.body.getReader()` reads SSE events; lighter than EventSource (which only supports GET) and EventSource (which doesn't support POST) |
| **AbortController** | Web API (native) | Stream cancellation | Allows HR users to cancel long-running agent workflows; hooks into fetch's signal parameter |

The existing backend already sends SSE events correctly (see `api/server.py`). The frontend only needs a thin custom hook (`useSSEStream`) to consume them.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **Biome** | Linting + formatting | Faster than ESLint + Prettier combined (Rust-based); single tool for both lint and format |
| **Husky + lint-staged** | Pre-commit hooks | Runs Biome on staged files before commit; prevents formatting drift |
| **@vitejs/plugin-react-swc** | Fast refresh | SWC-based compilation (Rust) is 10-20x faster than Babel-based alternatives |
| **Lucide React** | Icons | Tree-shakeable SVG icons, pairs with shadcn/ui (which uses Lucide by default); 1000+ icons for HR dashboard (users, files, check, x, download, upload, search, filter) |

## Installation

```bash
# Frontend scaffold
npm create vite@latest frontend -- --template react-ts
cd frontend

# Core UI + styling
npm install tailwindcss @tailwindcss/vite
npm install lucide-react class-variance-authority clsx tailwind-merge
npx shadcn@latest init
npx shadcn@latest add button input table dialog toast form select dropdown-menu tabs card badge separator

# Data management
npm install @tanstack/react-query @tanstack/react-table zustand

# Forms + validation
npm install react-hook-form @hookform/resolvers zod

# Routing
npm install react-router-dom

# Icons
npm install lucide-react

# Dev dependencies
npm install -D @biomejs/biome husky lint-staged @vitejs/plugin-react-swc

# Backend additions (in existing requirements.txt)
pip install pyjwt passlib[bcrypt] python-multipart reportlab openpyxl slowapi
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| React 19 + Vite | **Next.js 15/16** | When SEO matters (this HR tool is 100% behind auth, so it does not) |
| shadcn/ui + Tailwind | **MUI v7** | When you need an opinionated design system with less flexibility; MUI is heavier (100-200KB gzipped) and harder to customize |
| Zustand + TanStack Query | **Redux Toolkit + RTK Query** | When you have complex interdependent state that benefits from Redux DevTools; rare for dashboards, overkill here |
| Server-side PDF (ReportLab) | **Client-side PDF (react-pdf)** | When PDFs are small and simple; but react-pdf has poor CJK support and blocks the main thread |
| fetch + ReadableStream | **EventSource API** | When you use GET requests for streaming (EventSource does not support POST, which agent streaming endpoints require) |
| React Hook Form + Zod | **Formik + Yup** | When you have deeply nested dynamic forms; Formik re-renders on every keystroke, RHF is more performant |
| Vite SPA | **TanStack Start** | When you want SSR but not Next.js; TanStack Start is newer and less proven for production |
| PyJWT | **python-jose** | python-jose was archived. PyJWT is the current standard for JWT in Python |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **localStorage for auth tokens** | XSS-vulnerable; any injected script can steal tokens and impersonate users | HTTP-only Secure cookies (JS cannot read them) |
| **Next.js** | SSR adds complexity (server/client boundaries, caching, deployment) with zero benefit for an internal auth-gated tool | Vite + React SPA |
| **Redux Toolkit** | Boilerplate-heavy; Zustand + TanStack Query covers 90% of use cases with 10% of the code | Zustand + TanStack Query |
| **Material UI (MUI)** | CSS-in-JS (Emotion) adds runtime overhead; Material Design opinions clash with admin dashboard needs; bundle is 100-200KB gzipped | shadcn/ui + Tailwind |
| **EventSource (browser API)** | Only supports GET requests; agent streaming uses POST with JSON payloads | fetch + ReadableStream |
| **Client-side PDF generation** | React-pdf has poor CJK (Chinese) font rendering — critical for Chinese resume reports; blocks main thread on large reports | Server-side ReportLab |
| **axios for SSE streaming** | Axios does not natively support streaming response bodies in the same way as fetch's ReadableStream | fetch ReadableStream API (native) |
| **Ant Design** | Heaviest bundle (150-300KB); design language feels dated; hard to customize without overriding CSS-in-JS | shadcn/ui for most cases, MUI Data Grid only if needing enterprise-grade table (and only import the table module) |
| **Custom data fetching hooks** | Rolling your own fetch/loading/error/cache logic duplicates TanStack Query's features with more bugs | @tanstack/react-query |
| **Styled Components / Emotion** | Runtime CSS-in-JS conflicts with React Server Components and adds bundle overhead; harder to debug | Tailwind CSS (zero runtime) |
| **Sentry** (not needed yet) | Premature observability for an internal tool; adds bundle weight and noise | Start with console.error + error boundary logging; add Sentry only when in production with real users |

## Stack Patterns by Variant

**If the team has Vue experience and prefers it over React:**
- Use Vue 3.5+ with Vite instead of React 19 + Vite
- Replace TanStack Table with vue-good-table or vue-tables-2
- Replace Zustand with Pinia
- Keep everything else the same (Tailwind, shadcn-vue, server-side auth, SSE streaming pattern)
- Note: Smaller ecosystem and hiring pool; verify shadcn-vue component parity first

**If SSO/OIDC is required by enterprise IT (e.g., Okta, Azure AD):**
- Add a managed auth provider (Clerk, Auth0, or WorkOS) OR self-hosted Keycloak
- Replace manual PyJWT + passlib setup with the provider's SDK
- Pattern stays the same: HTTP-only cookies, FastAPI middleware
- Only invest in SSO when enterprise demands it — start with simple JWT auth

**If the HR user base is <50 concurrent users (the likely case):**
- Skip performance optimization for bundle splitting — Vite's default code splitting is fine
- Skip PWA/service worker setup
- No need for rate limiting on export endpoints (remove slowapi)
- The simplest path wins

**If the system needs to handle >10,000 candidates (future scale):**
- Move server-side PDF/Excel generation to a background task queue (Celery or Arq)
- Add Redis caching layer for generated reports
- Implement chunked streaming for large Excel downloads
- This is a future concern — start simple

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| react@19.x | @tanstack/react-query@5.x | Fully compatible; no breaking changes |
| react@19.x | react-hook-form@7.x | Verified compatibility |
| react@19.x | @tanstack/react-table@8.x | Headless utility, no React version dependency |
| react@19.x | react-router-dom@7.x | Fully compatible |
| react@19.x | zustand@5.x | Compatible; zustand v5 uses `create` API (v4's `create` still works but v5 has cleaner TypeScript) |
| vite@8.x | @vitejs/plugin-react-swc | Latest versions compatible |
| tailwindcss@4.x | shadcn/ui | shadcn/ui v2 (post-2025) uses Tailwind v4; verify component generator version |
| @tanstack/react-table@8.x | @tanstack/react-query@5.x | Separate concerns, zero coupling |
| openpyxl@3.1.x | Python 3.12 | Fully compatible |
| reportlab@4.4.x | Python 3.12 | Fully compatible; CJK font registration requires manual font file setup |
| pyjwt@2.12.x | Python 3.12 | Fully compatible; use `PyJWT` library, not deprecated `python-jose` |

### Critical Compatibility Notes

1. **shadcn/ui init requires a fresh Vite project** — `npx shadcn@latest init` will detect Vite and configure paths automatically. Do not use create-react-app (deprecated) or CRA-based templates.

2. **Tailwind v4 CSS-first config**: Tailwind v4 uses CSS-based configuration (`@import "tailwindcss"`) instead of `tailwind.config.js`. The `tailwind-merge` utility (`cn()` helper) still works identically.

3. **Zod schemas should mirror Pydantic models**: Keep a shared type contract between frontend Zod schemas and backend Pydantic models. Manually maintained — no automated bridge (pydantic-to-zod generators exist but produce bloated schemas). For this project's ~15 models, manual mirroring is cleaner.

4. **ReportLab CJK fonts**: ReportLab does not bundle CJK fonts. You must register them:
   ```python
   from reportlab.pdfbase import pdfmetrics
   from reportlab.pdfbase.ttfonts import TTFont
   pdfmetrics.registerFont(TTFont('NotoSansSC', 'NotoSansSC-Regular.ttf'))
   ```
   Download Noto Sans SC (or a system CJK font) and register before rendering.

## Sources

- [npm registry] — Zustand v5.0.12, TanStack Query v5.100.5, TanStack Table v8.21.3, React Hook Form v7.74.0, Zod v4.3.6, Vite v8.0.10, Tailwind v4.2.4, React Router v7.14.2 (confirme via `npm view`)
- [PyPI registry] — ReportLab v4.4.10, openpyxl v3.1.5, PyJWT v2.12.1, passlib v1.7.4, bcrypt v5.0.0, slowapi v0.1.9, python-multipart v0.0.26 (confirmed via `pip index versions`)
- [Dev.to - Zustand + TanStack Query replaced 90% of Redux](https://dev.to/devforgedev/you-dont-need-redux-zustand-tanstack-query-replaced-90-of-my-state-management-2ggi) — State management pattern validation (MEDIUM)
- [DesignRevision - Vite vs Next.js (2026)](https://designrevision.com/blog/vite-vs-nextjs) — SPA vs SSR decision framework (MEDIUM)
- [Dev.to - Common Mistakes in React Admin Dashboards](https://dev.to/vaibhavg/common-mistakes-in-react-admin-dashboards-and-how-to-avoid-them-1i70) — Anti-pattern validation (MEDIUM)
- [Dev.to - Building AI Interfaces: Why We Went All-In on TanStack Ecosystem](https://ertyurk.com/posts/building-ai-interfaces-why-we-went-all-in-on-the-tanstack-ecosystem/) — SSE streaming with TanStack (MEDIUM)
- [C# Corner - State Management in React (2026)](https://www.c-sharpcorner.com/article/state-management-in-react-2026-best-practices-tools-real-world-patterns/) — 4-layer state management model (LOW — single source)
- [CloudThat - Stateless Authentication using JWT and Secure Cookies](https://www.cloudthat.com/resources/blog/stateless-authentication-in-react-using-jwt-and-secure-cookies) — Auth cookie pattern (MEDIUM)
- [OneUptime - FastAPI Authentication Middleware](https://OneUptime.com/blog/post/2026-01-25-fastapi-authentication-middleware/view) — FastAPI Depends() auth pattern (MEDIUM)
- [StackOverflow - FastAPI Excel download streaming](https://stackoverflow.com/questions/78980589) — openpyxl + FastAPI StreamingResponse pattern (MEDIUM)
- [Dev.to - PDF Generation in Python (FastAPI + DocuForge)](https://dev.to/yoshyaes/pdf-generation-in-python-fastapi-docuforge-39le) — Server-side PDF pattern (LOW)
- [CSDN - 前端框架技术对比与选型指南 (2026)](https://wenku.csdn.net/doc/5ypqtkvrqviz) — React/Vue/Angular 2026 comparison (LOW)
- [GitHub Project - truffle-ai/dexto SSE state management patterns](https://deepwiki.com/truffle-ai/dexto/10.4-state-management-and-real-time-updates) — Production example of TanStack Query + Zustand + SSE (MEDIUM)

---
*Stack research for: HR recruitment dashboard frontend over FastAPI agent backend*
*Researched: 2026-04-26*
