# Multi-Agent Recruitment System

基于 **Harness Engineering** 原则构建的多 Agent 智能招聘系统。

> **核心公式：`Agent = Model + Harness`**
> Model 负责推理，Harness 负责将推理转化为可靠的工作产出。

---

## 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [环境变量配置](#环境变量配置)
- [运行方式](#运行方式)
- [前端开发](#前端开发)
- [API 接口说明](#api-接口说明)
- [添加简历数据](#添加简历数据)
- [项目结构](#项目结构)
- [常见问题](#常见问题)

---

## 系统要求

- Python 3.11+
- Node.js 18+（前端开发需要）
- 网络连接（调用 LLM / Embedding / Rerank API）
- OpenAI 兼容 API Key

---

## 快速开始

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 `.env`

项目根目录已有 `.env`，按需编辑（详见[环境变量配置](#环境变量配置)）：

```bash
OPENAI_API_KEY=你的密钥
JWT_SECRET=你的JWT密钥（32字节Hex）
ADMIN_PASSWORD=你的管理员密码
```

### 3. 初始化数据库

```bash
python -m backend.db.seed
```

### 4. 启动服务

```bash
python api/server.py
```

打开 http://localhost:8000/ ，使用配置的管理员账号登录。

---

## 环境变量配置

编辑 `.env` 文件：

```ini
# ── LLM ──────────────────────────────────────────────────
OPENAI_API_KEY=你的密钥
OPENAI_BASE_URL=https://aihubmix.com/v1
LLM_MODEL=gpt-5.4-mini
LLM_TEMPERATURE=0.0

# ── Embedding ────────────────────────────────────────────
EMBEDDING_BACKEND=openai
EMBEDDING_MODEL=text-embedding-3-small

# ── RAG ──────────────────────────────────────────────────
VECTOR_STORE_PATH=data/vector_store
RESUME_DIR=data/resumes
RAG_TOP_K=5

# ── Rerank（可选）────────────────────────────────────────
RERANK_ENABLED=false
RERANK_MODEL=jina-reranker-v2-base-multilingual

# ── API 服务 ─────────────────────────────────────────────
API_HOST=0.0.0.0
API_PORT=8000

# ── 数据库 ───────────────────────────────────────────────
DATABASE_URL=sqlite+aiosqlite:///./data/dev.db

# ── JWT 认证 ─────────────────────────────────────────────
JWT_SECRET=你的32字节Hex密钥
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── CORS ─────────────────────────────────────────────────
CORS_ORIGINS=http://localhost:5173,http://localhost:8000

# ── 种子用户 ─────────────────────────────────────────────
ADMIN_USERNAME=admin
ADMIN_PASSWORD=你的管理员密码

# ── LangSmith 追踪（可选）────────────────────────────────
# LANGSMITH_TRACING=true
# LANGSMITH_API_KEY=你的LangSmith密钥
# LANGSMITH_PROJECT=recruitment-agent
```

---

## 运行方式

### 方式一：API 服务 + 前端（推荐）

```bash
python api/server.py
```

- 前端页面：http://localhost:8000/
- API 文档（Swagger）：http://localhost:8000/docs

### 方式二：CLI 交互模式

```bash
python main.py
```

输入招聘需求，系统自动解析岗位 → 搜索候选人 → 评分 → 输出推荐报告。

### 方式三：前端开发模式

```bash
cd frontend && npm install && npm run dev
```

启动 Vite 开发服务器（http://localhost:5173），API 请求自动代理到后端 :8000，支持热更新。

---

## 前端开发

前端使用 React 19 + TypeScript + Tailwind CSS 4 + shadcn/ui。

```bash
cd frontend
npm install        # 安装依赖
npm run dev        # 开发模式（热更新，端口 5173）
npm run build      # 生产构建（输出到 ../static/）
```

**技术栈：**

| 类别 | 技术 |
|------|------|
| 框架 | React 19 + TypeScript |
| 构建 | Vite 8 |
| 样式 | Tailwind CSS 4 + shadcn/ui |
| 路由 | React Router 7 |
| 状态管理 | Zustand |
| 数据请求 | TanStack React Query + Axios |
| 实时通信 | SSE（流式匹配结果） |

**前端页面路由：**

| 路径 | 页面 | 说明 |
|------|------|------|
| `/login` | 登录 | 公共页面 |
| `/dashboard` | 仪表盘 | 活跃职位/候选人/待审核统计 |
| `/jd` | 职位管理 | 创建、编辑、筛选职位 |
| `/candidates` | 候选人管理 | 上传简历、管理应聘流程 |
| `/matching` | 智能匹配 | 选择职位发起 AI 匹配 |
| `/matching/:jdId` | 匹配详情 | 针对特定职位的匹配会话 |

---

## API 接口说明

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户名+密码登录，返回 access_token + 设置 refresh_token cookie |
| POST | `/api/auth/logout` | 登出，清除 cookie |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 职位管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/jd` | 分页列表，支持 status / keyword / date 筛选 |
| POST | `/api/jd` | 创建职位 |
| GET | `/api/jd/{id}` | 获取职位详情 |
| PUT | `/api/jd/{id}` | 更新职位 |
| PATCH | `/api/jd/{id}/status` | 更新职位状态 |
| GET | `/api/jd/templates` | 获取职位模板 |

### 候选人管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/candidates` | 分页列表，支持 status / keyword 筛选 |
| POST | `/api/candidates/upload` | 上传简历（PDF/DOCX），自动解析 |
| GET | `/api/candidates/{id}` | 获取候选人详情 |
| PUT | `/api/candidates/{id}` | 更新候选人信息 |
| PATCH | `/api/candidates/{id}/status` | 更新应聘流程状态 |

### AI 匹配

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/recruit` | 标准招聘流程（同步） |
| POST | `/api/recruit/stream` | SSE 流式招聘流程 |
| POST | `/api/recruit/hitl/start` | 启动 HITL 流程（HR 审核前暂停） |
| POST | `/api/recruit/hitl/resume` | 提交 HR 审核并继续 |
| POST | `/api/recruit/hitl/stream` | SSE 流式 HITL 匹配 |
| POST | `/api/recruit/hitl/reverse-stream` | SSE 反向匹配（按候选人找职位） |

### 仪表盘 & 导出

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/dashboard/stats` | 仪表盘统计（活跃职位/候选人/待审核） |
| GET | `/api/matching/{session_id}/export/pdf` | 导出匹配报告 PDF |
| GET | `/api/matching/{session_id}/export/excel` | 导出匹配报告 Excel |

### 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/skills` | 查看所有可用技能 |
| POST | `/api/admin/rebuild-index` | 重建 FAISS 向量索引 |

### SSE 事件格式

流式接口返回 Server-Sent Events：

```
data: {"event": "status",     "data": {"node": "planner_agent", "status": "completed"}}
data: {"event": "tool_call",  "data": {"tool": "search_candidates", "args": {...}}}
data: {"event": "progress",   "data": {"message": "任务规划完成"}}
data: {"event": "match_result","data": {"candidate_name": "张三", "match_score": 85, ...}}
data: {"event": "result",     "data": {"final_report": "...", "match_results": [...]}}
data: {"event": "done",       "data": {}}
```

---

## 添加简历数据

将候选人简历（`.txt` 或 `.pdf`）放入 `data/resumes/` 目录：

```
data/resumes/
├── zhang_san.txt
├── li_si.pdf
└── wang_wu.txt
```

添加后重建向量索引：

```bash
# 方式一：删除旧索引，下次启动自动重建
rm -rf data/vector_store

# 方式二：通过 API 重建
curl -X POST http://localhost:8000/api/admin/rebuild-index
```

---

## 项目结构

```
hellojobs/
├── main.py                       # LangGraph 工作流定义 + CLI 入口
├── config.py                     # 全局配置
├── requirements.txt              # Python 依赖
├── mcp_servers.json              # MCP 服务器配置
├── .env                          # 环境变量
│
├── agent/                        # AI 智能体核心
│   ├── agent.py                  # Triage / Planner / Worker / Reviewer
│   ├── tools.py                  # 工具注册表（含 MCP 动态加载）
│   ├── schemas.py                # Pydantic 状态与数据结构
│   ├── prompt.py                 # Agent Prompt 模板
│   ├── memory.py                 # ChromaDB 向量记忆
│   ├── skills.py                 # Skills 渐进式披露
│   ├── mcp_tools.py              # MCP 客户端集成
│   └── observability.py          # LangSmith 追踪
│
├── api/
│   └── server.py                 # FastAPI（SSE 流式、SPA fallback）
│
├── backend/
│   ├── api/
│   │   ├── deps.py               # 依赖注入（get_db, get_current_user）
│   │   └── routes/
│   │       ├── auth.py           # 认证端点（JWT login/logout/me）
│   │       ├── jd.py             # 职位 CRUD
│   │       └── candidate.py      # 候选人 CRUD
│   ├── auth/
│   │   ├── jwt.py                # JWT 令牌
│   │   └── password.py           # bcrypt 密码哈希
│   ├── config/
│   │   └── templates.py          # 职位模板
│   ├── db/
│   │   ├── engine.py             # SQLAlchemy 异步引擎
│   │   ├── seed.py               # 管理员种子脚本
│   │   ├── migrations/           # Alembic 迁移
│   │   └── models/               # User, JD, Candidate, MatchSession
│   └── export/
│       ├── pdf.py                # ReportLab PDF 导出
│       └── excel.py              # openpyxl Excel 导出
│
├── rag/                          # RAG 检索增强
│   ├── vector_store.py           # FAISS 索引
│   ├── retriever.py              # 检索器（含 rerank）
│   └── reranker.py               # Cohere/Jina 兼容 rerank 客户端
│
├── skills/                       # Markdown 技能定义
├── data/                         # 运行时数据（gitignore）
│   ├── resumes/                  # 简历文件
│   └── vector_store/             # FAISS 索引（自动生成）
├── static/                       # 前端构建产物
│
└── frontend/                     # React 前端
    ├── package.json
    ├── vite.config.ts            # Vite 配置（代理 + 别名）
    └── src/
        ├── main.tsx              # 入口
        ├── App.tsx               # 路由定义
        ├── pages/                # Login, Dashboard, JDManagement, Candidates, Matching
        ├── components/           # UI 组件（shadcn/ui + 业务组件）
        ├── api/                  # Axios 客户端 + API 调用
        ├── hooks/                # useAuth, useJDs, useCandidates, useMatchingSSE
        ├── store/                # Zustand 认证状态
        └── types/                # TypeScript 类型定义
```

---

## 常见问题

**Q：前端打开白屏？**

A：检查是否在端口 8000 访问且静态文件是旧的。运行 `cd frontend && npm run build` 重新构建。

**Q：点击匹配后报 401 Unauthorized？**

A：确认已登录。匹配接口（SSE）使用 `fetch()` 而非 axios，依赖 `refresh_token` cookie 认证（path=`/api`）。

**Q：提示 `No resume .txt or .pdf files found`？**

A：检查 `data/resumes/` 目录下是否有简历文件。添加后运行 `rm -rf data/vector_store` 触发重建。

**Q：匹配效果不好怎么优化？**

A：1) 开启 `RERANK_ENABLED=true`；2) 调高 `RAG_TOP_K`；3) 在 `agent/prompt.py` 调整评分提示词；4) 换用更强 LLM 模型。

**Q：如何换用 OpenAI 官方 Key？**

A：修改 `.env`，去掉 `OPENAI_BASE_URL`：

```bash
OPENAI_API_KEY=sk-你的OpenAI密钥
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

