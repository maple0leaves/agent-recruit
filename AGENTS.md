# AGENTS.md — AI 招聘系统 Harness 说明书

本文件是 Harness Engineering 上下文架构（Context Architecture）的核心组件。
Agent 在每次会话开始时注入本文件，以获取项目规范、约束和历史经验。

---

## 项目定位

基于 **Harness Engineering** 原则构建的多 Agent 智能招聘系统。
公式：`Agent = Model + Harness`

本系统的 Harness 层包括：
- **LangGraph 状态机**：强制执行 Triage → Planner → Worker → Reviewer 序列
- **Skills 渐进式披露**：按需加载技能，避免上下文腐烂（Context Rot）
- **ChromaDB 向量记忆**：跨会话持久化候选人历史，支持语义召回
- **CrossEncoder Rerank**：RAG 二阶段精排，工具输出质量优先
- **LangSmith 可观测性**：每步追踪，反馈传感器（Feedback Sensor）
- **MCP 工具扩展**：通过 `mcp_servers.json` 动态接入外部能力

---

## 目录结构

```
hellojobs/
├── agent/
│   ├── agent.py          # 四个 Agent 节点实现（Triage/Planner/Worker/Reviewer）
│   ├── tools.py          # 工具注册表（含 MCP 动态加载）
│   ├── memory.py         # ChromaDB 向量记忆 + JSON 降级
│   ├── skills.py         # Skills 渐进式披露加载器
│   ├── observability.py  # LangSmith 追踪 + 运行指标
│   ├── prompt.py         # 所有 Agent 的 Prompt 模板
│   └── schemas.py        # Pydantic 数据模型（状态/输入/输出）
├── rag/
│   ├── vector_store.py   # FAISS 索引构建与加载
│   ├── retriever.py      # RerankRetriever（FAISS + CrossEncoder）
│   └── reranker.py       # CrossEncoder 重排序模块
├── api/
│   └── server.py         # FastAPI：/recruit, /recruit/stream, /skills, /health
├── skills/
│   ├── resume_analysis.md      # 简历解析技能
│   ├── candidate_matching.md   # 候选人匹配评分技能
│   └── report_generation.md    # 招聘报告生成技能
├── data/
│   ├── resumes/          # 简历文件目录（.txt / .pdf）
│   ├── vector_store/     # FAISS 索引持久化
│   └── chroma_memory/    # ChromaDB 候选人历史记忆
├── main.py               # LangGraph 构建 + CLI 入口
├── config.py             # 全局配置（含 init_langsmith）
├── mcp_servers.json      # MCP Server 配置
├── .env                  # 环境变量（不提交到 git）
└── AGENTS.md             # 本文件
```

---

## Agent 工作流

```
用户输入
  │
  ▼
triage_router ──→ single_resume_agent ──→ END（单简历直通）
  │
  ▼（inquiry 分类）
planner_agent ──→ worker_agent（工具执行）
  │   ↑__________________|（循环直到有评分结果）
  ▼
reviewer_agent ──→ END（生成最终报告）
  ↑
  │ HITL 中断点（use_hitl=True 时，HR 审核后恢复）
```

---

## 工具列表

| 工具名 | 功能 | 类型 |
|--------|------|------|
| `search_candidates` | FAISS+Rerank 语义检索简历 | 内置 |
| `analyze_resume` | LLM 结构化解析简历 → CandidateInfo | 内置 |
| `score_match` | 候选人与 JD 匹配评分 → MatchResult | 内置 |
| `query_candidate_history` | ChromaDB 精确查询候选人历史 | 内置 |
| `send_interview_invite` | 发送面试邀请（模拟） | 内置 |
| `send_rejection_email` | 发送婉拒邮件（模拟） | 内置 |
| MCP 工具 | 由 `mcp_servers.json` 动态加载 | 外部 |

> 工具输出占 Agent 上下文的 67.6%（LangChain 数据），优化工具输出格式比优化 prompt 更重要。

---

## Skills 系统

Skills 实现**渐进式披露（Progressive Disclosure）**，对抗上下文腐烂：
- 启动时不加载所有工具描述
- 根据当前任务描述，按需激活匹配的 Skill
- 每个 Skill 包含：关联工具、触发条件、执行步骤、质量检查

新增 Skill：在 `skills/` 目录创建 `.md` 文件，遵循 frontmatter 格式：
```markdown
---
name: skill_name
description: 技能描述
tools: [tool1, tool2]
trigger: 触发关键词描述
---
执行步骤和质量检查...
```

---

## 记忆系统

### 短期记忆
LangGraph `messages` 状态字段 + `InMemorySaver` checkpoint，自动管理当前会话。

### 长期记忆（ChromaDB）
- 每次 Reviewer 生成报告后，自动写入 ChromaDB 和 JSON 双写
- `get_candidate_history(name)` — 精确查询
- `search_memory(query)` — 语义搜索历史（新增）
- `search_candidate_similar(name)` — 找相似经历的候选人（新增）
- ChromaDB 不可用时自动降级为 JSON 模式

---

## API 端点

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/recruit` | 标准招聘工作流 |
| POST | `/recruit/stream` | SSE 流式输出（实时进度） |
| POST | `/recruit/hitl/start` | HITL 流程启动（HR 审核前暂停） |
| POST | `/recruit/hitl/resume` | HITL 流程恢复（提交 HR 决策） |
| GET  | `/skills` | 查看所有可用 Skills |
| POST | `/upload-resume` | 上传简历文件（PDF/TXT） |
| POST | `/admin/rebuild-index` | 重建 FAISS 向量索引 |
| GET  | `/health` | 健康检查 |

---

## 环境变量速查

```bash
# LLM
OPENAI_API_KEY=        # API 密钥
OPENAI_BASE_URL=       # 兼容接口地址（OpenRouter/AiHubMix 等）
LLM_MODEL=             # 模型名称

# RAG Rerank
RERANK_ENABLED=false   # 改为 true 开启 CrossEncoder 重排
RERANK_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# ChromaDB
CHROMA_MEMORY_PATH=data/chroma_memory

# LangSmith（可选）
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=     # 填入后自动激活追踪
LANGSMITH_PROJECT=recruitment-agent
```

---

## 已知约束与经验（AI 曾犯过的错误）

1. **工具调用必须等待结果**：Worker Agent 执行工具后必须回到 Planner，
   不能直接跳转到 Reviewer，否则 match_results 为空。

2. **ChromaDB 查询需检查 count()**：在 `query()` 前先检查集合数量，
   `n_results` 不能大于文档总数，否则报错。

3. **MCP 工具不覆盖内置工具**：`_merge_mcp_tools` 中内置工具名称优先，
   同名 MCP 工具自动跳过。

4. **SSE 流不能用 list() 阻塞**：`graph.stream()` 必须通过
   `asyncio.Queue` 桥接，不能用 `list()` 包裹，否则流式完全失效。

5. **Rerank 使用 API 模式**：不依赖本地模型，通过 `RERANK_API_URL`
   调用 Cohere/Jina 兼容接口。默认复用 `OPENAI_API_KEY`，
   `RERANK_ENABLED=false` 时直接跳过，无任何额外开销。

---

## Harness Engineering 四大支柱对照

| 支柱 | 本项目实现 |
|------|-----------|
| 上下文架构 | AGENTS.md + Skills 渐进式披露 |
| 智能体专业化 | Triage/Planner/Worker/Reviewer 四角色 |
| 持久化记忆 | ChromaDB 向量记忆 + JSON 双写 |
| 结构化执行 | LangGraph 强制流程 + LangSmith 反馈传感器 |
