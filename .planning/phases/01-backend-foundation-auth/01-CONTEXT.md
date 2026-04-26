# Phase 1: Backend Foundation & Authentication - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

将现有的裸 Agent 后端变成有认证、有数据库、有前端入口的安全系统底座。交付：HR 可以用用户名密码登录，系统区分角色，后端稳定安全。这是后续所有阶段的依赖。

</domain>

<decisions>
## Implementation Decisions

### Authentication Strategy
- **D-01:** JWT 存储在 HTTP-only cookie（不用 localStorage）— 防 XSS，SSE 无需额外处理
- **D-02:** PyJWT + passlib(bcrypt) 作为 JWT 和密码哈希库，搭配 FastAPI OAuth2PasswordBearer 模式
- **D-03:** 简单角色检查 — JWT payload 里带 role 字段，后端 Depends() 检查。三种角色：admin / recruiter / hiring-manager
- **D-04:** 登录页提供用户名+密码登录，不需要注册页、不需要"记住我"

### Database & Storage
- **D-05:** SQLite + SQLAlchemy async — Phase 1 零配置开发，schema 按 PostgreSQL 规范设计，后续换连接串即可切换
- **D-06:** 用户表最小字段：username, hashed_password, role(enum: admin/recruiter/hiring-manager), created_at
- **D-07:** Alembic 做 migration，初始化建 users 表
- **D-08:** CLI 种子脚本（seed.py）创建第一个 admin 用户，密码通过环境变量或命令行参数传入
- **D-09:** LangGraph checkpoint 从 InMemorySaver 换成 SqliteSaver，复用同一个 SQLite 文件

### Frontend Scaffold
- **D-10:** React 19 + Vite + TypeScript + Tailwind CSS v4 + shadcn/ui
- **D-11:** 完整应用壳 — 登录页 + 侧边栏+顶栏布局 + 受保护的路由占位页
- **D-12:** TanStack Query + axios 管理 API 交互，axios 配置 withCredentials 自动携带 cookie
- **D-13:** 路由结构：/login（公开）、/（重定向到 /dashboard）、/dashboard /jd /candidates /matching（受保护占位页）
- **D-14:** 生产环境 FastAPI 直接托管 Vite build 的 dist/ 静态文件，不需要独立前端服务

### Backend Hardening
- **D-15:** 全部在 Phase 1 完成 — 认证中间件、SSE 超时/断连处理、async 端点改造、CORS 配置、请求体输入校验
- **D-16:** CORS 配置为前端开发和生产域名，credentials 开启（配合 cookie 跨域）

### Claude's Discretion
- 登录页和布局的具体视觉设计（颜色、间距、字体）
- 密码强度策略（是否要求最小长度、特殊字符）
- Token 过期时间的具体数值
- SSE 超时的具体秒数
- Loading/error 状态的具体 UI

</decisions>

<specifics>
## Specific Ideas

- 用户明确选择"最小字段"+"简单角色检查"+"CLI 种子脚本"——偏好保持简洁，不引入企业级框架的复杂度
- Phase 1 做完整应用壳而非仅登录页——说明预期后续阶段快速迭代，现在搭好骨架很重要

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — 项目定位、核心价值、约束和关键决策
- `.planning/REQUIREMENTS.md` — v1 需求，Phase 1 覆盖 AUTH-01/AUTH-02/AUTH-03

### Roadmap & scope
- `.planning/ROADMAP.md` — Phase 1 目标、成功标准、依赖关系

### Research on tech decisions
- `.planning/research/STACK.md` — 前端/后端技术栈推荐及版本
- `.planning/research/ARCHITECTURE.md` — 系统架构、组件边界、构建顺序
- `.planning/research/PITFALLS.md` — 13 个已知坑点及 Phase 1 需要防范的 7 个

### Existing codebase
- `.planning/codebase/CONCERNS.md` — 当前代码库已知问题（无 auth、InMemorySaver、async 阻塞等）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `api/server.py` — FastAPI 路由和 SSE 端点，Phase 1 需要在上面加 auth 中间件
- `config.py` — 全局配置模块，可扩展数据库连接和 JWT 配置
- `main.py` — LangGraph StateGraph 构建，需要从 InMemorySaver 切换到 SqliteSaver

### Established Patterns
- FastAPI 依赖注入模式 — 现有端点已用 Depends()，auth 中间件同理
- Pydantic schema 定义在 `agent/schemas.py` — 新增用户模型遵循相同模式
- 环境变量配置在 `.env` — JWT_SECRET 和数据库连接串遵循此模式

### Integration Points
- Auth 中间件挂在 `api/server.py` 的 FastAPI app 层级
- SQLite 数据库文件放在 `data/` 目录下
- 前端 SPA build 输出到 `static/` 目录（覆盖现有 index.html）
- SSE 端点 `/recruit/stream` 需要加超时和断连处理

</code_context>

<deferred>
## Deferred Ideas

- 用户注册页面 — 超出 Phase 1 范围，管理员通过 CLI 创建
- "记住我"功能 — Phase 1 不做
- 细粒度权限（部门级隔离）— 当前简单角色检查够用，后续按需升级
- 前端 SSR/Next.js — 明确选 React SPA，无 SEO 需求
- 独立前端部署（nginx）— 当前 FastAPI 托管够用

</deferred>

---

*Phase: 01-backend-foundation-auth*
*Context gathered: 2026-04-26*
