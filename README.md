# Multi-Agent Recruitment System

基于 **Harness Engineering** 原则构建的多 Agent 智能招聘系统。

> **核心公式：`Agent = Model + Harness`**
> Model 负责推理，Harness 负责将推理转化为可靠的工作产出。

本项目完整实现了 Harness Engineering 四大支柱：**上下文架构**（AGENTS.md + Skills 渐进式披露）、**智能体专业化**（四角色 Agent 分工）、**持久化记忆**（ChromaDB 向量记忆）、**结构化执行**（LangGraph + LangSmith）。

---

## 核心技术亮点

| 技术 | 实现 | Harness 层 |
|------|------|-----------|
| **LangGraph 多 Agent 编排** | Triage → Planner → Worker → Reviewer 状态机 | 结构化执行 |
| **HITL 人机协作** | `interrupt_before` 中断 + `thread_id` 恢复 | 结构化执行 |
| **RAG + API Rerank** | FAISS 粗检索（k×3）→ Cohere/Jina API 二阶段精排 | 工具集成 |
| **ChromaDB 向量记忆** | 语义搜索历史 + 相似候选人推荐 | 持久化记忆 |
| **Skills 渐进式披露** | 按需加载技能，对抗 Context Rot | 上下文架构 |
| **MCP 外部工具接入** | 通过 `mcp_servers.json` 动态扩展工具 | 工具集成 |
| **SSE 流式输出** | `asyncio.Queue` 桥接，节点级实时进度 | 结构化执行 |
| **LangSmith 可观测性** | 全链路追踪 + 运行指标 | 反馈传感器 |

---

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [环境变量配置](#环境变量配置)
- [运行方式](#运行方式)
- [API 接口说明](#api-接口说明)
- [添加简历数据](#添加简历数据)
- [项目结构](#项目结构)
- [常见问题](#常见问题)

---

## 系统要求

- Python 3.11 及以上
- 网络连接（调用 LLM / Embedding / Rerank API）
- OpenAI 兼容 API Key（支持 OpenRouter、aihubmix 等聚合平台）

---

## 快速开始

### 第一步：进入项目目录

```bash
cd hellojobs
```

### 第二步：安装依赖

```bash
pip install -r requirements.txt
```

> 所有依赖均为轻量级 Python 包，无需下载本地模型，安装速度快。

### 第三步：配置 `.env`

项目根目录已有 `.env` 文件，编辑填入你的 API Key：

```bash
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://aihubmix.com/v1   # 或 https://openrouter.ai/api/v1
LLM_MODEL=gpt-4o-mini
```

### 第四步：运行项目

```bash
# CLI 交互模式
python main.py

# 或启动 API 服务
python api/server.py
```

启动 API 服务后，打开 [http://localhost:8000/](http://localhost:8000/) 即可使用前端页面。

---

## 环境变量配置

编辑 `hellojobs/.env`，所有配置项说明如下：

```bash
# LLM（必填）
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://aihubmix.com/v1   # 兼容 OpenRouter / aihubmix 等
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.0

# Embedding（使用同一套 API Key）
EMBEDDING_BACKEND=openai
EMBEDDING_MODEL=text-embedding-3-small

# RAG
RAG_TOP_K=5

# Rerank（可选，默认关闭）
# 开启后使用 Cohere/Jina 兼容接口进行二阶段精排，无需本地模型
RERANK_ENABLED=false
RERANK_MODEL=jina-reranker-v2-base-multilingual
# RERANK_API_URL=https://api.jina.ai/v1/rerank  # 留空则从 OPENAI_BASE_URL 推导
# RERANK_API_KEY=                               # 留空则复用 OPENAI_API_KEY

# ChromaDB 长期记忆
CHROMA_MEMORY_PATH=data/chroma_memory

# LangSmith 追踪（可选）
# LANGSMITH_TRACING=true
# LANGSMITH_API_KEY=你的LangSmith密钥
# LANGSMITH_PROJECT=recruitment-agent

# API 服务
API_HOST=0.0.0.0
API_PORT=8000
```

> **开启 Rerank**：将 `RERANK_ENABLED=true`，确保你的 API 提供商支持 `/v1/rerank` 端点（Jina AI、Cohere、aihubmix 均支持）。

---

## 运行方式

### 方式一：CLI 交互模式

```bash
python main.py
```

启动后输入招聘需求，例如：

```
请输入招聘需求：招聘一个3年经验的Python后端工程师
```

系统会自动：解析岗位要求 → 搜索候选人 → 逐一评分 → 输出推荐报告。

---

### 方式二：API 服务模式

```bash
python api/server.py
```

服务启动后访问：

- **前端界面**：http://localhost:8000/
- **接口文档（Swagger UI）**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

**标准请求：**

```bash
curl -X POST http://localhost:8000/recruit \
  -H "Content-Type: application/json" \
  -d '{"user_input": "招聘3年经验Python工程师"}'
```

**流式请求（SSE 实时进度）：**

```bash
curl -N -X POST http://localhost:8000/recruit/stream \
  -H "Content-Type: application/json" \
  -d '{"user_input": "招聘3年经验Python工程师"}'
```

SSE 事件格式：

```
data: {"event": "status",    "data": {"node": "planner_agent", "status": "completed"}}
data: {"event": "tool_call", "data": {"tool": "search_candidates", "args": {...}}}
data: {"event": "progress",  "data": {"message": "任务规划完成"}}
data: {"event": "result",    "data": {"final_report": "...", "match_results": [...]}}
```

**返回示例：**

```json
{
  "final_report": "推荐候选人：张三（匹配度 85%）...",
  "match_results": [
    {
      "candidate_name": "张三",
      "match_score": 85,
      "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
      "missing_skills": [],
      "recommendation": "强烈推荐",
      "should_proceed": true
    }
  ],
  "classification": "inquiry"
}
```

---

### 方式三：Human-in-the-Loop 模式（HR 审核）

**第一步：启动流程（系统在 Reviewer 前暂停）**

```bash
curl -X POST http://localhost:8000/recruit/hitl/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "招聘Python工程师",
    "thread_id": "session-001"
  }'
```

返回 `"status": "waiting_for_hr"` 表示已暂停，等待 HR 审核。

**第二步：HR 审核后继续**

```bash
curl -X POST http://localhost:8000/recruit/hitl/resume \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "session-001",
    "hr_approved": true,
    "hr_feedback": "张三背景不错，优先安排面试"
  }'
```

---

## API 接口说明

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/` | 前端页面 |
| POST | `/recruit` | 标准招聘流程 |
| POST | `/recruit/stream` | SSE 流式输出（实时进度） |
| POST | `/recruit/hitl/start` | 启动 HITL 流程（HR 审核前暂停） |
| POST | `/recruit/hitl/resume` | 提交 HR 审核结果，恢复流程 |
| GET | `/skills` | 查看所有可用 Skills |
| POST | `/upload-resume` | 上传简历文件（PDF/TXT） |
| POST | `/admin/rebuild-index` | 重建 FAISS 向量索引 |

完整接口文档：启动服务后访问 http://localhost:8000/docs

---

## 添加简历数据

将候选人简历以 `.txt` 或 `.pdf` 格式放入 `data/resumes/` 目录：

```
data/resumes/
├── zhang_san.txt
├── li_si.pdf
└── wang_wu.txt
```

简历建议包含：姓名、邮箱、工作经历、技能列表。

**添加新简历后重建向量索引：**

```bash
# 方式一：删除旧索引，下次运行自动重建
rm -rf data/vector_store

# 方式二：通过 API 重建（服务运行时）
curl -X POST http://localhost:8000/admin/rebuild-index
```

---

## 项目结构

```
hellojobs/
├── AGENTS.md                     # Harness 上下文架构核心文件
├── .env                          # 环境变量配置
├── config.py                     # 全局配置 + init_langsmith()
├── main.py                       # LangGraph 工作流 + CLI 入口
├── mcp_servers.json              # MCP Server 配置
├── requirements.txt              # Python 依赖
│
├── agent/
│   ├── agent.py                  # Triage / Planner / Worker / Reviewer Agent
│   ├── tools.py                  # 工具注册表（含 MCP 动态加载）
│   ├── schemas.py                # Pydantic 状态与数据结构
│   ├── prompt.py                 # 所有 Agent Prompt 模板
│   ├── memory.py                 # ChromaDB 向量记忆 + JSON 降级
│   ├── skills.py                 # Skills 渐进式披露加载器
│   ├── mcp_tools.py              # MCP 客户端工具集成
│   └── observability.py          # LangSmith 追踪 + 运行指标
│
├── rag/
│   ├── vector_store.py           # FAISS 索引构建与加载
│   ├── retriever.py              # RerankRetriever（FAISS + API Rerank）
│   └── reranker.py               # Cohere/Jina 兼容 Rerank API 客户端
│
├── api/
│   └── server.py                 # FastAPI（含 SSE 流式、Skills 管理）
│
├── skills/
│   ├── resume_analysis.md        # 简历解析技能
│   ├── candidate_matching.md     # 候选人匹配评分技能
│   └── report_generation.md      # 报告生成技能
│
├── static/
│   └── index.html                # 前端页面
│
└── data/
    ├── resumes/                  # 简历文件（.txt / .pdf）
    ├── vector_store/             # FAISS 索引（自动生成）
    ├── chroma_memory/            # ChromaDB 候选人记忆（自动生成）
    └── candidate_memory.json     # JSON 降级记忆（自动生成）
```

---

## 常见问题

**Q：如何开启 Rerank 二阶段精排？**

A：在 `.env` 中设置 `RERANK_ENABLED=true`。Rerank 使用 API 调用，不需要本地模型。
默认配置会自动复用 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`（推导为 `/v1/rerank` 端点）。
如果 API 提供商不支持 Rerank，可以显式指定 `RERANK_API_URL=https://api.jina.ai/v1/rerank`，
并单独申请 Jina API Key 填入 `RERANK_API_KEY`。

---

**Q：如何开启 LangSmith 追踪？**

A：在 `.env` 中取消注释以下三行：

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=你的LangSmith密钥
LANGSMITH_PROJECT=recruitment-agent
```

前往 [https://smith.langchain.com](https://smith.langchain.com) 注册并获取 API Key。

---

**Q：HR 审核模式如何使用？**

A：通过前端页面切换到 HR 审核模式，系统会在 Reviewer 前暂停，前端展示候选人卡片和审核面板。也可直接调用 `/recruit/hitl/start` 和 `/recruit/hitl/resume` API。

---

**Q：提示 `No resume .txt or .pdf files found`？**

A：检查 `data/resumes/` 目录下是否有 `.txt` 或 `.pdf` 格式的简历文件。项目已提供 3 份示例简历。

---

**Q：如何添加自定义 MCP 工具？**

A：编辑 `mcp_servers.json`，添加 MCP Server 配置（stdio 或 SSE 传输均支持）。重启服务后自动加载。

```json
{
  "servers": [
    {
      "name": "fetch",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-fetch"]
    }
  ]
}
```

---

**Q：如何换用 OpenAI 官方 Key？**

A：修改 `.env`，去掉 `OPENAI_BASE_URL` 这行：

```bash
OPENAI_API_KEY=sk-你的OpenAI密钥
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

---

**Q：匹配效果不好怎么优化？**

A：
1. 开启 `RERANK_ENABLED=true` 提升检索质量
2. 调高 `RAG_TOP_K`（检索更多候选人）
3. 在 `agent/prompt.py` 中调整评分提示词
4. 更换更强的 LLM 模型
