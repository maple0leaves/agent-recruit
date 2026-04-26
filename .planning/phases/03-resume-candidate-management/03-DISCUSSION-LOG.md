# Phase 3: Resume & Candidate Management — Discussion Log

**Date:** 2026-04-26
**Mode:** Interactive (default)

## Areas Discussed

### 1. 简历上传与解析流程

| # | Question | Options | Selected | Notes |
|---|----------|---------|----------|-------|
| 1 | 复用已有 Agent 还是独立解析？ | 复用Agent / 独立函数 | 复用已有 Agent (Recommended) | 已有 CandidateInfo schema |
| 2 | 文件格式和大小？ | PDF+Word / 仅PDF | PDF + Word (Recommended) | 最大 10MB |
| 3 | 同步还是异步解析？ | 同步 / 异步+轮询 | 同步解析 (Recommended) | 3-10 秒等待 |
| 4 | 解析预览展示方式？ | 展示+可编辑 / 仅展示 | 展示+可编辑 (Recommended) | HR 可修正 |
| 5 | 解析失败怎么处理？ | 允许手动补填 / 必须重传 | 允许手动补填 (Recommended) | 不阻塞流程 |

### 2. 候选人数据模型设计

| # | Question | Options | Selected | Notes |
|---|----------|---------|----------|-------|
| 1 | 数据模型字段？ | 标准字段 / 完整字段 | 标准字段 (Recommended) | name/email?/phone?/skills/education/experience/status/resume_file/parsed_at |
| 2 | Pipeline 状态值？ | 5状态 / 更细粒度 | new/screening/interview/hired/rejected | RES-05 一致性 |

### 3. 候选人列表与详情界面

| # | Question | Options | Selected | Notes |
|---|----------|---------|----------|-------|
| 1 | 列表布局？ | 表格 / 卡片 | 表格 (Recommended) | 与 JD 列表一致 |
| 2 | 搜索/筛选维度？ | 姓名/技能/状态 | 姓名+技能+状态 (全部) | 多选结果 |
| 3 | 详情页布局？ | 单页滚动 / Tab切换 | 单页滚动 (Recommended) | 解析数据+匹配历史+状态操作 |
| 4 | 行点击行为？ | 详情=编辑 / 只读+编辑按钮 | 详情=编辑 (Recommended) | 减少步骤 |
| 5 | 匹配历史处理？ | 占位提示 / 不显示 | 占位提示 (Recommended) | "暂无匹配记录" |

### 4. Pipeline 状态与生命周期

| # | Question | Options | Selected | Notes |
|---|----------|---------|----------|-------|
| 1 | 终态是否可逆？ | 终态不可逆 / 终态可逆 | 终态不可逆 (Recommended) | hired/rejected 为终态 |
| 2 | 状态变更需要备注？ | 需要 / 不需要 | 需要备注 (Recommended) | 必填 |
| 3 | 能否删除？ | 只关不删 / 支持删除 | 只关不删 (Recommended) | 始终保留 |

## Deferred Ideas

- 异步简历解析 — Phase 3 用同步
- 批量上传简历 — v2 RES-06
- 候选人删除 — 只保留不删
- 简历 BLOB 存储 — 当前存路径
- 更细粒度 Pipeline 状态 — 5 状态够用
- 候选人头像提取 — 超出范围
- 卡片布局 — 用标准表格

## Claude's Discretion Items

- 简历存储目录名称
- 解析超时秒数
- 候选人与简历文件关系（1:1 / 1:N）
- 上传进度 UI 细节
- 详情页区域排布
