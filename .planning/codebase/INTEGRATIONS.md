# External Integrations

**Analysis Date:** 2026-04-26

## APIs & External Services

### LLM / AI Providers

**OpenAI-compatible API (Primary LLM + Embedding):**
- **Purpose:** All LLM calls (triage routing, JD parsing, resume analysis, match scoring, report generation) and text embeddings for vector search
- **Provider:** Configurable via `OPENAI_BASE_URL` in `config.py`. Supports:
  - OpenAI official (when `OPENAI_BASE_URL` is empty): `config.py:21`
  - OpenRouter (`https://openrouter.ai/api/v1`): `.env.example:3`
  - aihubmix (`https://aihubmix.com/v1`): `README.md:72`
  - Any OpenAI-compatible endpoint
- **SDK/Client:** `ChatOpenAI` from `langchain-openai` (`agent/agent.py:46-52`) and `OpenAIEmbeddings` from `langchain-openai` (`rag/vector_store.py:84-92`)
- **Auth:** `OPENAI_API_KEY` env var
- **Model config:** `LLM_MODEL` (default: `gpt-4o-mini`), `EMBEDDING_MODEL` (default: `text-embedding-3-small`)
- **HTTP headers:** Sends `HTTP-Referer: https://github.com/recruitment-agent` when using a custom base URL (`agent/agent.py:51`)
- **Usage locations:**
  - `agent/agent.py:46-52` - LLM instantiation for agents
  - `agent/agent.py:196` - JD parsing (structured output via `with_structured_output(JDInfo)`)
  - `agent/agent.py:223-241` - Planner agent reasoning
  - `agent/agent.py:426` - Reviewer report generation
  - `agent/tools.py:20-37` - Singleton resume parser and match scorer LLMs
  - `rag/vector_store.py:80-92` - Embedding model for FAISS index
  - `agent/prompt.py` - All prompt templates consumed by LLM calls

**Embedding Backend:**
- **Primary:** OpenAI-compatible API (`EMBEDDING_BACKEND=openai`), same API key and base URL as LLM
- **Alternate (declared but not implemented):** `EMBEDDING_BACKEND=huggingface` is mentioned in `config.py:33` comments with suggested models (`BAAI/bge-small-zh-v1.5`, `shibing624/text2vec-base-chinese`) but no HuggingFace embedding code exists in the codebase
- **Key implementation note:** Both LLM and embedding use the same `OPENAI_API_KEY` and `OPENAI_BASE_URL`. If using OpenRouter, the embedding model must be one supported by OpenRouter's embeddings endpoint

### Rerank API

**CrossEncoder Reranking (Optional):**
- **Purpose:** Second-stage reranking of FAISS retrieval results to improve precision (`rag/reranker.py`)
- **Protocol:** Compatible with Cohere `/v1/rerank` API format
- **Supported providers:**
  - Jina AI (`https://api.jina.ai/v1/rerank`) - default fallback URL
  - Cohere
  - aihubmix
  - Any provider exposing a `/v1/rerank` endpoint
- **SDK/Client:** Direct `httpx.Client()` POST call (`rag/reranker.py:46-48`)
- **Auth:** `RERANK_API_KEY` env var (falls back to `OPENAI_API_KEY` if empty)
- **URL derivation:** When `OPENAI_BASE_URL` is set, `RERANK_API_URL` auto-derives by replacing `/v1` suffix with `/v1/rerank` (`rag/reranker.py:17-21`)
- **Model:** `RERANK_MODEL` (default: `jina-reranker-v2-base-multilingual`)
- **Enabled only when:** `RERANK_ENABLED=true` in env config

## Data Storage

**Vector Store (Resume Search):**
- **FAISS** (`faiss-cpu >=1.8.0`) - Local file-based vector index
- **Location:** `data/vector_store/` (configurable via `VECTOR_STORE_PATH`)
- **Files:** `index.faiss` + `index.pkl` + `resume_manifest.json` (auto-generated)
- **Client:** `FAISS` from `langchain_community.vectorstores` (`rag/vector_store.py:7`)
- **Chunking:** `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)` (`rag/vector_store.py:138`)
- **Auto-rebuild:** When `VECTOR_INDEX_AUTO_REBUILD=true`, detects resume directory changes via fingerprint manifest and rebuilds automatically (`rag/vector_store.py:177-185`)
- **Fallback:** None -- FAISS is the primary vector store

**Long-term Memory (Candidate History):**
- **ChromaDB** (`chromadb >=0.5.0`) - Embedded persistent vector database
- **Location:** `data/chroma_memory/` (configurable via `CHROMA_MEMORY_PATH`)
- **Client:** `chromadb.PersistentClient` (embedded, no server needed) (`agent/memory.py:36`)
- **Collection:** `candidate_records` with `hnsw:space=cosine` (`agent/memory.py:38-39`)
- **Graceful degradation:** When ChromaDB is unavailable, falls back to JSON file storage at `data/candidate_memory.json` (`agent/memory.py:43-46`)
- **Storage format:** ChromaDB stores candidate evaluation records (name, position, match score, decision, timestamp) -- NOT resumes

**Resume Files (Source Documents):**
- **Location:** `data/resumes/` (configurable via `RESUME_DIR`)
- **Formats:** `.txt` (UTF-8 plain text) and `.pdf` (extracted via `pymupdf`/`fitz`)
- **Metadata:** Candidate name derived from filename (stem with underscores replaced by spaces, title-cased)
- **Eval pools:** Separate directories under `data/eval_pools/` for benchmarking (IT_eval_run, IT_smoke, mix_520)

**File Storage:**
- Local filesystem only. No cloud storage (S3, GCS, etc.) integration

**Caching:**
- In-process LRU caches:
  - `_read_resume_file` - LRU cache for PDF/TXT file reads (`agent/tools.py:53-54`)
  - `_analyze_resume_cached` - LRU cache for LLM resume parsing results keyed by MD5 hash (`agent/tools.py:59-69`)
- No external caching service (Redis, Memcached, etc.)

## Authentication & Identity

**Auth Provider:**
- None. The system has no user authentication, no API key validation, no session management
- The FastAPI `CORSMiddleware` allows all origins (`api/server.py:33-37`), effectively public
- MCP server auth: Not configured (no `env` or `headers` fields defined in `mcp_servers.json`)
- JWT/OAuth/SSO: Not present

## Monitoring & Observability

**LangSmith Tracing (Optional):**
- **Service:** [LangSmith](https://smith.langchain.com) by LangChain
- **Purpose:** Full tracing of LangGraph agent steps, tool calls, RAG retrievals, and run metrics (`agent/observability.py`)
- **SDK:** `langsmith >=0.1.0`
- **Activation:** `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` in `.env`
- **Init path:** `config.py:52-63` (`init_langsmith()`)
- **Enables:** LangChainTracer callback on graph execution, traceable decorators on nodes, tool usage logging
- **Displays:** Node latency, tool call count, RAG retrieval count, wall time

**Local Metrics:**
- Thread-safe `_RunMetrics` singleton in `agent/observability.py:39-68` -- tracks tool call counts, latencies, RAG retrievals
- Logging via Python `logging` module (standard library) -- no external log aggregation

**Error Tracking:**
- None. No Sentry, Datadog, or similar error monitoring integration

## CI/CD & Deployment

**Hosting:**
- No production deployment target detected
- No Dockerfile, docker-compose.yml, or container configuration
- No cloud platform configuration (AWS, GCP, Azure, Railway, Render, etc.)

**CI Pipeline:**
- None detected. No GitHub Actions, GitLab CI, Jenkins, or similar configuration

## Environment Configuration

**Required env vars:**
- `OPENAI_API_KEY` - API key for LLM and embedding providers

**Optional env vars:**
- `OPENAI_BASE_URL` - Custom API endpoint (OpenRouter, aihubmix, etc.)
- `LLM_MODEL` - LLM model name (default: `gpt-4o-mini`)
- `LLM_TEMPERATURE` - LLM temperature (default: `0.0`)
- `EMBEDDING_BACKEND` - Embedding backend (default: `openai`)
- `EMBEDDING_MODEL` - Embedding model name (default: `text-embedding-3-small`)
- `VECTOR_STORE_TYPE` - Vector store type (default: `faiss`)
- `VECTOR_STORE_PATH` - FAISS index path (default: `data/vector_store`)
- `RESUME_DIR` - Resume files directory (default: `data/resumes`)
- `RAG_TOP_K` - Number of results to retrieve (default: `5`)
- `VECTOR_INDEX_AUTO_REBUILD` - Auto-rebuild on file changes (default: `true`)
- `RERANK_ENABLED` - Enable CrossEncoder reranking (default: `false`)
- `RERANK_MODEL` - Rerank model name (default: `jina-reranker-v2-base-multilingual`)
- `RERANK_API_URL` - Rerank API URL (auto-derived if empty)
- `RERANK_API_KEY` - Rerank API key (falls back to OPENAI_API_KEY)
- `CHROMA_MEMORY_PATH` - ChromaDB path (default: `data/chroma_memory`)
- `LANGSMITH_TRACING` - Enable LangSmith tracing (default: `false`)
- `LANGSMITH_API_KEY` - LangSmith API key
- `LANGSMITH_PROJECT` - LangSmith project name (default: `recruitment-agent`)
- `API_HOST` - FastAPI bind host (default: `0.0.0.0`)
- `API_PORT` - FastAPI bind port (default: `8000`)
- `CANDIDATE_PARALLELISM` - Max concurrent LLM calls (default: `8`)

**Secrets location:**
- `.env` file at project root (git-ignored via `.gitignore`)
- No secret management service (Vault, AWS Secrets Manager, etc.)

## MCP (Model Context Protocol) Servers

**Configuration file:** `mcp_servers.json`

**Currently configured:**

| Server | Transport | Command | Args |
|--------|-----------|---------|------|
| `fetch` | stdio | `npx` | `-y @anthropic/mcp-server-fetch` |

**How it works:**
- `agent/mcp_tools.py` loads config from `mcp_servers.json` at module import time
- Supports three transport modes:
  - **stdio** (`mcp_tools.py:43-48`) - spawns a subprocess via command+args
  - **sse** (`mcp_tools.py:49-55`) - connects to a Server-Sent Events URL
  - **streamable_http** (`mcp_tools.py:49-55`) - HTTP streaming transport
- Connection is managed via `langchain_mcp_adapters.client.MultiServerMCPClient` (`mcp_tools.py:90`)
- Tools are loaded into a background asyncio event loop running in a daemon thread (`mcp_tools.py:66-78`)
- MCP tools are merged into the global tool registry in `agent/tools.py:204-212`, avoiding name collisions with built-in tools
- Failed MCP connections degrade gracefully (logged as warnings, tools list stays empty)

**Threading model for MCP:**
- A daemon thread runs `asyncio` event loop for async MCP operations
- `get_mcp_tools_sync()` submits coroutines via `asyncio.run_coroutine_threadsafe()` with a 60-second timeout

## Webhooks & Callbacks

**Incoming:**
- None. No webhook endpoints are registered

**Outgoing:**
- None. The system does not call external webhooks
- Email notifications (`send_interview_invite`, `send_rejection_email`) are simulated stubs in `agent/tools.py:157-176` -- no actual email/notification service is connected

## Built-in Tools (Agent Tool Registry)

**Defined in `agent/tools.py:181-188`:**

| Tool | Purpose | External Dependency |
|------|---------|---------------------|
| `search_candidates` | Semantic search over FAISS vector store | FAISS, embedding model API |
| `analyze_resume` | Parse resume text via LLM | LLM API |
| `score_match` | Score candidate-JD match via LLM | LLM API |
| `query_candidate_history` | Query ChromaDB/JSON candidate history | ChromaDB (local) |
| `send_interview_invite` | Simulated email stub | None (mock) |
| `send_rejection_email` | Simulated email stub | None (mock) |

**Note:** `send_interview_invite` and `send_rejection_email` are simulated stubs -- they return a success message string without actually sending emails. Adding a real email/SMS/notification integration would require replacing these implementations.

## Skills System (Context Injection)

**Not an external integration** but a progressive disclosure system that loads `.md` files from `skills/` directory:

| Skill File | Trigger Keywords | Associated Tools |
|------------|-----------------|------------------|
| `skills/resume_analysis.md` | "解析" + resume-related terms | `analyze_resume` |
| `skills/candidate_matching.md` | "匹配" + matching-related terms | `score_match`, `search_candidates` |
| `skills/report_generation.md` | "报告" + report-related terms | `query_candidate_history`, `send_interview_invite`, `send_rejection_email` |

Skills are loaded dynamically during streaming requests (`api/server.py:224-236`) and injected into agent prompts.

---

*Integration audit: 2026-04-26*
