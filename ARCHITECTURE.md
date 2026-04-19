# 真正落地出来的图

这个文件汇总当前 `hellojobs` 项目已经落地实现的三张核心结构图，方便和最初的 `demo.md` 目标架构对照查看。

## 1. 主工作流图

当前系统的主流程是一个 LangGraph 编排链路，核心入口在 `main.py`，节点实现主要在 `agent/agent.py`。

```mermaid
flowchart TD
    A["START"] --> B["triage_router"]

    B -->|inquiry| C["planner_agent"]
    B -->|new_resume| D["single_resume_agent"]
    B -->|ignore| Z["END"]

    C --> E{"planner 是否产出 tool_calls"}
    E -->|是| F["worker_agent"]
    E -->|否| G["reviewer_agent"]

    F --> C
    G --> Z
    D --> Z
```

## 2. Worker 内部执行图

虽然现在还不是多个并行 Worker Agent，但 `worker_agent` 已经把招聘主链真正串起来了。

```mermaid
flowchart TD
    P["planner_agent"] --> S["search_candidates"]
    S --> R["从 FAISS / 简历库取回候选人"]
    R --> A["analyze_resume<br/>逐个解析简历"]
    A --> M["score_match<br/>逐个和 JD 打分"]
    M --> U["写回 state.candidates / state.match_results"]
    U --> V["reviewer_agent<br/>生成最终推荐报告"]
```

## 3. 项目模块图

从代码组织上看，当前项目已经形成了 API、Agent、RAG、Memory、Skills 和前端页面几个层次。

```mermaid
flowchart TD
    CFG["config.py<br/>全局配置 / LangSmith 初始化"]
    API["api/server.py<br/>FastAPI 接口"] --> MAIN["main.py<br/>构建 LangGraph"]
    MAIN --> CFG
    MAIN --> AGENT["agent/agent.py<br/>triage / planner / worker / reviewer"]
    AGENT --> TOOLS["agent/tools.py<br/>搜索 / 解析 / 评分 / 历史查询 / 邮件动作"]
    AGENT --> MCP["agent/mcp_tools.py<br/>MCP 外部工具动态加载"]
    AGENT --> SKILLS["agent/skills.py<br/>Skills 渐进式披露加载器"]
    SKILLS --> SKILLSDIR["skills/<br/>resume_analysis / candidate_matching / report_generation"]
    AGENT --> OBS["agent/observability.py<br/>LangSmith 追踪 + 运行指标"]
    AGENT --> MEM["agent/memory.py<br/>ChromaDB 候选人长期记录"]
    AGENT --> PROMPT["agent/prompt.py"]
    AGENT --> SCHEMA["agent/schemas.py"]
    TOOLS --> RAG["rag/retriever.py + reranker.py + vector_store.py"]
    RAG --> DATA["data/resumes/*.txt"]
    API --> UI["static/index.html<br/>普通模式 + HR 审核模式"]
```
