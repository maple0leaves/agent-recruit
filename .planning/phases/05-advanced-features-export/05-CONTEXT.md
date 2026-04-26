# Phase 5: Advanced Features & Export - Context

**Gathered:** 2026-04-26
**Status:** Ready for planning

<domain>
## Phase Boundary

HR 可以从候选人侧发起反向匹配（找合适的 JD），审核时给 Agent 发送反馈让其重新调整结果，匹配完成后导出 PDF 报告和 Excel 表格。这是最后阶段，三项相对独立的功能基于 Phase 4 的匹配基础设施构建。

</domain>

<decisions>
## Implementation Decisions

### Reverse Matching (Candidate → JD)
- **D-01:** 从候选人详情页触发 — CandidateDetail 加「反向匹配」按钮
- **D-02:** 复用匹配页面和 SSE 基础设施 — 传 candidate_id 而非 jd_id，Agent 方向反转

### Agent Feedback
- **D-03:** 审核卡片加「反馈重新匹配」按钮 — 弹出对话框输入自由文本反馈
- **D-04:** 复用 HITL resume 机制 — resume 请求加 feedback 字段，Agent 根据反馈调整后通过 SSE 重新推送结果
- **D-05:** 反馈后 Agent 重新运行匹配，结果通过 SSE 再次流式展示

### PDF/Excel Export
- **D-06:** 后端生成 — reportlab（PDF）和 openpyxl（Excel），确保中文支持
- **D-07:** 匹配结果页「导出」按钮 — 匹配完成后（DONE 状态）显示，提供 PDF 和 Excel 两个选项
- **D-08:** PDF 报告内容：JD 标题、匹配日期、候选人列表（姓名/匹配度/技能对比/审核结果）
- **D-09:** Excel 内容：一个 sheet，列含候选人姓名/匹配度/匹配技能/缺失技能/审核状态/备注

### Carried Forward from Phase 1-4
- SSE 流式匹配基础设施（Phase 4）
- HITL resume 机制（Phase 4）
- Matching 页面和 9-state 状态机（Phase 4）
- Candidate 详情页（Phase 3）
- JD 模型和 API（Phase 2）
- Auth + SQLAlchemy + shadcn/ui（Phase 1）
- FastAPI FileResponse 用于文件下载

### Claude's Discretion
- PDF 具体排版样式（字体大小、表格宽度、页眉页脚）
- Excel 列宽、单元格样式
- 导出按钮的具体位置（匹配结果页底部或顶部）
- 反馈对话框的 placeholder 文案
- reportlab 中文字体注册方式

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project definition
- `.planning/PROJECT.md` — 项目定位、已完成能力
- `.planning/REQUIREMENTS.md` — MATCH-04, APRV-03, DASH-02

### Roadmap & scope
- `.planning/ROADMAP.md` — Phase 5 目标、成功标准、依赖 Phase 4

### Phase 4 matching infrastructure (critical dependency)
- `.planning/phases/04-ai-matching-approval/04-CONTEXT.md` — D-01~D-15 matching/approval/dashboard decisions
- `api/server.py` — POST /recruit/hitl/stream, POST /recruit/hitl/resume, GET /dashboard/stats
- `agent/schemas.py` — CandidateApproval, MatchResult schemas
- `agent/agent.py` — reviewer_agent with per-candidate and feedback support

### Phase 3 candidate infrastructure
- `.planning/phases/03-resume-candidate-management/03-CONTEXT.md` — D-01~D-17, Candidate model/API
- `frontend/src/pages/Candidates.tsx` — CandidateDetail integration point

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `api/server.py` — HITL stream/resume endpoints (add feedback field + reverse matching support)
- `agent/agent.py` — reviewer_agent (add feedback processing), matching pipeline (add reverse direction)
- `frontend/src/pages/Matching.tsx` — matching page (reuse for reverse matching)
- `frontend/src/components/Matching/MatchCandidateCard.tsx` — review card (add feedback button)
- `frontend/src/components/Candidates/CandidateDetail.tsx` — detail page (add reverse match button)
- `agent/schemas.py` — existing schemas (add feedback field)

### New Dependencies (need install)
- `reportlab` — Python PDF generation library
- `openpyxl` — Python Excel generation library

### Integration Points
- 反向匹配按钮挂载到 CandidateDetail 组件
- 反馈按钮挂载到 MatchCandidateCard 组件
- PDF/Excel 导出 API：GET /matching/{session_id}/export/pdf 和 /export/excel
- 导出按钮挂载到 Matching 页面完成状态

</code_context>

<specifics>
## Specific Ideas

- 反向匹配本质是参数反转（传 candidate_id 而非 jd_id），基础设施完全复用
- Agent 反馈是 Phase 4 HITL 的自然扩展（加个字段），不新建独立流程
- 导出在后端做以确保格式统一和中文兼容性
- 三项功能相对独立，可以分计划并行开发

</specifics>

<deferred>
## Deferred Ideas

- 批量导出多个匹配 session → 当前单 session 导出
- 自定义导出模板 → 当前固定格式
- 导出历史记录页面 → 匹配结果页直接导出
- 反向匹配的独立 UI 页面 → 复用正向匹配页面

</deferred>

---

*Phase: 05-advanced-features-export*
*Context gathered: 2026-04-26*
