<!-- refreshed: 2026-04-26 -->
# Architecture

**Analysis Date:** 2026-04-26

## System Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                         │
│         `api/server.py` — REST endpoints + SSE streaming           │
├───────────────────────────────────────────────────────────────────┤
│                    LangGraph Workflow (StateGraph)                  │
│                         `main.py` — graph builder                  │
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────────┐   │
│  │ triage   │───>│ planner  │───>│ worker   │───>│ reviewer   │   │
│  │ _router  │    │ _agent   │    │ _agent   │    │ _agent     │   │
│  └────┬─────┘    └──────────┘    └──────────┘    └────────────┘   │
│       │              ^                                               │
│       │              └─────── (worker loops back to planner) ───────┘
│       │                                                            
│       └───> single_resume_agent ───> END                          
│       └───> END (ignore)                                           
├───────────────────────────────────────────────────────────────────┤
│                   Agent Nodes (`agent/agent.py`)                    │
│                                                                     │
│  triage_router   →  LLM + rule-based classification                │
│  planner_agent   →  JD parsing + tool-selection strategy           │
│  worker_agent    →  Executes tools, parallel candidate processing  │
│  reviewer_agent  →  Final report generation + memory persistence   │
├───────────────────────────────────────────────────────────────────┤
│    Tool Layer (`agent/tools.py`, `agent/mcp_tools.py`)              │
│    Skills Layer (`agent/skills.py`, `skills/*.md`)                  │
│    RAG Layer (`rag/retriever.py`, `rag/vector_store.py`, `rag/reranker.py`) │
│    Memory Layer (`agent/memory.py`)                                 │
├───────────────────────────────────────────────────────────────────┤
│                   External Dependencies                              │
│  LLM API  │  Embedding API  │  Rerank API  │  ChromaDB  │  MCP     │
└───────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Graph builder | Compile LangGraph StateGraph with nodes, edges, HITL interrupts | `main.py` |
| Triage Router | Classify user request: inquiry / new_resume / ignore | `agent/agent.py:148` |
| Planner Agent | Parse JD, decide which tools to call, orchestrate search strategy | `agent/agent.py:199` |
| Worker Agent | Execute tool calls, parallel candidate parsing + scoring | `agent/agent.py:323` |
| Reviewer Agent | Generate final report, persist candidate history | `agent/agent.py:392` |
| Single Resume Agent | Bypass full pipeline for one-resume analysis | `agent/agent.py:458` |
| Tool Registry | Define and register 6 built-in tools + MCP dynamic tools | `agent/tools.py` |
| MCP Client | Load external tools via MCP protocol (stdio/SSE) | `agent/mcp_tools.py` |
| Prompt Templates | All system/user prompt strings for each agent | `agent/prompt.py` |
| State/Data Schemas | Pydantic types for JDInfo, CandidateInfo, MatchResult, state | `agent/schemas.py` |
| Long-term Memory | ChromaDB vector memory + JSON file fallback | `agent/memory.py` |
| Skills Loader | Progressive disclosure: parse markdown skill files, match triggers | `agent/skills.py` |
| Observability | LangSmith tracing wrapper + in-process run metrics | `agent/observability.py` |
| Vector Store | Build/load FAISS index from resume files, auto-rebuild on change | `rag/vector_store.py` |
| Retriever | Two-stage retrieval: FAISS + optional CrossEncoder rerank | `rag/retriever.py` |
| Reranker | Cohere-compatible rerank API client with fallback | `rag/reranker.py` |
| Global Config | Environment variable loading, path resolution, LangSmith init | `config.py` |
| API Server | FastAPI with REST, SSE streaming, HITL, file upload, admin | `api/server.py` |

## Pattern Overview

**Overall:** Multi-agent orchestration with LangGraph state machine.

**Key Characteristics:**
- **State-driven workflow**: LangGraph StateGraph manages a single `RecruitmentState` TypedDict that flows through all nodes. Messages are accumulated via LangGraph's `add_messages` reducer.
- **Agent specialization**: Four distinct agent roles (Triage, Planner, Worker, Reviewer) each with dedicated prompts and model configurations. Planner and Worker form an inner loop; Reviewer is terminal.
- **Structured LLM output**: Heavy use of `with_structured_output()` bound to Pydantic schemas (`RouterSchema`, `JDInfo`, `CandidateInfo`, `MatchResult`) for reliable parsing.
- **Fallback chains**: Every decision point has a fast-path rule fallback before invoking LLM (triage `_fast_classify`, planner `_fallback_search_plan`).
- **Parallel batch processing**: Candidate analysis (analyze_resume + score_match) runs in `ThreadPoolExecutor` with configurable parallelism (default 8).
- **Cascade persistence**: Long-term memory writes to ChromaDB first; falls back to JSON file on failure.

## Layers

**API Layer (`api/server.py`):**
- Purpose: Expose the recruitment workflow as HTTP endpoints with REST and SSE streaming
- Contains: FastAPI app, route handlers, request/response models, CORS middleware
- Depends on: `main.py` (compiled graph), `agent/skills.py`, `rag/vector_store.py`
- Used by: Frontend static SPA (`static/index.html`), curl, external clients

**Workflow Layer (`main.py`):**
- Purpose: Define the LangGraph StateGraph topology (nodes, edges, conditional edges, interrupt points)
- Contains: `build_graph()`, `run()` entry function, default compiled graph instances
- Depends on: `agent/agent.py` (node functions), `agent/schemas.py` (state type), `config.py`
- Used by: `api/server.py`, CLI (`if __name__ == "__main__"`)

**Agent Layer (`agent/agent.py`):**
- Purpose: Implement all graph node functions (triage, planner, worker, reviewer, single_resume)
- Contains: LLM initialization, tool binding, JD parsing, candidate processing pipeline, report generation
- Depends on: `agent/schemas.py`, `agent/tools.py`, `agent/prompt.py`, `agent/memory.py`, `config.py`
- Used by: `main.py` (node references)

**Tool Layer (`agent/tools.py`, `agent/mcp_tools.py`):**
- Purpose: Define, register, and dynamically load callable tools for the agent
- Contains: 6 built-in tools (search_candidates, analyze_resume, score_match, query_candidate_history, send_interview_invite, send_rejection_email), MCP tool merging
- Depends on: `rag/retriever.py`, `agent/memory.py`, `agent/prompt.py`
- Used by: `agent/agent.py` (tool binding)

**RAG Layer (`rag/vector_store.py`, `rag/retriever.py`, `rag/reranker.py`):**
- Purpose: Resume document indexing, semantic retrieval, and reranking
- Contains: FAISS index builder/loader, `RerankRetriever` (FAISS + optional CrossEncoder), rerank API client
- Depends on: `config.py`, `langchain_openai.OpenAIEmbeddings`
- Used by: `agent/tools.py` (search_candidates)

**Memory Layer (`agent/memory.py`):**
- Purpose: Persistent long-term storage for candidate evaluation records
- Contains: ChromaDB collection client, JSON file fallback, semantic search API
- Depends on: `chromadb`, JSON file at `data/candidate_memory.json`
- Used by: `agent/agent.py` (reviewer saves records), `agent/tools.py` (query_candidate_history)

**Skill Layer (`agent/skills.py`, `skills/*.md`):**
- Purpose: Conditional knowledge injection based on user intent
- Contains: Markdown skill parser, trigger-based matcher, context builder
- Depends on: `skills/` directory with `.md` files
- Used by: `api/server.py` (SSE streaming injects matched skills)

## Data Flow

### Primary Request Path — Recruitment Inquiry

1. User submits `user_input` (e.g., "招聘一个3年经验的Python工程师") via CLI (`main.py:137`) or API (`api/server.py:68`).
2. `main.py:run()` constructs an initial `RecruitmentState` and invokes the compiled `recruitment_graph`. (`main.py:127`)
3. **triage_router** (`agent/agent.py:148`): Checks `resume_text` first (bypass for direct resume). Runs `_fast_classify()` rule checker against keywords. If no rule match, falls back to `_llm_router.with_structured_output(RouterSchema)`. Routes to `planner_agent` for "inquiry".
4. **planner_agent** (`agent/agent.py:199`): Parses JD via `_parse_jd()` using `_llm_jd` (structured output `JDInfo`). On first invocation (no history, no candidates), skips LLM entirely and calls `_fallback_search_plan()` to produce a deterministic `search_candidates` tool call. Subsequent rounds use `_llm_with_tools` (LLM + tool binding) to decide next action.
5. **worker_agent** (`agent/agent.py:323`): Iterates `last_message.tool_calls`. For `search_candidates`, invokes FAISS retriever via `rag/retriever.py`, gets candidate payloads, then processes them in parallel via `ThreadPoolExecutor`. Each candidate undergoes `analyze_resume` (LLM extracts structured info) then `score_match` (LLM scores against JD). Results are deduplicated by email/name and sorted by score.
6. Loop: Worker returns to **planner_agent** (`builder.add_edge("worker_agent", "planner_agent")` in `main.py:61`). If `match_results` exist, planner signals "reviewer".
7. `should_continue_planning` (`agent/agent.py:493`): Inspects `last.tool_calls` to route to worker_agent (has tools) or reviewer_agent (no tools).
8. **reviewer_agent** (`agent/agent.py:392`): Sorts matches, invokes `_llm_reviewer` to generate a prose report. Saves each candidate record to long-term memory via `save_candidate_record()` (ChromaDB + JSON fallback). Returns `final_report`.
9. Final state returned to caller. Metrics snapshot printed by `main.py:140`.

### Single Resume Path

1. User submits `resume_text` alongside `user_input`. (`api/server.py:68-73`)
2. **triage_router** (`agent/agent.py:150`): Detects `resume_text` is set, bypasses classification, routes directly to `single_resume_agent`.
3. **single_resume_agent** (`agent/agent.py:458`): Parses JD from `user_input`, runs `analyze_resume` + `score_match` sequentially, builds a simple text report, returns to END.

### HITL (Human-in-the-Loop) Path

1. Client calls `/recruit/hitl/start` (`api/server.py:98`). Uses `recruitment_graph_hitl` which has `interrupt_before=["reviewer_agent"]`.
2. Graph runs through triage -> planner -> worker -> planner -> (suspends before reviewer). State is persisted in-memory via `InMemorySaver`.
3. Client calls `/recruit/hitl/resume` (`api/server.py:140`) with `hr_approved` and optional `hr_feedback`. These values are injected into state, and the graph resumes at reviewer_agent.
4. Reviewer incorporates HR approval/feedback into the final report.

### SSE Streaming Path

1. Client calls `/recruit/stream` (`api/server.py:304`). Streams events via `text/event-stream`.
2. `_stream_recruitment` (`api/server.py:205`) runs the graph in a background thread via `loop.run_in_executor`. Graph chunks are pushed through an `asyncio.Queue`.
3. Events: `status` (node completed), `tool_call` (tool invocation details), `progress` (human-readable messages), `result` (final output), `error` (on failure).
4. Before graph execution, matched skills are loaded and sent as a `progress` event.

**State Management:**
- **Short-term memory**: LangGraph `messages` field with `add_messages` reducer. Handles conversation history between planner/worker cycles.
- **Execution state**: `RecruitmentState` TypedDict flows through all nodes, accumulates candidates, match_results, and the final report.
- **Long-term memory**: ChromaDB (semantic search) + JSON file fallback for candidate evaluation records persisted across sessions.
- **Thread safety**: `_RunMetrics` uses `threading.Lock`. Memory module shares no mutable state across threads. ChromaDB client is lazily initialized as a module singleton.

## Key Abstractions

**RecruitmentState (TypedDict):**
- Purpose: The single state object that flows through the entire LangGraph workflow. All nodes read from and write to this.
- Location: `agent/schemas.py:61`
- Keys: `user_input`, `resume_text`, `jd_info` (JDInfo), `candidates` (list[CandidateInfo]), `match_results` (list[MatchResult]), `final_report`, `classification`, `next_action`, `hr_approved`, `hr_feedback`, `messages`

**LLM singleton pattern:**
- Purpose: Reuse LLM instances across agent calls instead of re-initializing per invocation. Each LLM variant is configured once with its specific structured output or tool binding.
- Location: `agent/agent.py:56-60`, `agent/tools.py:20-37`
- Instances: `_llm` (base), `_llm_router` (structured RouterSchema), `_llm_jd` (structured JDInfo), `_llm_with_tools` (bound to ALL_TOOLS), `_llm_reviewer` (temperature=0.3), `_LLM_RESUME_PARSER` (structured CandidateInfo), `_LLM_MATCH_SCORER` (structured MatchResult)

**RerankRetriever (BaseRetriever):**
- Purpose: Two-stage retrieval pipeline. Stage 1: FAISS dense vector search with `fetch_k_multiplier` (3x). Stage 2: Optional CrossEncoder API rerank.
- Location: `rag/retriever.py:37`
- Config: `RERANK_ENABLED` flag, configurable `top_k`, Cohere-compatible rerank endpoint.

**Auto-rebuilding vector store:**
- Purpose: When `VECTOR_INDEX_AUTO_REBUILD` is true, the FAISS index is compared against a `resume_manifest.json` fingerprint on every load. If resume files have been added, removed, or modified, the index is rebuilt automatically.
- Location: `rag/vector_store.py:165-186`

**SkillDefinition (dataclass):**
- Purpose: Represents a loaded skill from a markdown file. Contains frontmatter metadata (name, description, tools, trigger) and body content.
- Location: `agent/skills.py:13-18`
- Flow: Skills are loaded from `skills/*.md` on API startup, matched against user input via trigger keyword matching, and injected as context into prompts.

## Entry Points

**CLI Entry:**
- Location: `main.py:131-146`
- Triggers: Direct `python main.py` execution
- Responsibilities: Prompt user for input, invoke `run()`, print final report and metrics

**API Entry:**
- Location: `api/server.py:348-352` (uvicorn.run) or `python api/server.py`
- Responsibilities: Start FastAPI server on configured host:port, serve REST endpoints + static frontend

**API Endpoints:**
| Method | Path | Handler | Purpose |
|--------|------|---------|---------|
| GET | `/` | `frontend()` | Serve static SPA (`static/index.html`) |
| GET | `/health` | `health()` | Liveness check |
| POST | `/recruit` | `recruit()` | Synchronous full workflow |
| POST | `/recruit/stream` | `recruit_stream()` | SSE streaming workflow |
| POST | `/recruit/hitl/start` | `hitl_start()` | Start HITL workflow (pauses before reviewer) |
| POST | `/recruit/hitl/resume` | `hitl_resume()` | Resume after HR review |
| GET | `/skills` | `list_skills()` | List all available skills |
| POST | `/upload-resume` | `upload_resume()` | Upload PDF/TXT resume file |
| POST | `/admin/rebuild-index` | `rebuild_index()` | Rebuild FAISS vector index |

## Architectural Constraints

- **Threading**: Single-threaded asyncio for API server. Worker agent uses `ThreadPoolExecutor` for CPU-bound candidate processing (up to `CANDIDATE_PARALLELISM`, default 8). MCP tools use a dedicated daemon background event loop thread. All LLM calls are synchronous (blocking) within the LangGraph execution thread.
- **Global state**: Module-level singletons for LLM instances (`agent/agent.py:56-60`, `agent/tools.py:16-17`), FAISS vector store (`rag/retriever.py:18`), ChromaDB collection (`agent/memory.py:21-23`), MCP client (`agent/mcp_tools.py:14`), and run metrics (`agent/observability.py:71`). These are safe for read-heavy concurrent access but must be explicitly invalidated (e.g., `invalidate_vector_store_cache()`).
- **Circular imports**: `agent/tools.py` imports `_build_llm` from `agent/agent.py` at function-call time (inside `_get_resume_parser` and `_get_match_scorer`) rather than at module level to avoid circular dependency.
- **HITL checkpointing**: Uses `InMemorySaver` only. Checkpoints are not persisted to disk. State is lost on process restart. For production, a persistent `CheckpointSaver` would be needed.
- **Memory**: ChromaDB collection uses cosine distance metric (`hnsw:space: cosine`). JSON fallback has no semantic search capability.

## Anti-Patterns

### LLM singleton delayed import
**What happens:** `agent/tools.py` imports `_build_llm` from `agent/agent.py` inside a function call (`_get_resume_parser`, `_get_match_scorer`) rather than at module top level, because `agent/agent.py` imports from `agent/tools.py` creating a circular dependency.
**Why it's wrong:** Fragile — any change to the import chain can break this. The import is hidden inside a function, making debugging harder.
**Do this instead:** Extract `_build_llm` and LLM singletons into a separate module (e.g., `agent/llm.py`) that both `agent.py` and `tools.py` can import safely without circular dependency.

### InMemorySaver for HITL
**What happens:** HITL workflows use `InMemorySaver()` (`main.py:70`), which stores checkpoints in process memory only.
**Why it's wrong:** If the server restarts or crashes during the HITL pause, the checkpoint is lost. The HR reviewer's work is discarded.
**Do this instead:** Use a persistent `CheckpointSaver` (e.g., `PostgresSaver`, `SqliteSaver`) from `langgraph-checkpoint` to survive restarts.

### Module-level mutable state across graph nodes
**What happens:** FAISS vector store is cached in a module global `_vector_store` (`rag/retriever.py:18`). LLM singletons are module globals.
**Why it's wrong:** OK for read-only singletons, but the vector store cache must be explicitly invalidated on rebuild. If two concurrent requests trigger a rebuild, race conditions on the global are possible.
**Do this instead:** Use a request-scoped cache (e.g., `contextvars`) or ensure rebuild operations use a lock.

## Error Handling

**Strategy:** Graceful degradation with fallback chains. Every external dependency has a fallback path.

**Patterns:**
- **Triage fallback**: Rule-based `_fast_classify()` first, LLM fallback second (`agent/agent.py:135-169`)
- **Planner fallback**: Deterministic `_fallback_search_plan` when LLM produces no tool calls (`agent/agent.py:243-244`)
- **Memory fallback**: ChromaDB write/read failures degrade to JSON file (`agent/memory.py:26-46`)
- **Rerank fallback**: API rerank failure degrades to score-order truncation (`rag/reranker.py:73-81`)
- **MCP fallback**: MCP tool loading failure returns empty list; tools are not available but the system continues (`agent/mcp_tools.py:117-119`, `agent/tools.py:222-225`)
- **API error handling**: `HTTPException` with 400/422/500 status codes (`api/server.py:83`, `api/server.py:166`, `api/server.py:345`)

## Cross-Cutting Concerns

**Logging:** Python `logging` module throughout. Agent nodes print to stdout with emoji prefixes for CLI visibility. Worker agent logs tool calls. Memory module logs ChromaDB availability and fallback. All agent node implementations are wrapped with `trace_agent_step` decorator for LangSmith tracing (`agent/observability.py:74-98`).

**Validation:** Pydantic models enforce field types and constraints (e.g., `MatchResult.match_score` constrained to 0-100 with `Field(ge=0, le=100)`). API input validated via `RecruitmentInput` Pydantic model. Response serialization via `RecruitmentOutput`.

**Authentication:** None implemented. CORS is wide-open (`allow_origins=["*"]`). The admin rebuild endpoint has no auth. The system relies on network-level security (not running exposed to the internet).

---

*Architecture analysis: 2026-04-26*
