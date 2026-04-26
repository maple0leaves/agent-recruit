# Requirements: 智能招聘系统 (hellojobs)

**Defined:** 2026-04-26
**Core Value:** HR 能快速、精准地找到符合部门需求的候选人，AI 辅助但不能跳过人的判断

## v1 Requirements

Requirements for initial full-stack release. Each maps to roadmap phases.

### Authentication & Authorization

- [x] **AUTH-01**: HR 可以使用用户名和密码登录系统
- [x] **AUTH-02**: 系统支持角色区分（管理员、招聘专员、部门主管）
- [x] **AUTH-03**: 登录状态持久化，刷新页面不需要重新登录

### JD Management

- [x] **JD-01**: HR 可以在系统里创建新的 JD（职位名称、部门、技能要求、经验要求、薪资范围）
- [x] **JD-02**: HR 可以编辑、关闭已有的 JD
- [x] **JD-03**: HR 可以按部门、状态、日期筛选和搜索 JD 列表
- [x] **JD-04**: 系统提供常用 JD 模板，HR 可以基于模板快速创建

### Resume & Candidate Management

- [ ] **RES-01**: HR 可以上传候选人简历（PDF/Word 格式）
- [ ] **RES-02**: 系统自动解析简历，提取姓名、技能、教育、工作经历等结构化信息
- [ ] **RES-03**: HR 可以查看候选人详情（解析结果、匹配历史、当前状态）
- [ ] **RES-04**: HR 可以搜索候选人库（按姓名、技能、状态）
- [ ] **RES-05**: 候选人状态追踪（新入库 → 筛选中 → 面试 → 录用 → 不合适）

### AI Matching

- [ ] **MATCH-01**: HR 选择一个 JD，系统自动匹配候选人并展示排序结果
- [ ] **MATCH-02**: 匹配结果展示评分和技能逐项对比（候选人匹配的技能 / 缺失的技能）
- [ ] **MATCH-03**: 系统实时流式展示 Agent 匹配过程（Triage → 搜索 → 评分），而不是空白等待
- [ ] **MATCH-04**: HR 可以从候选人侧发起反向匹配（此候选人适合哪些 JD）

### Approval Workflow

- [ ] **APRV-01**: HR 审核匹配结果，可以「通过」或「驳回」每个候选人
- [ ] **APRV-02**: 审核时可填写备注（通过原因 / 驳回理由）
- [ ] **APRV-03**: HR 可以在审核中给 Agent 反馈，让 Agent 重新调整结果

### Dashboard & Export

- [ ] **DASH-01**: 首页仪表盘展示关键指标（活跃 JD 数、候选人总数、待审核数）
- [ ] **DASH-02**: HR 可以将匹配结果导出为 PDF 报告或 Excel 表格

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

- **RES-06**: 批量导入简历（一次上传多个文件）
- **NOTF-01**: 审核完成后通知相关部门主管
- **DASH-03**: 候选人-JD 评分散点图可视化（score vs experience）
- **APRV-04**: HR 和 Agent 之间支持多轮对话式交互（"帮我再找几个有云经验的"）
- **JD-05**: 部门主管可提交用人需求，HR 在系统里审批 JD

## Out of Scope

| Feature | Reason |
|---------|--------|
| 求职者自助门户 | 当前专注 HR 侧，求职者端有独立的复杂性和安全风险 |
| 自动发送面试/婉拒邮件 | 当前模拟工具，真实发送需要独立的消息系统 |
| 多租户 SaaS | PROJECT.md 已明确单企业使用 |
| 内建视频面试 | WebRTC 等基础设施复杂，应接入现有工具 |
| 一键发布到多个招聘网站 | 集成成本高，与核心匹配价值无关 |
| 自定义报表构建器 | 复杂度和维护成本远高于预置报表 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Complete (01-02) |
| AUTH-02 | Phase 1 | Complete (01-02) |
| AUTH-03 | Phase 1 | Complete (01-02) |
| JD-01 | Phase 2 | Complete (02-01) |
| JD-02 | Phase 2 | Complete (02-01) |
| JD-03 | Phase 2 | Complete (02-01) |
| JD-04 | Phase 2 | Complete (02-01) |
| RES-01 | Phase 3 | Pending |
| RES-02 | Phase 3 | Pending |
| RES-03 | Phase 3 | Pending |
| RES-04 | Phase 3 | Pending |
| RES-05 | Phase 3 | Pending |
| MATCH-01 | Phase 4 | Pending |
| MATCH-02 | Phase 4 | Pending |
| MATCH-03 | Phase 4 | Pending |
| MATCH-04 | Phase 5 | Pending |
| APRV-01 | Phase 4 | Pending |
| APRV-02 | Phase 4 | Pending |
| APRV-03 | Phase 5 | Pending |
| DASH-01 | Phase 4 | Pending |
| DASH-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21 ✓
- Unmapped: 0

### Phase Summary

| Phase | Requirements | Count |
|-------|-------------|-------|
| Phase 1: Backend Foundation & Authentication | AUTH-01, AUTH-02, AUTH-03 | 3 |
| Phase 2: JD Management | JD-01, JD-02, JD-03, JD-04 | 4 |
| Phase 3: Resume & Candidate Management | RES-01, RES-02, RES-03, RES-04, RES-05 | 5 |
| Phase 4: AI Matching & Approval | MATCH-01, MATCH-02, MATCH-03, APRV-01, APRV-02, DASH-01 | 6 |
| Phase 5: Advanced Features & Export | MATCH-04, APRV-03, DASH-02 | 3 |

---
*Requirements defined: 2026-04-26*
*Last updated: 2026-04-26 after roadmap creation*
