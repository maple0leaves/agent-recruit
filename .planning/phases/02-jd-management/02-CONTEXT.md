# Phase 2: JD Management - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

HR 可以创建、编辑、管理职位描述（JD），支持从预设模板快速创建，按状态/关键词/日期筛选和搜索 JD 列表。交付：JD CRUD API + 列表页 + 编辑页 + 模板快速创建。Phase 2 是 Phase 1 之上的第一个业务功能层，使用已有的认证体系、数据库设施和前端壳。

</domain>

<decisions>
## Implementation Decisions

### JD Data Model
- **D-01:** JD 核心字段：title (str), department (str, 自由文本), skills (str, 逗号分隔), experience_years (int), education (enum), salary_min (int), salary_max (int), description (str, 长文本), status (enum)
- **D-02:** education 枚举值：高中 / 大专 / 本科 / 硕士 / 博士 / 不限
- **D-03:** title 无命名规范约束，HR 自由输入
- **D-04:** created_at / updated_at 时间戳自动维护

### JD List UI
- **D-05:** 表格布局（shadcn/ui Table），列：职位名称、部门、状态、薪资范围、更新日期
- **D-06:** 传统分页（每页 20 条），页码按钮 + 上一页/下一页
- **D-07:** 服务端搜索和筛选，API 传参过滤
- **D-08:** 筛选维度：状态筛选、关键词搜索、日期范围筛选

### JD Template System
- **D-09:** 3-5 个预设模板，硬编码在代码/配置文件里，不需要数据库表
- **D-10:** 模板预设所有字段（skills, experience_years, education, salary_min, salary_max, description），HR 填写 title 和 department
- **D-11:** HR 不能编辑或创建模板（Phase 2 范围外）

### JD Status & Lifecycle
- **D-12:** 三状态：draft（草稿）→ active（发布中）→ closed（已关闭），closed 可重新激活回 active
- **D-13:** 只关不删，不提供删除功能（软删除/硬删除都不做）
- **D-14:** 任何登录用户都可以创建/编辑任何 JD，不做创建者所有权控制

### Carried Forward from Phase 1
- SQLite + SQLAlchemy async async_session pattern — JD 模型和迁移复用此模式
- Alembic migrations — JD 表通过新的 migration 创建
- FastAPI Depends() 认证模式 — JD 端点挂 get_current_user / require_role
- React 19 + Vite + TypeScript + Tailwind v4 + shadcn/ui
- TanStack Query (useQuery/useMutation) + axios withCredentials
- Dark sidebar layout，/jd 路由已预留，JD 管理页已在导航栏中

### Claude's Discretion
- 模板具体包含哪些职位（如"软件工程师"、"产品经理"等）
- skills 逗号分隔格式的具体值
- 列表页表格列的具体顺序和宽度
- 日期范围筛选的 UI 组件选择
- 新增 JD 时表单的布局和分步方式

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — 项目定位、核心价值、约束和关键决策
- `.planning/REQUIREMENTS.md` — v1 需求，Phase 2 覆盖 JD-01/JD-02/JD-03/JD-04

### Roadmap & scope
- `.planning/ROADMAP.md` — Phase 2 目标、成功标准、依赖关系

### Phase 1 foundation (decisions inherited)
- `.planning/phases/01-backend-foundation-auth/01-CONTEXT.md` — D-05 (SQLite+SQLAlchemy), D-07 (Alembic), D-10~D-14 (frontend stack)

### Existing codebase
- `.planning/codebase/CONVENTIONS.md` — 命名规范、类型注解、文件组织
- `.planning/codebase/CONCERNS.md` — 已知问题

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/db/engine.py` — async engine + session factory, Base 类已定义
- `backend/db/models/user.py` — User 模型模板，JD 模型遵循相同 Column/Enum 模式
- `backend/api/routes/auth.py` — API 路由模板，JD 路由遵循 APIRouter + Depends 模式
- `backend/api/deps.py` — get_current_user, require_role 认证依赖
- `frontend/src/api/client.ts` — axios 实例，withCredentials 已配置
- `frontend/src/hooks/useAuth.ts` — 认证 hook，JD 页面可复用
- `frontend/src/components/Layout.tsx` — 侧边栏+顶栏布局，/jd 路由已注册
- shadcn/ui components: Button, Input, Card, Label, Form, Separator, Table 可通过 npx shadcn add 安装

### Established Patterns
- SQLAlchemy async: `create_async_engine` + `async_sessionmaker` + `DeclarativeBase`
- FastAPI: `APIRouter(prefix="/jd", tags=["jd"])` + `Depends(get_current_user)`
- Alembic: `backend/db/migrations/versions/` 目录，同步 engine URL
- Frontend pages: `frontend/src/pages/` 目录，React 函数组件 + TSX
- API 交互: TanStack Query `useQuery` / `useMutation` 模式

### Integration Points
- JD API 挂载到 `api/server.py` 的 FastAPI app（除 auth 中间件外）
- JD 页面替换 `frontend/src/pages/JDManagement.tsx` 占位页
- JD 数据表由新的 Alembic migration 创建，与 users 表共享同一个 SQLite 文件
- 前端路由 `/jd` 已在 App.tsx 中注册，由 ProtectedRoute + Layout 包裹

</code_context>

<specifics>
## Specific Ideas

- 用户偏好简洁：最小字段、三状态、只关不删、无所有权控制 — 避免过度设计
- 模板系统偏好硬编码而非数据库驱动，保持 Phase 2 复杂度可控

</specifics>

<deferred>
## Deferred Ideas

- 部门预设枚举列表（department 下拉选择）— Phase 2 用自由文本
- HR 可自定义模板（创建/编辑/删除模板）— 后续阶段
- JD 所有权控制（创建者+admin 才可编辑）— 后续阶段
- JD 删除/软删除功能 — 当前只关不删
- JD 审批流程 — 当前无需审批，即时创建
- 批量导入 JD — v2 范围（RES-06 同类功能）

</deferred>

---

*Phase: 02-jd-management*
*Context gathered: 2026-04-26*
