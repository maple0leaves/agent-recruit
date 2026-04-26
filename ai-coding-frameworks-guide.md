# AI 编程框架深度解析：Planning with Files、GSD、Superpowers 与 gstack

> 截至 2026 年 4 月，这些方法论代表了 AI 辅助软件开发领域的不同哲学路线。其中 Planning with Files 是底层基础设施，GSD、Superpowers、gstack 是建立在其上的三大代表性框架。

---

## 0. Planning with Files（基础方法论）

### 背景：200 亿美元的方法论

2025 年 12 月，Meta 以 **200 亿美元收购了 AI 创业公司 Manus**，其核心创新就是"上下文工程"——用 Markdown 文件给 AI 代理提供持久工作记忆。Planning with Files 是这套哲学的**开源实现**。

### 核心类比

> **上下文窗口 = 内存（RAM）**——快、易失、容量有限  
> **文件系统 = 硬盘**——持久、无限容量、结构化

"AI 不会因为上下文太短而失败，它们失败是因为不知道如何管理遗忘。"

### 三文件核心系统

面对复杂任务时，AI 代理维护三个 Markdown 文件：

| 文件 | 脑科学类比 | 职责 |
|------|-----------|------|
| `task_plan.md` | 前额叶皮层（执行控制） | 追踪阶段、目标、决策、错误和进度。代理在每次重大决策前重读此文件，作为"注意力锚点" |
| `findings.md` | 海马体（长期记忆） | 存储调研发现、API 发现、代码分析结果。避免重复搜索或反复读取大量历史对话 |
| `progress.md` | 会话日志 | 记录实际完成的操作、测试结果等 |

### 解决了什么

1. **记忆丢失** — 上下文重置不会清除任务状态，文件就是持久记忆
2. **目标漂移** — 50+ 次工具调用后，重读 `task_plan.md` 重新锚定原始目标
3. **重复犯错** — 所有错误被显式记录并分析，避免重现
4. **上下文膨胀** — 信息按类别归入专用文件，而非全部塞进上下文

### 安装（Claude Code 插件）

```bash
/plugin marketplace add OthmanAdi/planning-with-files
/plugin install planning-with-files@planning-with-files
```

### 与三大框架的关系

Planning with Files 是更底层的基础设施——**GSD、Superpowers、gstack 都在不同程度上实现了这个模式**：

- GSD 的 `PROJECT.md` / `STATE.md` / `PLAN.md` / `REQUIREMENTS.md` 就是一套复杂的文件记忆系统
- Superpowers 的 `writing-plans` 技能生成结构化的计划文件，brainstorm 技能也输出文件
- gstack 的角色技能链中间产物本质上也是文件传递

可以说 **Planning with Files 是三大框架的共同思想源头**。

---

## 1. GSD（Get Shit Done）

### 是什么

GSD 是由 **TÂCHES** 团队构建的轻量级规范驱动开发系统，专为独立开发者和中小团队使用 AI 编程助手而设计。截至 2026 年 4 月，拥有 **52,000+ GitHub Stars**，被 Amazon、Google、Shopify、Webflow 等公司的工程师使用。

**安装：** `npx get-shit-done-cc@latest`

### 解决的核问题：上下文腐烂（Context Rot）

随着 AI 编程会话变长，上下文窗口中的"垃圾"会累积，导致代码质量下降。GSD 的解决方案是将工作分解为小的原子阶段，每个阶段在**全新的 200k token 上下文窗口**中执行。

### 核心工作流（6 步循环）

```
初始化 → 讨论 → 计划 → 执行 → 验证 → 交付
```

| 步骤 | 命令 | 作用 |
|------|------|------|
| 初始化 | `/gsd-new-project` | 深度提问 → 调研 → 需求书 → 路线图 |
| 讨论 | `/gsd-discuss-phase N` | 在规划前捕获实现偏好（布局、API 形态、错误处理） |
| 计划 | `/gsd-plan-phase N` | 调研领域 → 创建 2-3 个原子化 XML 结构任务计划 |
| 执行 | `/gsd-execute-phase N` | 按 wave 并行执行，每个任务一个原子 git commit |
| 验证 | `/gsd-verify-work N` | 用户验收测试，自动诊断失败，生成修复计划 |
| 交付 | `/gsd-ship N` | 创建 PR，完成里程碑 |

### 关键创新

- **上下文工程**：将项目知识分散到 `PROJECT.md`、`REQUIREMENTS.md`、`ROADMAP.md`、`STATE.md`、`PLAN.md` 等文件中，按需加载
- **XML 计划格式化**：每个任务用 XML 结构描述（文件路径、操作、验证方式）
- **Wave 并行执行**：基于依赖分析的 wave 分组，独立任务并行执行
- **多代理编排**：12 个专业子代理负责调研、规划、执行和验证
- **原子 Git 提交**：每个任务一个 commit，可追溯、可回滚

### 哲学

> "没有企业角色扮演的废话。没有 sprint 仪式、story points、stakeholder 同步或 Jira 工作流。只是一个极其高效的系统，用于持续构建酷的东西。"

---

## 2. Superpowers

### 是什么

Superpowers 是由 **Jesse Vincent 和 Prime Radiant 团队**构建的 AI 编程代理技能框架。2025 年 10 月发布，五个月内突破 **107,000+ GitHub Stars** 和 8,600 个 Fork，是增长最快的开发者工具仓库之一。

**仓库：** `github.com/obra/superpowers`

### 核心理念

将"写代码"转变为**严格的流水线工程**，AI 代理必须先思考、再设计、再执行，每一步都有硬性关卡：

```
头脑风暴 → Git Worktree 隔离 → 编写计划 → 子代理驱动开发 → TDD → 代码审查 → 完成
```

### 14 个核心技能

| 技能 | 功能 |
|------|------|
| `brainstorming` | 苏格拉底式提问，将模糊想法打磨为清晰设计文档 |
| `writing-plans` | 将工作拆分为 2-5 分钟的小任务，精确到文件路径和命令 |
| `test-driven-development` | 强制 RED-GREEN-REFACTOR 循环，不写测试不能写代码 |
| `subagent-driven-development` | 每个任务由独立子代理执行，含两阶段代码审查 |
| `systematic-debugging` | 系统化四阶段根因分析 |
| `dispatching-parallel-agents` | 多个独立子代理并行处理 |
| `using-git-worktrees` | 创建隔离开发分支，保护主分支 |
| `requesting-code-review` / `receiving-code-review` | 代码审查协作 |
| `verification-before-completion` | 完成前必须运行验证命令 |
| `finishing-a-development-branch` | 开发分支生命周期管理 |
| `writing-skills` | 自定义技能创建（元技能） |

### 跨平台支持

支持 **Claude Code、OpenAI Codex CLI、Cursor、OpenCode、GitHub Copilot CLI、Gemini CLI** 等主流 AI 编程工具。

### 对比 GSD

| 维度 | Superpowers | GSD |
|------|-------------|-----|
| 核心理念 | 流程即真理（TDD 驱动） | 上下文管理 |
| 质量控制 | 强制 TDD + 代码审查 | XML 验证任务 + 质量关卡 |
| 隔离机制 | Git Worktree | 全新上下文窗口 |
| 最佳场景 | 长时间自主开发、并行代理 | 马拉松式多日会话 |

---

## 3. gstack

### 是什么

gstack 是由 **Garry Tan**（Y Combinator 总裁兼 CEO）构建的开源专业化工作流技能集合。它将 Claude Code 转变为一个拥有 **23+ 专业角色**的虚拟工程团队，拥有 **71,000+ GitHub Stars**，MIT 协议开源。

**仓库：** `github.com/garrytan/gstack`

### 核心理念：「一支团队，而不仅是一个副驾驶」

gstack 将 AI 编程模拟为一个**完整的工程组织**：

| 角色 | 命令 | 作用 |
|------|------|------|
| YC 合伙人 | `/office-hours` | 产品重构，六个强制问题 |
| CEO | `/plan-ceo-review` | 范围验证（扩展/选择/暂缓/削减） |
| 工程经理 | `/plan-eng-review` | 锁定架构、映射数据流、列举边界情况 |
| 高级工程师 | `/review` | 发现生产 Bug，自动修复明显问题 |
| QA 负责人 | `/qa` | 真实的 Chromium 浏览器测试（基于 Playwright） |
| 发布工程师 | `/ship` | 一键部署 + 覆盖率审计 |
| 安全官 | `/cso` | OWASP + STRIDE 安全审计 |
| SRE | `/canary` | 部署后监控循环 |

### 关键技术创新

- **持久浏览器守护进程**：长生命周期的无头 Chromium 进程（Bun + Playwright），约 100ms 响应时间，状态跨命令持久化
- **基于角色的治理**：每个专业角色相互隔离，工程师看不到产品路线图，QA 看不到实现细节
- **Conductor 并行引擎**：最多 10+ 个 Claude Code 会话同时运行在隔离工作区
- **Diff-Aware QA**：分析 git diff 识别受影响路由，只测试变更部分
- **技能链流水线**：`/office-hours` → `/plan-ceo-review` → `/plan-eng-review` → 实现 → `/review` → `/qa` → `/ship`
- **跨模型审查**：`/codex` 调用 OpenAI Codex CLI 进行独立代码审查

### sprint 结构

```
思考 → 计划 → 构建 → 审查 → 测试 → 交付 → 反思
```

---

## 三者对比总结

| 维度 | GSD | Superpowers | gstack |
|------|-----|-------------|--------|
| **创建者** | TÂCHES | Jesse Vincent (obra) | Garry Tan (YC) |
| **Stars (~)** | ~52K | ~107K | ~71K |
| **哲学** | 上下文管理 + 规范驱动 | TDD 纪律至上 | 角色分权治理 |
| **核心机制** | 全新上下文窗口 / Wave 并行 | 强制 TDD + Git Worktree | 23+ 虚拟角色 / 浏览器守护进程 |
| **代理数** | 12+ | 6 | 7 |
| **最佳场景** | 马拉松多日开发 | 单人项目 + 测试驱动 | 创始人快速交付产品 |
| **学习曲线** | 中等 | 中高 | 中等 |
| **独特卖点** | 上下文腐烂的终极解 | 不写测试不能写代码 | 模拟整支工程团队 |

### 如何选择

- **选 GSD**：如果你需要连续多日开发大型特性，担心 AI 质量随对话变长而下降
- **选 Superpowers**：如果你重视代码质量和测试覆盖率，愿意接受强约束的 TDD 流程
- **选 gstack**：如果你是独立创始人要从 0 到 1 交付产品，需要产品思考 + 工程执行的全套角色

三者并不互斥——可以组合使用。例如用 GSD 规划阶段，用 Superpowers 执行 TDD，用 gstack 做代码审查和 QA。

---

## 资料来源

- [GitHub - OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files)
- [Planning with Files - EveryDev.ai](https://www.everydev.ai/tools/planning-with-files)
- [GitHub - gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)
- [GitHub - obra/superpowers](https://github.com/obra/superpowers)
- [GitHub - garrytan/gstack](https://github.com/garrytan/gstack)
- [GSD for Claude Code: A Deep Dive (codecentric)](https://www.codecentric.de/en/knowledge-hub/blog/the-anatomy-of-claude-code-workflows-turning-slash-commands-into-an-ai-development-system)
- [Superpowers, GSD, and GSTACK: Picking the Right Framework (Pulumi)](https://www.pulumi.com/blog/claude-code-orchestration-frameworks/)
- [gstack vs Superpowers vs AEGIS — 3 Philosophies (dev.to)](https://dev.to/th19930828/gstack-vs-superpowers-vs-aegis-3-philosophies-of-ai-agent-systems-o05)
