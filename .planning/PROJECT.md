# 智能招聘系统 (hellojobs)

## What This Is

一个面向企业 HR 部门的多 Agent 智能招聘系统。HR 在系统里管理各部门的招聘需求（JD）和候选人简历，系统自动完成人岗双向匹配、候选人评分排序，HR 审核匹配结果并走审批流程。当前已有完整的 Agent 后端（LangGraph 多 Agent 编排 + RAG 检索管道 + FastAPI），需要补齐配套的前端和产品化功能。

## Core Value

HR 能快速、精准地找到符合部门需求的候选人，审核决策有 AI 辅助但不能跳过人的判断。

## Requirements

### Validated

- ✓ 多 Agent 工作流编排（Triage → Planner → Worker → Reviewer 状态机） — 已有
- ✓ JD 语义检索候选人（FAISS 粗检索 + CrossEncoder 重排） — 已有
- ✓ 简历结构化解析与候选人评分 — 已有
- ✓ ChromaDB 候选人长期记忆与语义搜索 — 已有
- ✓ SSE 流式输出实时进度 — 已有
- ✓ HITL 人机协作流程（中断-审核-恢复） — 已有
- ✓ Skills 渐进式披露系统 — 已有
- ✓ MCP 外部工具动态加载 — 已有
- ✓ LangSmith 全链路追踪 — 已有

### Active

- [ ] **HR-01**: HR 有独立的 Web 管理后台，可以登录访问
- [ ] **HR-02**: HR 可以在系统里创建、编辑、管理各部门的 JD
- [ ] **HR-03**: HR 可以上传、管理候选人简历库
- [ ] **HR-04**: 系统支持双向匹配：JD → 候选人 和 候选人 → JD
- [ ] **HR-05**: HR 可以在界面上审核 Agent 的匹配结果，通过/驳回
- [ ] **HR-06**: 匹配结果可导出为招聘报告（PDF/Excel）
- [ ] **HR-07**: 各部门可提交用人需求，HR 据此发起匹配

### Out of Scope

- 求职者端功能（求职者注册、投递简历） — 当前专注 HR 侧
- 多租户 SaaS — 当前单企业使用
- 自动发送面试邮件/短信 — 当前仅人审核，后续可接入

## Context

- 技术基础：Python 3.12 + LangChain/LangGraph + FastAPI + FAISS + ChromaDB
- 当前有一个简陋的 `static/index.html` 前端，仅作调试用
- Agent 核心能力已验证（匹配精度、评估体系已有 benchmark）
- 数据格式已有成熟的 Pydantic schema 定义
- FAISS 索引和 ChromaDB 记忆的持久化机制已完善

## Constraints

- **技术栈**: 后端继续 Python/FastAPI，前端待选型（React/Vue）
- **数据**: 简历和 JD 数据目前是本地文件，暂不考虑大规模分布式
- **安全**: 需要加登录认证，目前 API 无任何鉴权

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 后端保持 FastAPI | 已有完整的 API 层，无需重写 | — Pending |
| 前端新建 SPA | 当前 static/index.html 过于简陋，不适合做产品 | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-26 after initialization*
