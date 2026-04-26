# Coding Conventions

**Analysis Date:** 2026-04-26

## Language and Runtime

- **Language:** Python 3.10+
- **Package manager:** pip, with dependencies in `requirements.txt`
- **No pyproject.toml or setup.py** -- the project runs as a script-based application, not a pip-installable package
- **No type checker config** (no `mypy.ini`, `pyrightconfig.json`, or `pyproject.toml` with mypy/pyright settings) -- type hints are used but not enforced by a static analysis tool in CI

## Naming Patterns

**Files:**
- `snake_case.py` for all Python modules: `agent/agent.py`, `rag/retriever.py`, `api/server.py`, `scripts/eval_rag_metrics.py`
- No `__init__.py` contains logic -- `agent/__init__.py`, `rag/__init__.py`, `api/__init__.py` are all empty files serving only as package markers

**Functions and Methods:**
- `snake_case` universally: `save_candidate_record`, `load_all_skills`, `_build_llm`, `_fast_classify`
- Private helpers prefixed with single underscore: `_build_llm`, `_candidate_key`, `_coerce_candidate`, `_load_memory`, `_get_collection`
- Module-level "public API" functions have no underscore prefix: `save_candidate_record`, `get_candidate_history`, `get_retriever`

**Classes:**
- `PascalCase` for all classes: `CandidateInfo`, `MatchResult`, `RecruitmentState`, `SkillDefinition`, `RerankRetriever`
- LangChain built-in classes followed: `BaseRetriever`, `BaseModel`

**Variables and Constants:**
- `snake_case` for variables: `user_input`, `resume_text`, `match_results`, `sorted_matches`
- `UPPER_SNAKE_CASE` for module-level constants and configuration: `RERANK_ENABLED`, `LLM_MODEL`, `RAG_TOP_K`, `_CANDIDATE_PARALLELISM`, `_INQUIRY_KEYWORDS`, `_IGNORE_PATTERNS`
- Configuration constants sourced via `os.getenv()`: `OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")`

## Type Annotations

**Consistent use of `from __future__ import annotations`** in files that use complex annotations (`rag/retriever.py`, `agent/observability.py`, `scripts/eval_rag_metrics.py`, `scripts/eval_end_to_end.py`).

**Return type annotations are always present:**

```python
# agent/agent.py
def triage_router(state: RecruitmentState) -> Command[Literal["planner_agent", "single_resume_agent", "__end__"]]:
def planner_agent(state: RecruitmentState) -> dict:
def reviewer_agent(state: RecruitmentState) -> dict:
def should_continue_planning(state: RecruitmentState) -> Literal["worker_agent", "reviewer_agent"]:

# agent/tools.py
def search_candidates(query: str, top_k: int = 5) -> str:
def analyze_resume(resume_text: str) -> str:
def score_match(candidate_json: str, jd_json: str) -> str:
def get_all_tools(refresh_mcp: bool = False) -> list:
```

**Pydantic `BaseModel` used for all structured data schemas** (`agent/schemas.py`):

```python
class CandidateInfo(BaseModel):
    name: str = Field(default="", description="候选人姓名")
    skills: list[str] = Field(default_factory=list, description="技能列表")
```

**`TypedDict` for graph state** -- `RecruitmentState` in `agent/schemas.py` uses `TypedDict` with `Annotated[list, add_messages]` for the LangGraph message accumulator.

**Parameter type annotations are used consistently** across the entire codebase. Few functions omit them and those are limited to generic decorator wrappers (e.g. `trace_agent_step` in `agent/observability.py`).

**Occasional `# type: ignore` comments** in `agent/observability.py` for langsmith's `get_current_run_tree` import fallback:

```python
def get_current_run_tree() -> None:  # type: ignore[misc]
    return None
```

## Docstrings

**Module-level docstrings** are present in every `.py` file, enclosed in `"""`:

```python
"""Retriever interface for the recruitment RAG pipeline.

Two-stage retrieval: FAISS similarity search -> CrossEncoder reranking.
"""
```

**Function docstrings follow a consistent pattern:**
- One-line summary of what the function does
- Optional detailed explanation on subsequent lines

```python
def _build_search_query(jd_info: JDInfo, user_input: str) -> str:
    """Create a retrieval query from structured JD info."""

def planner_agent(state: RecruitmentState) -> dict:
    """Planner: parse JD and decide which tools to call.
    
    Optimization note: on first round (no messages / no candidates),
    directly use ``_fallback_search_plan`` to skip a non-decision LLM call.
    """
```

**Chinese comments for Chinese-domain logic** -- inline comments explaining business logic are often in Chinese (e.g. `# ── Triage 规则前置 ──`, `# 简历全文获取优先级`). Docstrings are mixed: some in English, some in Chinese, some bilingual. The pattern is:
- English docstrings for general utility functions and clear technical interfaces
- Chinese docstrings or Chinese inline comments for business logic specific to the recruiting domain

**No Google/NumPy-style docstring format** -- the codebase uses simple paragraph-style docstrings without Args/Returns sections (though some LangChain-compatible functions do use Args: in their docstring per LangChain convention):

```python
@tool
def search_candidates(query: str, top_k: int = 5) -> str:
    """Search candidate resumes from the vector store using semantic similarity.

    Args:
        query: Search query, e.g. "Python engineer 3 years experience"
        top_k: Number of candidates to return

    Returns:
        JSON string of matched candidate summaries
    """
```

This LangChain Args/Returns style is used only in `@tool`-decorated functions in `agent/tools.py`. Other functions do not follow this convention.

## Import Style

**Absolute imports** throughout, using the project root as import base (added via `sys.path.insert`):

```python
# Every entry-point file adds the project root:
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Then uses absolute imports:
from config import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY
from agent.memory import save_candidate_record
from agent.schemas import CandidateInfo, JDInfo, MatchResult, RecruitmentState
from agent.tools import ALL_TOOLS, TOOLS_BY_NAME
from rag.retriever import get_retriever
```

**Import ordering** (consistent pattern):
1. Standard library (`json`, `os`, `re`, `sys`, `from concurrent.futures import ...`)
2. Third-party libraries (`langchain.chat_models`, `langchain_core.messages`, `fastapi`, `pydantic`)
3. Project internal (`from config import ...`, `from agent.xxx import ...`)

Grouped with a blank line between each group.

**`from __future__ import annotations`** used at the very top (before standard library imports) in files needing deferred annotation evaluation (`rag/retriever.py`, `agent/observability.py`).

**Lazy imports** used to avoid circular dependencies and speed up module load:

```python
# agent/tools.py
def _get_resume_parser():
    global _LLM_RESUME_PARSER
    if _LLM_RESUME_PARSER is None:
        from agent.agent import _build_llm  # lazy import
        ...

# agent/mcp_tools.py
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
except ImportError:
    ...
    return []
```

## Error Handling

**Pattern: try/except with logging, then graceful fallback:**

```python
try:
    resp = client.post(RERANK_API_URL, json=payload, headers=headers)
    resp.raise_for_status()
    ...
except Exception as exc:
    logger.warning("Rerank API call failed, falling back to original order: %s", exc)
    return None
```

This "try -> log -> fallback" pattern is used throughout:
- `agent/memory.py`: ChromaDB operations fall back to JSON file storage
- `rag/reranker.py`: Rerank API failures fall back to score-order truncation
- `agent/tools.py`: MCP tool loading failures log a debug message and return empty list
- `api/server.py`: FastAPI endpoints wrap logic in try/except and raise `HTTPException` with 500

**No bare `except:`** -- all exception handlers specify the exception type (typically `Exception`).

**BLE001 (broad exception) is explicitly suppressed** in one location:

```python
except Exception as exc:  # noqa: BLE001
    print(f"Reading resume failed {source}: {exc}")
```

**Early return for error/edge cases** -- functions return early with safe defaults:

```python
def reviewer_agent(state: RecruitmentState) -> dict:
    if not match_results:
        return {"final_report": "未找到可推荐的候选人，请尝试调整岗位描述或补充简历库。"}

def rerank_documents(query, docs, top_k):
    if not docs:
        return docs
```

**FastAPI HTTPException** is used for API-level error reporting:

```python
raise HTTPException(status_code=400, detail="仅支持 .pdf 或 .txt 格式的简历文件")
```

## Async vs Sync

**The codebase is predominantly synchronous** -- the LangGraph workflow (`main.py`), agent nodes (`agent/agent.py`), tools (`agent/tools.py`), and RAG pipeline (`rag/`) are all implemented as synchronous functions.

**Async used only where required by the FastAPI framework:**
- `api/server.py`: SSE streaming endpoint uses `async def recruit_stream()` and `async def _stream_recruitment()`
- `api/server.py`: File upload uses `async def upload_resume()`
- `agent/mcp_tools.py`: MCP client connections use asyncio with a background event loop thread

**ThreadPoolExecutor for parallelism** -- `agent/agent.py` uses `concurrent.futures.ThreadPoolExecutor` for parallel candidate processing:

```python
with ThreadPoolExecutor(max_workers=workers) as pool:
    processed = list(
        pool.map(
            lambda payload: _process_one_candidate(payload, jd_json),
            candidates_payload,
        )
    )
```

**threading.Lock for thread-safe metrics** -- `agent/observability.py` uses `threading.Lock()` to protect shared `_RunMetrics` state accessed from worker threads.

## Logging

**Framework:** Python `logging` standard library -- no third-party logging library.

**Logger initialization:**
```python
import logging
logger = logging.getLogger(__name__)
```

**Log levels used:**
- `logger.info()` -- tool invocations, state transitions, latencies, RAG retrievals
- `logger.warning()` -- fallback scenarios, API failures, degraded mode operations
- `logger.error()` -- recoverable failures (ChromaDB write failure, memory search failure)
- `logger.debug()` -- MCP tools unavailable, reranking disabled, node start/finish

**`print()` used extensively alongside logging** for CLI-mode visibility (non-logged output to stdout):

```python
print(f"🔍 分类：INQUIRY → 搜索候选人库")
print(f"📋 JD 解析完成：{jd_info.title or '未命名岗位'}")
print(f"⚡ 首轮直跳：不调用 Planner LLM，直接发起 search_candidates")
```

There is no `logging.basicConfig()` or explicit handler configuration in the application code -- logging configuration would need to be set up externally or by the runtime environment.

**Structured observability** via `agent/observability.py` wraps `print`-based and `logger`-based logging with a `_RunMetrics` accumulator and optional LangSmith tracing.

## Function Design

**Function size:** Most functions are small (10-40 lines). The longest functions are:
- `worker_agent` in `agent/agent.py` (~65 lines) -- orchestrates tool execution and result aggregation
- `_stream_recruitment` in `api/server.py` (~95 lines) -- SSE event streaming logic

**Pure helper functions** extracted for clarity:
- `_build_search_query()`, `_candidate_key()`, `_coerce_candidate()`, `_fast_classify()`, `_derive_name_from_source()`

**Default parameter values** consistently used for optional arguments:

```python
def run(user_input: str, resume_text: str = "", use_hitl: bool = False, thread_id: str | None = None) -> dict:
def get_retriever(top_k: int = 5) -> RerankRetriever:
def search_memory(query: str, top_k: int = 5) -> list[dict]:
```

## Module Design

**Single-responsibility modules:**
- `agent/schemas.py` -- all Pydantic models and TypedDict definitions
- `agent/prompt.py` -- all prompt templates as module-level string constants
- `agent/tools.py` -- all tool definitions and the tool registry
- `agent/agent.py` -- all LangGraph node functions
- `agent/memory.py` -- long-term memory (ChromaDB + JSON fallback)
- `agent/observability.py` -- metrics collection, LangSmith trace integration
- `agent/skills.py` -- skills progressive disclosure system
- `agent/mcp_tools.py` -- MCP protocol integration
- `config.py` -- all environment-variable-driven configuration
- `main.py` -- LangGraph graph construction and CLI entry point
- `api/server.py` -- FastAPI app definition and routes

**Module-level singletons** used for shared state:
- `_vector_store` in `rag/retriever.py` (cached FAISS instance)
- `_llm`, `_llm_router`, `_llm_with_tools`, `_llm_reviewer` in `agent/agent.py` (cached LLM instances)
- `_LLM_RESUME_PARSER`, `_LLM_MATCH_SCORER` in `agent/tools.py` (lazy LLM instances)
- `_chroma_collection`, `_chroma_available`, `_chroma_initialized` in `agent/memory.py`
- `_metrics` in `agent/observability.py` (`_RunMetrics` singleton)
- `_mcp_client`, `_background_loop` in `agent/mcp_tools.py`

**No barrel files** -- each module is imported directly by its path, not re-exported through `__init__.py`.

## Comments

**Section separators** using commented dashes:

```python
# ── Triage ──────────────────────────────────────────────────────────────────
# ── Candidate ───────────────────────────────────────────────────────────────
```

**Chinese inline comments** for domain-specific optimization notes:

```python
# 大多数真实流量是「招一个 X 工程师」「找一个 Y 经验的人」这种明显的招聘
# 检索请求；显式触发词命中时直接路由，无需调用 LLM。
```

**No TODO/FIXME/HACK comments** found in the source code -- the codebase is clean of technical debt markers.

## Configuration Pattern

**Centralized config** in `config.py` -- all environment variables are read and exported from a single module with `load_dotenv()`:

```python
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
```

**`_resolve_path()` helper** normalizes relative paths against the project root:

```python
VECTOR_STORE_PATH = _resolve_path(os.getenv("VECTOR_STORE_PATH", "data/vector_store"))
```

---

*Convention analysis: 2026-04-26*
