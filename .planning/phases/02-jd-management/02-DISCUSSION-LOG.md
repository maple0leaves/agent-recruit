# Phase 2: JD Management — Discussion Log

**Date:** 2026-04-26
**Mode:** Interactive (default)

## Areas Discussed

### 1. JD 数据模型设计

| # | Question | Options | Selected | Notes |
|---|----------|---------|----------|-------|
| 1 | JD 包含哪些字段？ | 核心字段 / 完整字段 | 核心字段 (Recommended) | title, department, skills, experience_years, education, salary_min, salary_max, status |
| 2 | department 自由文本还是枚举？ | 自由文本 / 预设枚举 | 自由文本 (Recommended) | HR 自行输入部门名称 |
| 3 | education 自由文本还是枚举？ | 自由文本 / 预设枚举 | 预设学历枚举 | 高中/大专/本科/硕士/博士/不限 |
| 4 | title 命名规范？ | 无约束 / 有规范 | 没有特别命名约束 | |
| 5 | 是否需要 description 字段？ | 需要 / 不需要 | 需要 (Recommended) | 长文本描述岗位职责 |

### 2. JD 列表界面交互

| # | Question | Options | Selected | Notes |
|---|----------|---------|----------|-------|
| 1 | 列表用什么布局？ | 表格 / 卡片 | 表格 (Recommended) | shadcn/ui Table，列：职位/部门/状态/薪资/日期 |
| 2 | 分页方式？ | 传统分页 / 无限滚动 | 传统分页 (Recommended) | 每页 20 条 |
| 3 | 搜索筛选前端还是服务端？ | 服务端 / 前端 | 服务端筛选 (Recommended) | API 传参过滤 |
| 4 | 筛选维度？ | 按状态/按部门/按日期/关键词搜索 | 状态 + 关键词 + 日期 | 多选结果 |

### 3. JD 模板系统

| # | Question | Options | Selected | Notes |
|---|----------|---------|----------|-------|
| 1 | 模板数量和管理方式？ | 3-5预设 / HR自定义 / 不需要 | 3-5 个预设模板 (Recommended) | 硬编码 |
| 2 | 模板预设哪些字段？ | 所有字段 / 仅技能学历 / 仅技能 | 预设所有字段 (Recommended) | HR 填 title + department |
| 3 | 模板存哪里？ | 代码/配置文件 / 数据库表 | 代码/配置文件 (Recommended) | 无需数据库表 |

### 4. JD 状态与生命周期

| # | Question | Options | Selected | Notes |
|---|----------|---------|----------|-------|
| 1 | JD 有哪些状态？ | 三状态 / 两状态 | 三状态 (Recommended) | draft/active/closed，可重新激活 |
| 2 | 编辑权限？ | 不做限制 / 创建者+admin | 不做限制 (Recommended) | 任何登录用户可编辑任意 JD |
| 3 | 已关闭能否重新激活？ | 允许 / 不允许 | 允许 (Recommended) | closed → active |
| 4 | 是否需要删除？ | 只关不删 / 软删除 / 硬删除 | 只关不删 (Recommended) | 无删除功能 |

## Deferred Ideas

- 部门预设枚举列表 — 后续阶段
- HR 可自定义模板 — 后续阶段
- JD 所有权控制 — 后续阶段
- JD 删除功能 — 当前只关不删
- JD 审批流程 — 即时创建无需审批
- 批量导入 JD — v2 范围

## Claude's Discretion Items

- 模板具体包含哪些职位
- skills 逗号分隔格式的具体值
- 列表页表格列的具体顺序和宽度
- 日期范围筛选的 UI 组件
- JD 表单的布局方式
