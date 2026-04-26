# Phase 3: Resume & Candidate Management - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

HR 可以上传 PDF/Word 简历文件，系统自动调用已有 Agent 解析简历提取结构化数据，HR 可查看和编辑解析结果，搜索候选人库，跟踪候选人 Pipeline 状态（New → Screening → Interview → Hired/Rejected）。交付：简历上传 API + 候选人 CRUD API + 列表页 + 详情/编辑页 + Pipeline 状态管理。

</domain>

<decisions>
## Implementation Decisions

### Resume Upload & Parsing
- **D-01:** 复用已有 LangGraph Agent 的简历解析逻辑，不新建独立解析函数
- **D-02:** 接受 PDF 和 Word（.doc/.docx）格式，单文件最大 10MB
- **D-03:** 同步解析 — 上传后立即解析（3-10 秒），返回包含解析结果的 Candidate 对象
- **D-04:** 解析预览展示提取字段（name/skills/education/experience），HR 可手动编辑修正
- **D-05:** 解析失败不阻塞流程 — 返回部分成功结果 + 警告信息，HR 可以手动补填所有字段

### Candidate Data Model
- **D-06:** 标准字段：name (str), email (str, optional), phone (str, optional), skills (str, 逗号分隔), education (str), experience (str, 长文本), status (enum), resume_file_path (str), status_note (str), parsed_at (datetime), created_at, updated_at
- **D-07:** 简历文件存本地磁盘（`data/resumes/` 目录），数据库只存文件路径，不存 BLOB
- **D-08:** Pipeline 状态枚举：new / screening / interview / hired / rejected
- **D-09:** 状态变更时备注（status_note）必填

### Candidate List & Detail UI
- **D-10:** 表格布局（shadcn Table，与 JD 列表一致），列：姓名、技能、状态、上传日期
- **D-11:** 搜索/筛选：姓名模糊搜索 + 技能关键词搜索 + 状态筛选
- **D-12:** 详情页单页滚动布局 — 解析数据区 + 匹配历史区（占位）+ 状态操作区。点击列表行直接进入编辑模式
- **D-13:** 匹配历史区域显示「暂无匹配记录」占位提示（Phase 4 填充）

### Pipeline Status & Lifecycle
- **D-14:** 状态机：new → screening → interview → hired | rejected
- **D-15:** hired 和 rejected 是终态，不可逆
- **D-16:** 每次状态变更需要填写备注（status_note），必填
- **D-17:** 不提供删除功能 — 候选人记录（包括 rejected）始终保留

### Carried Forward from Phase 1 & 2
- SQLite + SQLAlchemy async + Alembic（Candidate 模型和迁移复用此模式）
- FastAPI Depends() 认证模式 — 所有候选人端点挂 get_current_user
- React 19 + Vite + TypeScript + Tailwind v4 + shadcn/ui（Table/Form/Dialog/Badge）
- TanStack Query (useQuery/useMutation) + axios withCredentials
- Dark sidebar layout，/candidates 路由已预留
- 服务端搜索/筛选 + 传统分页（20 条/页）— 与 JD 列表一致
- 已有 Agent 解析能力（agent/schemas.py 有 CandidateInfo schema）

### Claude's Discretion
- 简历文件存储目录名称（建议 `data/resumes/`）
- 解析超时时间的具体秒数
- 候选人与简历文件的一对一/一对多关系
- 上传进度指示器的 UI 细节
- 详情页各区域的排布顺序和间距

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — 项目定位、已有 Agent 能力（简历解析）、技术栈
- `.planning/REQUIREMENTS.md` — v1 需求，Phase 3 覆盖 RES-01~RES-05

### Roadmap & scope
- `.planning/ROADMAP.md` — Phase 3 目标、成功标准、依赖关系

### Phase 1 & 2 foundation
- `.planning/phases/01-backend-foundation-auth/01-CONTEXT.md` — D-05 (SQLite+SQLAlchemy), D-07 (Alembic), D-10~D-14 (frontend stack)
- `.planning/phases/02-jd-management/02-CONTEXT.md` — CRUD 模式参考、Table 列表模式、Form dialog 模式

### Existing codebase
- `.planning/codebase/CONVENTIONS.md` — 命名规范、类型注解、文件组织
- `agent/schemas.py` — 已有 CandidateInfo schema（简历解析结果）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/db/engine.py` — async engine + Base + get_session
- `backend/db/models/user.py` / `jd.py` — 模型模板（Candidate 模型遵循相同 Column/Enum/DeclarativeBase 模式）
- `backend/api/routes/auth.py` / `jd.py` — API 路由模板（Candidate 路由遵循 APIRouter + Depends 模式）
- `backend/api/deps.py` — get_current_user, require_role
- `agent/schemas.py` — CandidateInfo Pydantic schema（已有），可直接用于解析输出
- `frontend/src/api/client.ts` — axios withCredentials
- `frontend/src/hooks/useJDs.ts` — TanStack Query hook 模板（useCandidates 遵循相同模式）
- `frontend/src/components/JDs/JDTable.tsx` — Table 组件模板（CandidateTable 复用相同 @tanstack/react-table 模式）
- shadcn/ui 已安装组件：table, form, dialog, select, badge, textarea, button, input, card, calendar

### Established Patterns
- 服务端筛选：SQLAlchemy `.where()` 链式动态过滤 + `ilike()` 关键词搜索
- 前端分页：TanStack Query `placeholderData: keepPreviousData` + 传统页码组件
- Table：@tanstack/react-table `useReactTable()` + `flexRender()`
- Form：react-hook-form + Zod validation + shadcn Form 组件

### Integration Points
- Candidate API 挂载到 `api/server.py` 的 FastAPI app
- Candidate 页面替换 `frontend/src/pages/Candidates.tsx` 占位页
- 简历文件存储到 `data/resumes/` 目录（需创建 + gitignore）
- Candidate 数据表由新 Alembic migration 创建
- 前端路由 `/candidates` 已在 App.tsx 注册
- Agent 解析函数：直接导入调用（POST /candidates/upload 处理流程：保存文件 → 调 Agent 解析 → 存 Candidate → 返回结果）

</code_context>

<specifics>
## Specific Ideas

- 用户偏好简洁：标准字段、只关不删、终态不可逆 — 避免过度设计
- 解析预览可编辑 — 体现"AI 辅助，人做判断"的核心价值
- 详情页直接编辑（点击即编辑）— 减少操作步骤
- 匹配历史用占位提示 — Phase 4 开发时自然衔接

</specifics>

<deferred>
## Deferred Ideas

- 异步简历解析（后台任务 + 轮询/SSE）— Phase 3 用同步解析
- 批量上传简历（一次提交多文件）— v2 范围（RES-06）
- 候选人删除功能 — 当前只保留不删
- 简历文件存数据库（BLOB）— 当前存本地磁盘路径
- Pipeline 更细粒度状态（phone_screen, technical_test 等）— 当前 5 状态够用
- 候选人头像/照片提取 — 超出当前解析范围
- 候选人卡片布局 — 列表用标准表格

</deferred>

---

*Phase: 03-resume-candidate-management*
*Context gathered: 2026-04-26*
