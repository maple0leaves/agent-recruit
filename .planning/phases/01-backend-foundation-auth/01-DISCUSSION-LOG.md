# Phase 1: Backend Foundation & Authentication - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-26
**Phase:** 01-backend-foundation-auth
**Areas discussed:** 认证方案, 数据库选型 + 用户初始化, 前端脚手架范围, 后端加固优先级

---

## 认证方案

| Option | Description | Selected |
|--------|-------------|----------|
| HTTP-only cookie | XSS 攻击拿不到 token，更安全。FastAPI 用 Depends() 自动解析。SSE 也能正常用 | ✓ |
| localStorage + Bearer header | 前端实现简单，但 XSS 能偷 token。SSE 需要额外处理（URL 带 token） | |

| Option | Description | Selected |
|--------|-------------|----------|
| 简单角色检查 | JWT 里带 role 字段，后端接口用 Depends() 检查角色即可。够用，不引入 RBAC 框架复杂度 | ✓ |
| 细粒度权限 | 检查具体操作权限（如 '只能编辑自己部门的 JD'）。引入 Casbin 或自定义 ABAC | |

| Option | Description | Selected |
|--------|-------------|----------|
| PyJWT + passlib | PyJWT 是事实标准，passlib 处理密码 hash（bcrypt）。搭配 FastAPI OAuth2PasswordBearer 模式 | ✓ |
| python-jose | 更完整的 JOSE 标准实现，功能比 PyJWT 多但依赖更重 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 用户名+密码登录 | 登录后拿到 cookie，有登出按钮。Phase 1 不需要注册页（管理员手动创建） | ✓ |
| 加上记住我 | 登录时可选「记住我」，token 有效期延长到 7 天 | |

---

## 数据库选型 + 用户初始化

| Option | Description | Selected |
|--------|-------------|----------|
| SQLite → 可切 PostgreSQL | 用 SQLAlchemy async 写，Phase 1 先用 SQLite 零配置开发。建模时按 PostgreSQL 规范设计，后面一条配置就切过去 | ✓ |
| 直接上 PostgreSQL | 从 Phase 1 就用 PostgreSQL，避免后续迁移。但多一个外部依赖 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 最小字段 | username, hashed_password, role(enum), created_at。够 Phase 1 用，后续按需加字段 | ✓ |
| 多加一些 | 加上 display_name, email, is_active, last_login。为后续功能预留 | |

| Option | Description | Selected |
|--------|-------------|----------|
| CLI 种子脚本 | 提供一个 python seed.py 命令，创建默认 admin 用户。简单直接，适合内部工具 | ✓ |
| 数据库 migration 里 seed | Alembic migration 自动插入初始 admin，但密码需要环境变量传 | |

| Option | Description | Selected |
|--------|-------------|----------|
| Alembic | SQLAlchemy 官配，异步原生支持。Phase 1 只需要建 users 表 | ✓ |
| 手动 SQL | 自己写 CREATE TABLE 脚本，不引入 Alembic 学习成本 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 换 SqliteSaver | 当前 InMemorySaver 重启丢数据。换 SqliteSaver 用同一个 SQLite 文件，零额外依赖 | ✓ |
| Phase 1 不动 | 当前不改，等 Phase 4（Matching & Approval）再换 | |

---

## 前端脚手架范围

| Option | Description | Selected |
|--------|-------------|----------|
| 完整应用壳 | 登录页 + 应用布局（侧边栏、顶部栏、路由框架）+ 角色保护的路由占位页。后续阶段直接往里填业务页面 | ✓ |
| 只要登录页 | 就一个登录页 + 登录后跳转占位页。Phase 2/3 再加布局和导航 | |

| Option | Description | Selected |
|--------|-------------|----------|
| React 19 + Vite + shadcn/ui | 研究验证过的标准组合。shadcn/ui 提供组件源码，Tailwind v4 样式。TanStack Query 管理服务端状态 | ✓ |
| React 19 + Ant Design | 国内 HR 后台常用，开箱即用的 Table/Form 组件，但定制性差 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 侧边栏 + 顶栏 | 左侧可折叠导航（职位、候选人、匹配、审批），顶部用户信息+登出 | ✓ |
| 只有顶栏 | 顶部导航，内容区更宽。适合页面少的简单后台 | |

| Option | Description | Selected |
|--------|-------------|----------|
| TanStack Query + axios | Query 管理缓存/重取/loading 状态，axios 自动带 cookie。标准组合 | ✓ |
| 裸 fetch + 自定义 hook | 不引入 Query 的复杂度，手写几个 hook。简单但后续状态管理容易乱 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 登录 + 占位页 | /login 登录页，/ 重定向到 /dashboard（占位），/jd、/candidates、/matching 占位，都受登录保护 | ✓ |
| 只做登录 | /login，登录后 / 显示一个简单首页 | |

---

## 后端加固优先级

| Option | Description | Selected |
|--------|-------------|----------|
| Auth 中间件 + SQLite | 加认证、加数据库。这是 Phase 1 的核心交付 | ✓ |
| SSE 超时/断连处理 | 当前 SSE stream 没有 timeout 和 disconnect 处理，前端连不上或断开时资源泄漏 | ✓ |
| async 端点改造 | 当前 4 个端点用 def 而不是 async def，会阻塞 event loop | ✓ |
| CORS + 输入校验 | 配置前端域名的 CORS，加 FastAPI 请求体校验 | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| FastAPI 托管静态文件 | Vite build 后把 dist/ 放到 FastAPI 的 static/ 下，一个端口搞定，零额外服务 | ✓ |
| 独立 dev server | 开发时 Vite dev server 独立跑，生产时用 nginx 反代 | |

---

## Claude's Discretion

- 登录页和布局的具体视觉设计
- 密码强度策略
- Token 过期时间的具体数值
- SSE 超时的具体秒数
- Loading/error 状态的具体 UI

## Deferred Ideas

- 用户注册页面 — 超出 Phase 1 范围
- "记住我"功能 — Phase 1 不做
- 细粒度权限（部门级隔离）— 当前简单角色检查够用
- 前端 SSR/Next.js — 无 SEO 需求
- 独立前端部署（nginx）— FastAPI 托管够用
