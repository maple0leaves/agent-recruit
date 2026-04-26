# Codebase Structure

**Analysis Date:** 2026-04-26

## Directory Layout

```
hellojobs/
├── agent/                     # Agent nodes, tools, schemas, prompts, memory, skills, MCP, observability
├── api/                       # FastAPI server with REST and SSE endpoints
├── rag/                       # RAG pipeline: vector store, retriever, reranker
├── skills/                    # Progressive disclosure skill definitions (markdown)
├── static/                    # Frontend SPA (HTML/CSS/JS)
├── data/                      # Runtime data: resumes, vector index, memory store
├── resume/                    # LaTeX resume template system for PDF generation
├── scripts/                   # Evaluation and data preparation scripts
├── testdataset/               # Optional Kaggle Resume Dataset expansion pool
├── .cursor/skills/            # Cursor IDE skill definitions
├── .specstory/                # Conversation history (specstory)
├── .planning/                 # Codebase architecture documentation
│   └── codebase/              # Current documents
├── .vscode/                   # VS Code workspace settings
│
├── main.py                    # LangGraph workflow build + CLI entry point
├── config.py                  # Global environment configuration + LangSmith init
├── mcp_servers.json           # MCP external tool server configuration
├── requirements.txt           # Python package dependencies
├── AGENTS.md                  # Harness context architecture core file
├── ARCHITECTURE.md            # Architecture documentation (root-level)
├── README.md                  # Project README
├── .env                       # Environment variables (not committed)
├── .env.example               # Environment variables template
└── .gitignore                 # Git ignore rules
```

## Directory Purposes

### `agent/` — Agent System Core

**Purpose:** All code related to the multi-agent recruitment logic: graph node implementations, tool definitions, data schemas, prompt templates, memory management, skill loading, MCP integration, and observability.

**Key files:**

| File | Lines | Purpose |
|------|-------|---------|
| `agent/agent.py` | 498 | Four agent node implementations (`triage_router`, `planner_agent`, `worker_agent`, `reviewer_agent`) plus `single_resume_agent`. LLM singleton initialization. Candidate parallel processing pipeline. Route decision function `should_continue_planning`. |
| `agent/tools.py` | 225 | Tool registry with 6 built-in tools: `search_candidates`, `analyze_resume`, `score_match`, `query_candidate_history`, `send_interview_invite`, `send_rejection_email`. MCP tool merging. LRU-cached resume file reader and LLM-based analyzers. |
| `agent/schemas.py` | 102 | Pydantic models: `CandidateInfo`, `MatchResult`, `JDInfo`, `RouterSchema`. LangGraph state definition `RecruitmentState`. API request/response models: `RecruitmentInput`, `RecruitmentOutput`. |
| `agent/prompt.py` | 102 | All prompt templates: `TRIAGE_SYSTEM_PROMPT`, `TRIAGE_USER_PROMPT`, `PLANNER_SYSTEM_PROMPT`, `REVIEWER_SYSTEM_PROMPT`, `JD_PARSE_PROMPT`, `RESUME_PARSE_PROMPT`, `MATCH_SCORING_PROMPT`. |
| `agent/memory.py` | 269 | Long-term memory with ChromaDB (semantic search) and JSON file fallback. Public API: `save_candidate_record()`, `get_candidate_history()`, `search_memory()`, `search_candidate_similar()`. |
| `agent/skills.py` | 112 | SkillDefinition dataclass. Markdown frontmatter parser. `load_all_skills()`, `match_skills()`, `build_skill_context()`, `get_skill_tools()`. |
| `agent/mcp_tools.py` | 130 | MCP client integration. Background event loop thread for async MCP connections. Supports stdio and SSE transports. `get_mcp_tools_sync()` for synchronous callers. |
| `agent/observability.py` | 162 | LangSmith tracing decorator `trace_agent_step`. In-process run metrics (`_RunMetrics`). `log_tool_usage()`, `log_rag_retrieval()`. Thread-safe counters. Graceful degradation when LangSmith is unavailable. |

### `api/` — HTTP Server

**Purpose:** FastAPI application exposing the recruitment workflow as REST endpoints and SSE streaming.

**Key files:**

| File | Lines | Purpose |
|------|-------|---------|
| `api/server.py` | 352 | FastAPI app. 8 endpoints: `/`, `/health`, `/recruit`, `/recruit/stream`, `/recruit/hitl/start`, `/recruit/hitl/resume`, `/skills`, `/upload-resume`, `/admin/rebuild-index`. CORS middleware. Static file serving. SSE event generator with asyncio.Queue bridge. |

### `rag/` — Retrieval-Augmented Generation

**Purpose:** Resume document indexing, semantic search, and reranking pipeline.

**Key files:**

| File | Lines | Purpose |
|------|-------|---------|
| `rag/vector_store.py` | 187 | FAISS index builder and loader. Resume directory fingerprinting via `resume_manifest.json`. Auto-rebuild on directory changes. PDF text extraction via pymupdf. |
| `rag/retriever.py` | 68 | `RerankRetriever` class implementing two-stage retrieval: FAISS (k x fetch_k_multiplier) + optional CrossEncoder rerank. `get_retriever()` factory function. Module-level vector store cache with `invalidate_vector_store_cache()`. |
| `rag/reranker.py` | 100 | Cohere-compatible rerank API client. Configurable endpoint, model, and API key. Falls back to score-order truncation on failure or when disabled. |

### `skills/` — Skill Definitions

**Purpose:** Markdown files defining progressive-disclosure skills. Each file has YAML frontmatter (name, description, tools, trigger) and body content with execution steps and quality checks.

**Key files:**

| File | Purpose |
|------|---------|
| `skills/resume_analysis.md` | Resume parsing skill. Tool: `analyze_resume`. Trigger: parsing needs. |
| `skills/candidate_matching.md` | Candidate matching skill. Tools: `score_match`, `search_candidates`. Trigger: matching needs. |
| `skills/report_generation.md` | Report generation skill. Tools: `query_candidate_history`, `send_interview_invite`, `send_rejection_email`. Trigger: report generation. |

### `static/` — Frontend

**Purpose:** Single-page frontend application served by FastAPI.

**Key files:**

| File | Purpose |
|------|---------|
| `static/index.html` | Full SPA with dark/light theme, standard workflow mode, HITL HR review mode, SSE streaming display, skill list panel. Communicates with backend via REST + SSE. |

### `data/` — Runtime Data

**Purpose:** Persistent data directories for resumes, vector index, and memory stores. Some directories are auto-generated at runtime.

| Directory | Content | Generated? | Committed? |
|-----------|---------|------------|------------|
| `data/resumes/` | .txt and .pdf resume files (35 sample resumes) | No | Yes |
| `data/vector_store/` | FAISS index (`index.faiss`, `index.pkl`) + `resume_manifest.json` | Yes (auto-built) | No |
| `data/chroma_memory/` | ChromaDB persistent data (SQLite + HNSW index files) | Yes (on first memory write) | No |
| `data/candidate_memory.json` | JSON fallback for long-term memory | Yes (on first memory write) | No |
| `data/eval_*.jsonl` | Evaluation datasets for retrieval and end-to-end tests | No (checked in) | Yes |

### `resume/` — LaTeX Resume Template

**Purpose:** LaTeX template system for generating Chinese technical PDF resumes. Contains a custom document class, photos, and pre-built sample resumes.

**Key files:**

| File | Purpose |
|------|---------|
| `resume/resume-photo.cls` | LaTeX document class for single-page resume with photo |
| `resume/resume-photo.tex` | Primary template file (editable for content) |
| `resume/fontawesome5/` | FontAwesome 5 LaTeX package for icons |
| `resume/adongwanai.jpg` | Sample photo for resume template |
| `resume/<name>.tex` / `.pdf` | Pre-generated sample resumes for 35 candidates |
| `resume/Makefile` | Build commands for LaTeX compilation |
| `resume/batch_demo_resumes.py` | Script to batch-generate all demo resumes |
| `.cursor/skills/generate-resume/SKILL.md` | Cursor skill with full LaTeX template usage guide |

### `scripts/` — Evaluation & Data Preparation

**Purpose:** Standalone scripts for RAG evaluation, end-to-end testing, and dataset preparation.

**Key files:**

| File | Purpose |
|------|---------|
| `scripts/eval_rag_metrics.py` | Evaluate FAISS retrieval quality (Recall@K, MRR) |
| `scripts/eval_end_to_end.py` | Run end-to-end workflow evaluation via API |
| `scripts/materialize_multi_pool.py` | Create candidate pool softlinks for evaluation |
| `scripts/synth_aligned_eval_llm.py` | Generate aligned evaluation datasets via LLM |
| `scripts/gen_eval_from_category.py` | Generate eval queries from resume category labels |

### `testdataset/` — Optional Evaluation Pool

**Purpose:** Optional Kaggle Resume Dataset subset for larger-scale evaluation (not included in git due to size). See `testdataset/TEST_SUMMARY.md`.

### `.cursor/skills/` — Cursor IDE Skills

**Purpose:** Cursor-specific skill definitions for AI-assisted development. Current skills:

| File | Purpose |
|------|---------|
| `.cursor/skills/generate-resume/SKILL.md` | Guide for generating Chinese PDF resumes via LaTeX template |
| `.cursor/skills/generate-resume/reference.md` | LaTeX template syntax reference |
| `.cursor/skills/generate-resume/scripts/compile.sh` | xelatex compilation script |

### `.planning/` — Codebase Planning Documents

**Purpose:** Architecture and planning documentation consumed by GSD commands. Current documents in `.planning/codebase/`:

| File | Purpose |
|------|---------|
| `.planning/codebase/ARCHITECTURE.md` | System architecture analysis |
| `.planning/codebase/STRUCTURE.md` | Codebase structure (this file) |

## Key File Locations

**Entry Points:**
- `main.py`: CLI entry point. Builds LangGraph, runs interactive input loop. Invoked via `python main.py`.
- `api/server.py`: FastAPI server entry point. Invoked via `python api/server.py` or `uvicorn api.server:app`.

**Configuration:**
- `config.py`: All environment variable loading, path resolution, LangSmith initialization. `.env` file loaded at module import time.
- `mcp_servers.json`: MCP external tool server definitions (stdio command/args or SSE URL).
- `requirements.txt`: Python package dependencies (no pinned versions, minimum bounds).
- `.env.example`: Template for required environment variables.

**Core Logic:**
- `main.py`: LangGraph workflow definition (graph topology, compile, `run()` function).
- `agent/agent.py`: All graph node implementations.
- `agent/tools.py`: Tool registry with 6 built-in tools.
- `rag/vector_store.py`: FAISS index building and loading.
- `agent/memory.py`: Long-term memory system.

**Testing:**
- `scripts/eval_rag_metrics.py`: Retrieval quality benchmarks.
- `scripts/eval_end_to_end.py`: End-to-end workflow tests.
- `data/eval_*.jsonl`: Pre-built evaluation datasets.

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `agent/agent.py`, `rag/vector_store.py`)
- Config/data: `camelCase.json` (e.g., `candidate_memory.json`, `resume_manifest.json`)
- Markdown: `snake_case.md` (e.g., `resume_analysis.md`, `candidate_matching.md`)
- LaTeX: `snake_case.tex` / `snake_case.cls` (e.g., `resume-photo.tex`, `resume-photo.cls`)
- Templates/docs: `UPPERCASE.md` (e.g., `ARCHITECTURE.md`, `README.md`)

**Directories:**
- All lowercase: `agent/`, `api/`, `rag/`, `skills/`, `static/`, `scripts/`, `data/`, `resume/`
- Dot-prefixed for tool config: `.cursor/`, `.specstory/`, `.planning/`, `.vscode/`

## Where to Add New Code

**New Feature — Agent Node:**
- Primary code: Add the node function in `agent/agent.py`
- Graph wiring: Register node and edges in `main.py:build_graph()`
- If new tool is needed: Register in `agent/tools.py` `_BUILTIN_TOOLS` list
- If new schema is needed: Add Pydantic model in `agent/schemas.py`
- If new prompt is needed: Add prompt template in `agent/prompt.py`

**New Feature — API Endpoint:**
- Implementation: `api/server.py` — add route handler under existing `app`
- Input/Output schemas: `agent/schemas.py` — add Pydantic request/response models
- If endpoint needs new business logic, call into `main.py:run()` or import from `agent/` directly

**New RAG Strategy or Retriever:**
- Implementation: `rag/` directory
- Vector store backend: `rag/vector_store.py`
- Retriever class: `rag/retriever.py` — extend `BaseRetriever`
- Rerank provider: `rag/reranker.py` — add provider-specific client

**New Skill Definition:**
- Add `.md` file in `skills/` with proper YAML frontmatter (name, description, tools, trigger)
- The system auto-discovers it via `agent/skills.py:load_all_skills()`

**New Resume Source Format:**
- Add reader logic in `rag/vector_store.py:_load_resume_documents()` for the new extension
- Update `_read_resume_file_uncached` in `agent/tools.py` if the format is also used for direct reading

**New Evaluation or Benchmark:**
- Script: `scripts/` directory
- Dataset: `data/` directory with `eval_` prefix as JSONL format
- Pool data: `data/eval_pools/` subdirectory

**New Frontend Feature:**
- Single file: `static/index.html` (the entire SPA is one file)

**New External Tool Integration (MCP):**
- Add server definition in `mcp_servers.json`
- No code changes needed — `agent/mcp_tools.py` auto-loads all configured MCP servers

## Special Directories

**`data/`:**
- Contains generated runtime data (FAISS index, ChromaDB memory, candidate_memory.json)
- `data/resumes/` is the one hand-curated directory checked into version control
- All other `data/` subdirectories are auto-generated and gitignored

**`resume/`:**
- Contains the LaTeX template system, pre-built sample PDFs, and intermediate build artifacts (`.aux`, `.log`, `.out`)
- The template class (`resume-photo.cls`) and `.tex` files are checked in
- Generated PDFs are checked in as sample outputs
- FontAwesome5 package is a vendored dependency

**`scripts/`:**
- Standalone Python scripts with their own entry points
- Not part of the main application module — run separately for evaluation

**`testdataset/`:**
- Optional; users must download the Kaggle dataset separately due to size
- Only contains `TEST_SUMMARY.md` and softlink pool structure

**`.specstory/`:**
- Conversation history metadata for the SpecStory tool
- Contains `bin/`, `cli/`, `history/`, `statistics.json`
- Auto-generated, checked in per project policy

**`.planning/codebase/`:**
- Architecture documentation consumed by GSD planning and execution commands
- Generated by `/gsd-map-codebase` commands

---

*Structure analysis: 2026-04-26*
