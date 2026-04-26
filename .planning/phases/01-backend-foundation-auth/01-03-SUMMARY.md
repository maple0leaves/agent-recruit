---
phase: 01-backend-foundation-auth
plan: 03
type: execute
generated: 2026-04-26T15:56:59Z
completed: 2026-04-26T16:04:12Z
duration_seconds: 489
requirements: [AUTH-01, AUTH-03]
---

# Phase 01 Plan 03: Frontend SPA Scaffold

**One-liner:** Vite React SPA with Tailwind v4, shadcn/ui components, routing structure, Axios API client with cookie auth, Zustand auth store, and useAuth hook.

## Completed Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Initialize Vite project and install all frontend dependencies | `d796fe6` |
| 2 | Create application core files (router, API client, auth store, auth hook, pages) | `ee6c9d7` |

## Commits

- `d796fe6`: feat(01-03): initialize Vite project with Tailwind v4, shadcn/ui, and frontend dependencies
- `ee6c9d7`: feat(01-03): create application core files (router, API client, auth store, auth hook, pages)
- `45a3858`: chore(01-03): add static/ to gitignore for Vite build output

## Files Created/Modified

### Frontend scaffold (new directory)
| File | Purpose |
|------|---------|
| `frontend/package.json` | Project dependencies (react, react-query, axios, router, zustand, tailwindcss, shadcn/ui) |
| `frontend/vite.config.ts` | Vite config with tailwindcss plugin, proxy for /auth and /api, build.outDir: ../static |
| `frontend/tsconfig.json` | Root TS config with path aliases (@/ -> ./src/) |
| `frontend/tsconfig.app.json` | App TS config with path aliases |
| `frontend/index.html` | Entry HTML with title "HR 智能招聘系统" |
| `frontend/src/styles/globals.css` | Tailwind v4 CSS entry with @import "tailwindcss" and shadcn CSS variables |
| `frontend/src/lib/utils.ts` | cn() utility (clsx + tailwind-merge) |
| `frontend/src/main.tsx` | React entry: QueryClientProvider + BrowserRouter |
| `frontend/src/App.tsx` | Route definitions: /login, /, /dashboard, /jd, /candidates, /matching |
| `frontend/src/api/client.ts` | Axios instance with withCredentials: true and 401 interceptor |
| `frontend/src/store/authStore.ts` | Zustand store: user, accessToken, setUser, setAccessToken, clearAuth |
| `frontend/src/hooks/useAuth.ts` | Auth hook: login, logout, isAuthenticated, isLoading via useQuery auth/me |
| `frontend/src/pages/Login.tsx` | Login page placeholder (coming in Plan 01-04) |
| `frontend/src/pages/Dashboard.tsx` | Dashboard placeholder |
| `frontend/src/pages/JDManagement.tsx` | JD management placeholder |
| `frontend/src/pages/Candidates.tsx` | Candidates placeholder |
| `frontend/src/pages/Matching.tsx` | Matching placeholder |
| `frontend/src/components/ui/` | shadcn/ui components (button, input, card, label, separator, avatar, sheet, skeleton) |

## Key Decisions

- **shadcn/ui v4 (base-nova style)**: The latest shadcn@4.5.0 uses "base-nova" style instead of the classic "new-york"/"default" presets. All components installed cleanly.
- **BrowserRouter in main.tsx**: Router wrapper placed at the app entry level, not in App.tsx. This is the standard React pattern and satisfies the routing requirement.
- **build.outDir: "../static"**: Vite build outputs to the project root `static/` directory per D-14 (FastAPI serves static files directly).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Dependency] Installed `zustand`**
- **Found during:** Task 2 - TypeScript compilation failed with "Cannot find module 'zustand'"
- **Issue:** The plan's npm install list omitted `zustand`, which is required by the auth store
- **Fix:** Added `npm install zustand` and committed the updated package.json
- **Files modified:** `frontend/package.json`, `frontend/package-lock.json`
- **Commit:** `ee6c9d7`

**2. [Rule 2 - Missing tsconfig] Added `ignoreDeprecations` to tsconfig.app.json**
- **Found during:** Task 2 build (tsc -b mode) failed with TS5101: Option 'baseUrl' is deprecated
- **Issue:** `baseUrl` is deprecated in TypeScript 7.0 but required for path aliases for shadcn compatibility
- **Fix:** Added `"ignoreDeprecations": "6.0"` to both `tsconfig.json` and `tsconfig.app.json`
- **Files modified:** `frontend/tsconfig.app.json`
- **Commit:** `ee6c9d7`

**3. [Rule 2 - Import Error] Fixed type-only import for verbatimModuleSyntax**
- **Found during:** Task 2 build (tsc -b mode) failed with TS1484: AuthUser must be imported using type-only import
- **Issue:** The `verbatimModuleSyntax` flag in tsconfig.app.json requires explicit `type` imports for types
- **Fix:** Changed `import { AuthUser }` to `import type { AuthUser }` in useAuth.ts
- **Files modified:** `frontend/src/hooks/useAuth.ts`
- **Commit:** `ee6c9d7`

**4. [Rule 2 - Missing gitignore] Added `static/` to .gitignore**
- **Found during:** Post-build cleanup check
- **Issue:** Vite build outputs to `../static/` (per build.outDir), generating tracked build artifacts
- **Fix:** Added `static/` to `.gitignore` and removed previously tracked `static/index.html` from index
- **Files modified:** `.gitignore`
- **Commit:** `45a3858`

### Note: shadcn/ui `form` component not available as standalone

The plan listed `form` as a required shadcn component, but shadcn@4.5.0 does not expose `form` as a standalone add-on component. `react-hook-form` is installed via `@hookform/resolvers` peer dependency and is available for direct use. The login page (Plan 01-04) can use react-hook-form directly or the form component can be manually created if needed.

## Verification Results

| Check | Status |
|-------|--------|
| `npx tsc --noEmit` | PASS (exit 0) |
| `npm run build` | PASS (exit 0) |
| Route definitions match D-13 | PASS |
| All pages export default components | PASS |
| API client has withCredentials + 401 interceptor | PASS |
| Auth store has setUser/setAccessToken/clearAuth | PASS |
| useAuth has login/logout/isAuthenticated/isLoading | PASS |
| shadcn/ui components directory exists | PASS |
| globals.css has @import "tailwindcss" | PASS |

## Self-Check

- `frontend/package.json` -- FOUND
- `frontend/vite.config.ts` -- FOUND
- `frontend/src/styles/globals.css` -- FOUND
- `frontend/src/lib/utils.ts` -- FOUND
- `frontend/index.html` -- FOUND
- `frontend/src/main.tsx` -- FOUND
- `frontend/src/api/client.ts` -- FOUND
- `frontend/src/store/authStore.ts` -- FOUND
- `frontend/src/hooks/useAuth.ts` -- FOUND
- `frontend/src/App.tsx` -- FOUND
- `frontend/src/pages/Login.tsx` -- FOUND
- `frontend/src/pages/Dashboard.tsx` -- FOUND
- `frontend/src/pages/JDManagement.tsx` -- FOUND
- `frontend/src/pages/Candidates.tsx` -- FOUND
- `frontend/src/pages/Matching.tsx` -- FOUND
- `frontend/src/components/ui/button.tsx` -- FOUND
- Commit `d796fe6` -- FOUND
- Commit `ee6c9d7` -- FOUND
- Commit `45a3858` -- FOUND

## Self-Check: PASSED

## Threat Flags

None. All created files are new frontend-only additions with no new network endpoints, auth paths, or data access patterns beyond what the plan defines. The 401 interceptor on `api/client.ts` is a standard UX redirect, not a security mechanism.
