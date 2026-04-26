# Technology Stack

**Analysis Date:** 2026-04-26

## Languages

**Primary:**
- Python 3.12 - All application code (agents, API, RAG pipeline, scripts)

**Secondary:**
- JavaScript/Vanilla (single `static/index.html` with inline CSS/JS for the frontend)
- HTML/CSS (frontend in `static/index.html`)
- Shell (build/compile scripts in `.cursor/skills/generate-resume/scripts/`)

## Runtime

**Environment:**
- Python 3.12 (confirmed: `python3 --version` reports 3.12.0)

**Package Manager:**
- pip (standard Python package manager)
- Lockfile: Not detected (no `requirements.lock`, `poetry.lock`, or `Pipfile.lock`)
- Dependencies defined in: `requirements.txt`

## Frameworks

**Core:**
- **LangChain** (`langchain>=1.0.0`, `langchain-core>=1.0.0`) - Foundation for agent tooling, LLM abstraction, retrievers, document processing
- **LangGraph** (`langgraph>=1.0.0`) - State machine workflow orchestration (Triage -> Planner -> Worker -> Reviewer graph in `main.py`)
- **LangGraph Checkpoint** (`langgraph.checkpoint.memory.InMemorySaver`) - In-memory workflow state persistence; no production checkpoint backend

**AI/LLM Integration:**
- **OpenAI SDK** (`openai>=1.0.0`) - Underlying Python SDK (transitive dependency via langchain-openai)
- **LangChain OpenAI** (`langchain-openai>=1.0.0`) - ChatOpenAI model wrapper, OpenAIEmbeddings embedding client
- **LangChain Community** (`langchain-community>=0.4.0`) - FAISS vector store integration
- **LangChain Text Splitters** (`langchain-text-splitters>=1.0.0`) - RecursiveCharacterTextSplitter for document chunking
- **LangChain MCP Adapters** (`langchain-mcp-adapters>=0.1.0`) - Bridge between MCP protocol servers and LangChain-compatible tools

**API Framework:**
- **FastAPI** (`fastapi>=0.110.0`) - REST API server (`api/server.py`) with automatic OpenAPI docs
- **Uvicorn** (`uvicorn[standard]>=0.29.0`) - ASGI server for FastAPI

**Testing:**
- No test framework detected (no pytest, unittest, or other test runner in `requirements.txt`)
- Evaluation scripts exist in `scripts/` for RAG metrics (`eval_rag_metrics.py`) and end-to-end tests (`eval_end_to_end.py`), but these are offline benchmarking tools, not unit/integration tests
- Data-driven eval sets in `data/` (JSONL format: `eval_*.jsonl`)

**Build/Dev:**
- No build tool detected (pure Python project)
- No formatter or linter configured (no `.eslintrc`, `biome.json`, `.prettierrc`, `ruff`, or `mypy` config)
- `.vscode/settings.json` only disables `specstory.cloudSync.enabled`

## Key Dependencies

**LLM & AI:**
| Package | Version | Why It Matters |
|---------|---------|---------------|
| `openai` | >=1.0.0 | OpenAI-compatible API client for LLM and embedding calls |
| `langchain-openai` | >=1.0.0 | LangChain wrapper for ChatOpenAI and OpenAIEmbeddings |
| `langgraph` | >=1.0.0 | Multi-agent state machine graph execution |
| `langchain-mcp-adapters` | >=0.1.0 | MCP protocol integration for external tool loading |

**Vector & Retrieval:**
| Package | Version | Why It Matters |
|---------|---------|---------------|
| `faiss-cpu` | >=1.8.0 | FAISS vector index for resume semantic search (`rag/vector_store.py`) |
| `chromadb` | >=0.5.0 | ChromaDB for long-term candidate memory (`agent/memory.py`) |
| `langchain-community` | >=0.4.0 | FAISS vector store integration from langchain |
| `langchain-text-splitters` | >=1.0.0 | Resume document chunking |

**Web & Server:**
| Package | Version | Why It Matters |
|---------|---------|---------------|
| `fastapi` | >=0.110.0 | REST API server |
| `uvicorn[standard]` | >=0.29.0 | ASGI server with HTTP/WebSocket support |
| `aiofiles` | >=23.0.0 | Async file operations for file uploads |
| `httpx` | >=0.27.0 | HTTP client for rerank API calls (`rag/reranker.py`) |

**PDF Processing:**
| Package | Version | Why It Matters |
|---------|---------|---------------|
| `pymupdf` (imported as `fitz`) | >=1.24.0 | PDF text extraction with CJK support (used in `rag/vector_store.py` and `agent/tools.py`) |
| `pypdf` | >=4.0.0 | Alternative PDF reader (not directly imported in code; potential fallback) |

**Data & Serialization:**
| Package | Version | Why It Matters |
|---------|---------|---------------|
| `pydantic` | >=2.0.0 | Data validation and schema definitions (`agent/schemas.py`) |
| `python-dotenv` | >=1.0.0 | Environment variable loading from `.env` file |

**Observability:**
| Package | Version | Why It Matters |
|---------|---------|---------------|
| `langsmith` | >=0.1.0 | LangSmith tracing and observability integration (`agent/observability.py`) |

**Network:**
| Package | Version | Why It Matters |
|---------|---------|---------------|
| `socksio` | >=1.0.0 | SOCKS proxy support (declared in requirements but not directly imported in code -- possible transitive dependency for httpx proxy support) |

## Configuration

**Environment:**
- `.env` file at project root (loaded by `python-dotenv` in `config.py`)
- All config lives in `config.py` with `os.getenv()` calls, providing defaults
- Key configuration variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | `""` | LLM / Embedding API key |
| `OPENAI_BASE_URL` | `""` | API base URL (empty = OpenAI official, filled = OpenRouter/aihubmix) |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model name |
| `LLM_TEMPERATURE` | `0.0` | LLM temperature |
| `VECTOR_STORE_TYPE` | `faiss` | Vector store type (faiss or chroma) |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model name |
| `EMBEDDING_BACKEND` | `openai` | Embedding backend (openai | huggingface — only openai implemented) |
| `RAG_TOP_K` | `5` | Number of candidates to retrieve |
| `VECTOR_INDEX_AUTO_REBUILD` | `true` | Auto-rebuild FAISS on resume directory changes |
| `RERANK_ENABLED` | `false` | Enable CrossEncoder reranking |
| `RERANK_MODEL` | `jina-reranker-v2-base-multilingual` | Rerank model name |
| `RERANK_API_URL` | derived from OPENAI_BASE_URL | Rerank API endpoint |
| `RERANK_API_KEY` | falls back to OPENAI_API_KEY | Rerank API key |
| `CHROMA_MEMORY_PATH` | `data/chroma_memory` | ChromaDB persistent storage path |
| `LANGSMITH_TRACING` | `false` | Enable LangSmith tracing |
| `LANGSMITH_API_KEY` | `""` | LangSmith API key |
| `LANGSMITH_PROJECT` | `recruitment-agent` | LangSmith project name |
| `API_HOST` | `0.0.0.0` | FastAPI host |
| `API_PORT` | `8000` | FastAPI port |
| `CANDIDATE_PARALLELISM` | `8` | Max concurrent LLM calls for candidate processing |

**Build:**
- No build system. Project runs directly from source (`python main.py` or `python api/server.py`)
- No TypeScript compilation, no bundler, no transpiler

## Platform Requirements

**Development:**
- Python 3.11+ (Python 3.12 confirmed)
- Network access for LLM/Embedding/Rerank API calls
- OpenAI-compatible API key (OpenAI, OpenRouter, aihubmix, etc.)
- `pip install -r requirements.txt`

**Production:**
- No containerization detected (no Dockerfile, docker-compose.yml)
- Run as a Python process via `uvicorn` or direct `python api/server.py`
- No database server needed (FAISS is file-based, ChromaDB is embedded/PersistentClient)
- No cloud deployment configuration detected

## Architecture Pattern

**Design:**
- Multi-Agent System (Triage -> Planner -> Worker -> Reviewer) orchestrated via LangGraph state machine
- RAG pipeline: FAISS dense retrieval + optional API-based CrossEncoder reranking
- Dual-memory: LangGraph message state (short-term) + ChromaDB/JSON (long-term)
- Skills-based progressive disclosure system for contextual knowledge injection
- MCP (Model Context Protocol) for dynamic external tool extension

---

*Stack analysis: 2026-04-26*
