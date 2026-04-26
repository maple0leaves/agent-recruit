# Phase 4: AI Matching & Approval - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

HR 从 JD 列表触发 AI 匹配，实时观看 Agent 流式进度（步骤管道图），逐步展示匹配结果（卡片列表 + 百分比评分 + 技能对比），逐个审核通过/驳回（reject 需备注），审核完成后批量提交恢复 Agent。仪表盘展示活跃 JD 数、候选人总数、待审核数。这是产品的核心价值——AI 匹配 + 人审核。

</domain>

<decisions>
## Implementation Decisions

### Matching Trigger & Streaming
- **D-01:** 从 JD 列表触发匹配 — 每行 JD 增加「开始匹配」按钮，点击后进入匹配页面
- **D-02:** 步骤管道图可视化 — Triage → 搜索 → 评分 → 审核，当前步骤 pulse 动画，已完成步骤打勾 ✓
- **D-03:** 匹配过程中允许取消 — 显示「取消匹配」按钮，取消后清理 Agent 工作，返回 JD 列表
- **D-04:** 前台等待模式 — 用户留在匹配页面观看流式进度，SSE 推送 [DONE] 后自动展示所有结果

### Match Results Display
- **D-05:** 匹配评分用百分比展示 — 如 "92% 匹配度"，根据 match_score 计算
- **D-06:** 卡片列表布局 — 每张卡片：候选人姓名 + 匹配度 + 技能标签（✅ 匹配 / ❌ 缺失）+ [通过] [驳回] 按钮
- **D-07:** 逐步展示 — SSE 每推送一个匹配结果，卡片立即弹出（渐进式渲染），营造实时感
- **D-08:** 结果按匹配度降序排列

### Approval Workflow
- **D-09:** 逐个审核 — 每张卡片独立操作，点击通过/驳回后卡片收起或灰掉
- **D-10:** 驳回备注必填（拒绝原因），通过备注可选
- **D-11:** 驳回后该候选人在本次匹配中标记为 rejected，不重新匹配
- **D-12:** 所有候选人审核完后，页面底部出现「完成审核」按钮，点击后批量提交（HITL resume）通知 Agent 继续

### Dashboard
- **D-13:** 3 个指标卡片：活跃 JD 数、候选人总数、待审核数，每个卡片有 Lucide 图标
- **D-14:** 页面加载时刷新数据（useQuery 默认行为），不自动轮询
- **D-15:** 点击指标卡片跳转到对应页面（活跃 JD → /jd，候选人 → /candidates，待审核 → /matching）

### Carried Forward from Phase 1-3
- SSE 流式端点 `/recruit/stream` 已加固（超时 120s、断连检测、[DONE] sentinel）
- LangGraph Agent 管线：triage → planner → worker → reviewer，HITL interrupt_before=["reviewer_agent"]
- HITL 中断/恢复机制：POST `/recruit/hitl/start` + `/recruit/hitl/resume`
- JWT 认证 + HttpOnly cookie 已覆盖所有端点
- React 19 + Vite + TypeScript + Tailwind v4 + shadcn/ui（Card/Badge/Button 已安装）
- TanStack Query + axios + EventSource/SSE 模式
- Dark sidebar layout，/matching 路由已预留，Dashboard 路由已有 /dashboard 占位

### Claude's Discretion
- 步骤管道图的具体 CSS 动画实现（pulse 动画、颜色过渡）
- 匹配卡片的具体视觉设计（间距、阴影、响应式列数）
- SSE EventSource 重连策略的具体参数
- 取消匹配时的清理确认对话框文案
- 仪表盘卡片的排列方向（垂直还是水平）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — 项目定位、已有 Agent 能力、HITL 流程
- `.planning/REQUIREMENTS.md` — v1 需求，Phase 4 覆盖 MATCH-01/02/03, APRV-01/02, DASH-01

### Roadmap & scope
- `.planning/ROADMAP.md` — Phase 4 目标、成功标准、依赖关系（Phase 2 JD + Phase 3 Candidates）

### Phase 1-3 foundation
- `.planning/phases/01-backend-foundation-auth/01-CONTEXT.md` — Auth, SSE, SqliteSaver
- `.planning/phases/02-jd-management/02-CONTEXT.md` — JD model + API patterns
- `.planning/phases/03-resume-candidate-management/03-CONTEXT.md` — Candidate model + API patterns

### Existing Agent codebase
- `api/server.py` — 已有 SSE `/recruit/stream`、HITL `/recruit/hitl/*` 端点
- `main.py` — LangGraph StateGraph 构建 + SqliteSaver
- `agent/schemas.py` — MatchResult、CandidateInfo schema

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `api/server.py` — POST `/recruit`（触发匹配）、GET `/recruit/stream`（SSE 流式）、POST `/recruit/hitl/start`（HITL 开始）、POST `/recruit/hitl/resume`（HITL 恢复）
- `main.py` — `build_graph(use_hitl=True)` 返回带 interrupt_before 的 compiled graph
- `agent/schemas.py` — `MatchResult` (candidate_id, name, match_score, matched_skills, missing_skills)、`CandidateInfo`
- `backend/db/models/jd.py` — JD 模型（匹配输入）
- `backend/db/models/candidate.py` — Candidate 模型（匹配对象）
- `frontend/src/api/client.ts` — axios withCredentials
- `frontend/src/pages/Matching.tsx` — 占位页（待替换）
- `frontend/src/pages/Dashboard.tsx` — 占位页（待替换）
- shadcn/ui: Card, Badge, Button（已安装），可能需要 Progress 组件

### Established Patterns
- SSE 消费：EventSource API + onmessage handler，解析 JSON event data
- HITL 流程：前端触发 → Agent 运行到 reviewer → interrupt → 前端展示结果 → 用户审核 → POST /recruit/hitl/resume → Agent 继续
- JD list 触发操作：在 JdManagement 页增加 action 按钮（与已有 dropdown menu 模式一致）
- 仪表盘：TanStack Query useQuery 获取数据，页面加载时刷新

### Integration Points
- 匹配页面替换 `frontend/src/pages/Matching.tsx` 占位
- 仪表盘替换 `frontend/src/pages/Dashboard.tsx` 占位
- JD 列表页增加匹配按钮（修改 JdManagement.tsx 或 JDTable 的 action column）
- 仪表盘 API 需要新增后端聚合端点（如 GET /dashboard/stats）

</code_context>

<specifics>
## Specific Ideas

- 用户偏好"前台等待+逐步展示"的流式体验 — 匹配过程是核心产品体验
- 卡片列表而非表格 — 匹配结果需要更丰富的视觉展示
- 批量提交审核结果 — 避免频繁 HITL resume
- 仪表盘保持简洁（3 卡片），不做复杂图表

</specifics>

<deferred>
## Deferred Ideas

- 后端 Agent 反馈（HR 审核意见反向训练 Agent）— Phase 5 (APRV-03)
- 反向匹配（从 Candidate 侧发起匹配）— Phase 5 (MATCH-04)
- 批量审核操作 — 当前逐个审核
- 仪表盘图表/趋势 — 当前仅 3 个指标卡片
- 匹配结果导出 — Phase 5 (DASH-02)
- 仪表盘自动刷新/轮询 — 当前页面加载刷新
- 匹配历史记录页面 — 当前匹配结果在 session 内展示

</deferred>

---

*Phase: 04-ai-matching-approval*
*Context gathered: 2026-04-26*
