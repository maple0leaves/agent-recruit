---
phase: 01-backend-foundation-auth
plan: 04
type: execute
wave: 2
subsystem: frontend-auth-ui
tags:
  - frontend
  - login-page
  - auth-guard
  - layout
  - sidebar
  - placeholder-pages
requires:
  - "01-03-frontend-scaffold"
provides:
  - "Login page with all states"
  - "ProtectedRoute auth guard"
  - "Layout sidebar + topbar shell"
  - "Placeholder pages for all 4 routes"
affects:
  - frontend/src/App.tsx
  - frontend/src/pages/*
  - frontend/src/components/*
tech-stack:
  added: []
  patterns:
    - "Nested route elements (ProtectedRoute > Layout > Page) for auth+layout composition"
    - "Axios error shape (err.response / err.request) for server vs network error differentiation"
    - "useSearchParams for post-login redirect preservation"
key-files:
  created:
    - "frontend/src/components/ProtectedRoute.tsx"
    - "frontend/src/components/Layout.tsx"
  modified:
    - "frontend/src/pages/Login.tsx"
    - "frontend/src/pages/Dashboard.tsx"
    - "frontend/src/pages/JDManagement.tsx"
    - "frontend/src/pages/Candidates.tsx"
    - "frontend/src/pages/Matching.tsx"
    - "frontend/src/App.tsx"
decisions: []
metrics:
  duration: 5m
  completed: "2026-04-26T16:13:00Z"
  tasks: 3
  files: 8
  commits: 3
---

# Phase 1 Plan 4: Completed — Frontend Auth UI (Login, Layout, Placeholders)

**One-liner:** Built the complete frontend authentication UI layer: login page with all form/validation/error states, ProtectedRoute auth guard with loading skeleton and redirect, Layout sidebar+topbar shell with user area and logout, and placeholder pages for all 4 protected routes.

## Summary

Executed plan 01-04 across 3 atomic tasks, each committed separately. Every file compiles cleanly under `tsc --noEmit` and the full Vite production build passes with zero errors. No deviations were needed -- the plan was executed exactly as written.

### Task 1: Login Page (`06819e2`)

Wrote `frontend/src/pages/Login.tsx` with:
- Centered Card on Slate-50 background with brand "HR 智能招聘系统" at 28px semibold
- Subtitle "请登录以继续" in muted text
- Username input (placeholder "用户名") and password input (placeholder "密码")
- Submit validation: "请输入用户名" (min 2 chars), "请输入密码" (non-empty)
- Field-level error messages in destructive red, cleared on input change
- Server error display: "用户名或密码错误" for 401 responses
- Network error display: "网络连接失败，请检查网络后重试"
- Loading state: button shows Loader2 spinner + "登录中...", inputs remain editable
- Redirect to original URL via `useSearchParams`
- Password cleared on error per UI-SPEC interaction contract

### Task 2: ProtectedRoute + Layout (`94cf7d6`)

Created `frontend/src/components/ProtectedRoute.tsx`:
- Loading state: centered Skeleton with "正在加载..." text
- Unauthenticated: `<Navigate to="/login?redirect=..." replace />` preserving intended destination
- Authenticated: renders `<Outlet />` for child routes

Created `frontend/src/components/Layout.tsx`:
- Fixed 240px Slate-900 sidebar with Briefcase icon + "hellojobs" branding
- Nav items with Lucide icons: Dashboard (LayoutDashboard), JD管理 (FileText), 候选人 (Users), 智能匹配 (BrainCircuit)
- Active nav item: 3px left border Blue-600, background #1e3a5f, text Blue-400
- Inactive: text Slate-400, hover bg Slate-800
- User area at bottom: Avatar with initial, username, Chinese role labels (管理员/招聘专员/部门主管), logout button "退出登录"

### Task 3: Placeholder Pages + App.tsx Routing (`1b49494`)

Updated all 4 placeholder pages with consistent Card UI:
- 48px Lucide icon, 20px heading, "功能开发中，敬请期待" description
- Each uses the matching icon from nav (LayoutDashboard, FileText, Users, BrainCircuit)

Replaced App.tsx with nested route structure:
- `/login` public route
- Protected routes wrapped in `<ProtectedRoute>` > `<Layout>` > page components
- `/` and `*` redirect to `/dashboard`

## Deviations from Plan

None - plan executed exactly as written.

## Threat Flags

None - all threat items (T-1-09, T-1-10, T-1-11) are correctly addressed:
- ProtectedRoute is UX-only guard (T-1-09 accepted -- backend enforces auth)
- Auth tokens in memory only (T-1-10 accepted -- HttpOnly cookie on server side)
- Role labels are intended UX (T-1-11 accepted -- D-02 requirement)

## Key Links

| From | To | Via |
|------|----|------|
| Login.tsx | useAuth.ts | `useAuth().login` |
| Layout.tsx | useAuth.ts | `useAuth().logout` / `useAuth().user` |
| ProtectedRoute.tsx | useAuth.ts | `useAuth().isLoading` / `useAuth().isAuthenticated` |
| App.tsx | ProtectedRoute | `<ProtectedRoute>` wrapping `<Layout>` |

## Self-Check: PASSED

- [x] `frontend/src/pages/Login.tsx` exists, contains all required copy strings
- [x] `frontend/src/components/ProtectedRoute.tsx` exists, checks auth, renders Outlet
- [x] `frontend/src/components/Layout.tsx` exists, sidebar with nav + user area + logout
- [x] All 4 placeholder pages exist with proper icons and copy
- [x] App.tsx has correct nested route structure
- [x] `npx tsc --noEmit` exits 0
- [x] `npm run build` exits 0, produces static/ output
- [x] Commits: 06819e2, 94cf7d6, 1b49494 all present in git log
