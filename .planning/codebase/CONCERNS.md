# Codebase Concerns

**Analysis Date:** 2026-04-26

## Tech Debt

### agent.py >400 lines, mixes 4 agent roles in one file

- **Issue:** `agent/agent.py` (498 lines) contains the implementation of all four agent nodes (triage_router, planner_agent, worker_agent, reviewer_agent) plus 11 helper functions and a single_resume_agent. This violates single-responsibility and makes the file hard to test, reason about, and modify.
- **Files:** `agent/agent.py`
- **Impact:** Changes to one agent require scanning 498 lines; diff churn is high; no isolated unit testing possible.
- **Fix approach:** Split into `agent/triage.py`, `agent/planner.py`, `agent/worker.py`, `agent/reviewer.py`. Keep shared helpers in `agent/_shared.py`.
- **Severity:** HIGH

### No tests exist anywhere

- **Issue:** Zero test files found in the entire repository. No `test_*.py`, no test configuration (`pytest.ini`, `pyproject.toml` test config, `jest.config.*`, etc.). No CI pipeline enforces test passing.
- **Files:** Entire codebase
- **Impact:** Every refactor, upgrade, or new feature is a blind deployment. Bugs in LLM response handling, edge cases in PDF parsing, and state machine routing are discovered at runtime.
- **Fix approach:** Add `pytest` with test configuration. Start with unit tests for domain logic (`schemas.py`, `_coerce_*` helpers, `_fast_classify`, `_derive_name_from_source`), then integration tests for RAG retrieval and agent flow.
- **Severity:** HIGH

### Print-based logging throughout core agent and RAG code

- **Issue:** `agent/agent.py` and `rag/vector_store.py` use bare `print()` instead of `logging` for all progress messages (14 occurrences in `agent.py`, 4 in `vector_store.py`). This means these messages cannot be controlled via log level, filtered, or redirected in production. The project already imports `logging` in 8 files but never configures the root logger or sets up handlers.
- **Files:** `agent/agent.py:151,161,172,178,184,207,221,282,342,358,451,469,479`, `rag/vector_store.py:111,141,147,181`
- **Impact:** Console pollution in production (FastAPI/uvicorn output); no log levels (info/warn/error) for operational filtering; cannot integrate with structured logging or log aggregation.
- **Fix approach:** Replace all `print(...)` with `logger.info(...)` / `logger.warning(...)`. Add `logging.basicConfig(level=logging.INFO)` in `main.py` or FastAPI lifespan startup.
- **Severity:** MEDIUM

### Mock email tools are no-ops

- **Issue:** `send_interview_invite` (`agent/tools.py:157`) and `send_rejection_email` (`agent/tools.py:171`) return a string like `"[模拟发送] 面试邀请已发送给..."` with no actual email delivery. They are documented as "mock" in the code but listed as real tools in prompts and skill files, meaning the LLM believes it is taking action.
- **Files:** `agent/tools.py:157-176`, `agent/prompt.py:23-28` (skill files list them as real tools)
- **Impact:** False sense of automation. In production, these would silently do nothing while the LLM believes it has sent notifications.
- **Fix approach:** Add an email backend configuration (SMTP/SendGrid env vars). Provide a config toggle: when email is not configured, return a clear log message stating email is disabled, rather than a realistic-looking success message.
- **Severity:** MEDIUM

### `sys.path.insert(0, ...)` in 6 source files

- **Issue:** Six files (`main.py:7`, `agent/agent.py:10`, `rag/retriever.py:16`, `rag/vector_store.py:11`, `api/server.py:17`, `reranker.py` via indirect) use `sys.path.insert(0, ...)` to add the project root to `sys.path`. This is fragile, makes the package non-installable via `pip install`, and can cause import conflicts.
- **Files:** `main.py:7`, `agent/agent.py:10`, `rag/retriever.py:16`, `rag/vector_store.py:11`, `api/server.py:17`
- **Impact:** Cannot install as a proper Python package. `python -m` invocation patterns are unreliable. Module shadowing possible.
- **Fix approach:** Add a `pyproject.toml` with project metadata and entry points. Install package with `pip install -e .`. Remove all `sys.path.insert(0, ...)` calls.
- **Severity:** MEDIUM

### `ALL_TOOLS` / `TOOLS_BY_NAME` mutable globals mutated at import time

- **Issue:** `agent/tools.py:190-191` defines `ALL_TOOLS` and `TOOLS_BY_NAME` as module-level lists/dicts. At import time (lines 222-225), `_load_mcp_tools_safe()` is called and `_merge_mcp_tools` clears and rebuilds the lists. Any code that captures a reference to `ALL_TOOLS` before this point will see stale or empty data. The mutation happens as a side effect of the import, not under explicit control.
- **Files:** `agent/tools.py:190-225`
- **Impact:** Race condition-like behavior at import time; fragile when tools are accessed before the module finishes loading; hard to debug when tools appear missing.
- **Fix approach:** Use a lazy-initialization pattern with `get_all_tools()` only. Remove the module-level `_initial_mcp` side effect. Move MCP loading to an explicit `init()` call.
- **Severity:** MEDIUM

### ChromaDB `RECORD` memory double-writes but single-path reads

- **Issue:** `agent/memory.py:108-146` writes to both JSON file and ChromaDB on every `save_candidate_record` call. But `get_candidate_history` (line 149) prefers ChromaDB and only falls back to JSON if ChromaDB fails. During a partial write failure where ChromaDB writes but JSON fails, data is inconsistent.
- **Files:** `agent/memory.py:108-167`
- **Impact:** Data could be in ChromaDB but not JSON (or vice versa) with inconsistent retrieval behavior. The JSON file grows unboundedly since it is never compacted or rotated.
- **Fix approach:** Choose one primary store (ChromaDB) and make JSON a true fallback (only on ChromaDB failure, not dual-write). Add a periodic compaction or TTL for JSON records.
- **Severity:** LOW

### Inconsistent configuration: `RERANK_ENABLED` defined in two places

- **Issue:** `config.py:38` and `rag/reranker.py:15` both define `RERANK_ENABLED` from the environment. The `reranker.py` version accesses `os.getenv` directly instead of importing from `config.py`, meaning the two sources can diverge if any runtime logic modifies config behavior.
- **Files:** `config.py:38`, `rag/reranker.py:15-23`
- **Impact:** Confusion about the single source of truth; if config logic is extended (e.g., lambda for dynamic enable/disable), the reranker copy will be stale.
- **Fix approach:** Remove the `os.getenv` calls from `reranker.py` and import all configuration from `config.py`.
- **Severity:** LOW

## Security Considerations

### FAISS `allow_dangerous_deserialization=True`

- **Issue:** `rag/vector_store.py:161` loads FAISS index with `allow_dangerous_deserialization=True`. FAISS indices can execute arbitrary pickle code during deserialization. If an attacker can replace the index files in `data/vector_store/`, they gain arbitrary code execution on the server.
- **Files:** `rag/vector_store.py:161`
- **Current mitigation:** The index is local and stored in a gitignored directory. No external input can directly write to it.
- **Recommendations:** Validate the FAISS index file checksum or sign it with HMAC after building. Document this as a security constraint. Consider using `FAISS.load_local(..., allow_dangerous_deserialization=False)` if the FAISS version supports pickle-free serialization.
- **Severity:** MEDIUM

### No authentication or authorization on any API endpoint

- **Issue:** All API endpoints in `api/server.py` (including `/recruit`, `/recruit/stream`, `/admin/rebuild-index`, `/upload-resume`) are fully open. The `CORS` middleware (`api/server.py:35`) allows all origins (`allow_origins=["*"]`). There is no API key, bearer token, or session check.
- **Files:** `api/server.py:28-38, 62-345`
- **Current mitigation:** None. Endpoint exposure depends on network-level controls.
- **Recommendations:** Add API key authentication via header (e.g., `X-API-Key`). Protect `/admin/rebuild-index` especially since it triggers index rebuild and is a potential denial-of-service vector. Restrict CORS to specific origins in production.
- **Severity:** HIGH

### No input validation on user_input (LLM injection risk)

- **Issue:** `api/server.py:68` and `api/server.py:101` take `request.user_input` and pass it directly to the LLM agent pipeline without any sanitization, length limits, or content filtering. Malicious input could prompt-inject the agent to exfiltrate data or execute unintended tool calls.
- **Files:** `api/server.py:68-83, 99-137, 205-301`
- **Current mitigation:** System prompts provide boundary instructions, but these are advisory, not enforced.
- **Recommendations:** Add input length limits (`max_length=2000`). Add content filtering for injection patterns. Consider adding a "human approval" gate for all tool calls involving external communication (email, interview invites).
- **Severity:** MEDIUM

### No file upload size limit or type validation depth

- **Issue:** `api/server.py:163-197` accepts file uploads but only checks the file extension (`.pdf` or `.txt`). There is no file size limit, no content-type verification, and no sandboxing during PDF parsing (pymupdf is called directly on the uploaded bytes).
- **Files:** `api/server.py:163-197`
- **Current mitigation:** The file is only parsed for text extraction; pymupdf is battle-tested.
- **Recommendations:** Add a maximum file size (e.g., `10MB`). Verify MIME type in addition to extension. Wrap PDF parsing in a subprocess or resource-limited context to prevent OOM from malicious PDFs.
- **Severity:** MEDIUM

### OpenRouter API key sent as HTTP-Referer header

- **Issue:** `agent/agent.py:51` and `rag/vector_store.py:89` set a hardcoded `HTTP-Referer: https://github.com/recruitment-agent` header when using OpenRouter. This leaks the identity of the software but also means OpenRouter's billing/call attribution is tied to this string. If the API key is compromised, this header provides no authentication protection.
- **Files:** `agent/agent.py:51`, `rag/vector_store.py:89`
- **Severity:** LOW

## Performance Bottlenecks

### InMemorySaver loses all state on restart

- **Issue:** `main.py:70` uses `InMemorySaver()` as the checkpoint saver. All active session threads (including HITL workflows awaiting HR approval) are lost when the process restarts. A server restart mid-HITL means the HR must start over.
- **Files:** `main.py:70`, `api/server.py:99-158`
- **Improvement path:** Replace with `SqliteSaver` or `PostgresSaver` from `langgraph-checkpoint` so thread state survives restarts. This is critical for the HITL flow.
- **Severity:** MEDIUM

### FAISS index loaded into memory on every cache miss

- **Issue:** `rag/retriever.py:27-34` uses a simple `_vector_store = None` cache. The full FAISS index (~hundreds of MB with many resumes) is loaded on cache invalidation or first request. The `load_local` call (vector_store.py:161) also deserializes the entire index into memory.
- **Files:** `rag/retriever.py:27-34`, `rag/vector_store.py:151-162`
- **Severity:** LOW (acceptable for current scale)

### No streaming timeout or resource cleanup in SSE endpoint

- **Issue:** `api/server.py:205-301` (`_stream_recruitment`) uses an executor thread (`run_in_executor`) with no timeout. If the LLM hangs or the graph gets stuck, the SSE connection stays open indefinitely with no server-side cleanup.
- **Files:** `api/server.py:250`
- **Improvement path:** Add a timeout around `loop.run_in_executor(None, _run_graph)`. Cancel the future on client disconnect (watch for `asyncio.CancelledError` via the request's disconnect handler).
- **Severity:** LOW

## Fragile Areas

### Circular import workaround in `_process_one_candidate`

- **Issue:** `agent/agent.py:278` imports `_read_resume_file` from `agent.tools` inside the function body to break a circular dependency. This is fragile: if the import ever becomes genuinely circular (e.g., `tools.py` needs something from `agent.py`), this will break silently.
- **Files:** `agent/agent.py:278`
- **Why fragile:** Inline imports are invisible to static analysis and tooling. Renaming or moving `_read_resume_file` would not trigger any import error at module load time -- only at runtime when the function is called.
- **Safe modification:** Extract shared low-level utilities (email regex, resume reading) into `agent/_utils.py` that has no dependencies on `agent.py` or `tools.py`.
- **Test coverage:** No tests exist for this fallback path.
- **Severity:** MEDIUM

### Overly broad `except Exception` throughout

- **Issue:** 16+ places in the codebase catch `Exception` with no distinction. Key locations include `agent/mcp_tools.py:117` (swallows all MCP tool loading failures), `agent/memory.py:43` (swallows all ChromaDB init failures), and `api/server.py:344` (swallows all admin rebuild failures). This can mask real bugs (e.g., `ImportError` vs `ValueError` vs `IOError`).
- **Files:** Most `except` clauses across `agent/*.py`, `rag/*.py`, `api/server.py`
- **Why fragile:** A bug in an underlying library (e.g., `chromadb==0.5.0` deprecating an API) would silently fall back instead of logging a clear error message. The fallback path itself might have its own bugs that are also caught and swallowed.
- **Safe modification:** Use more specific exception types where possible. Log the exception at `ERROR` level before falling back. At minimum, ensure `logger.exception(...)` is used instead of `logger.warning(...)` for unexpected errors.
- **Test coverage:** No tests for fallback paths.
- **Severity:** MEDIUM

### No graceful shutdown for MCP background event loop

- **Issue:** `agent/mcp_tools.py:66-78` spins up a daemon thread with an asyncio event loop at import time. There is no mechanism to stop the loop gracefully on shutdown. Resources (MCP subprocesses opened via `stdio` transport) may leak.
- **Files:** `agent/mcp_tools.py:66-78, 81-119`
- **Why fragile:** Daemon threads are killed abruptly when the process exits, leaving subprocesses (like `npx @anthropic/mcp-server-fetch`) orphaned.
- **Safe modification:** Store the MCP client instances and provide a `shutdown()` function. Register it with `atexit` or FastAPI's lifespan handler.
- **Severity:** LOW

## Missing Critical Features

### No rate limiting on API endpoints

- **Issue:** All API endpoints have no rate limiting. An attacker or misconfigured client can call `/recruit` in a tight loop, consuming unbounded LLM API credits.
- **Files:** `api/server.py`
- **Blocks:** Safe production deployment without a reverse proxy rate limiter.
- **Severity:** MEDIUM

### No request logging / audit trail

- **Issue:** There is no middleware to log incoming requests, response times, or errors. The `/recruit` endpoint does not log what input was received or what output was produced. There is no audit trail for debugging or compliance.
- **Files:** `api/server.py`
- **Blocks:** Debugging production issues, compliance with data protection regulations.
- **Severity:** MEDIUM

### No resume_text size enforcement

- **Issue:** `single_resume_agent` (`agent/agent.py:458`) takes `resume_text` which could be arbitrarily large. The text is sent to the LLM for parsing. A multi-megabyte resume TXT would consume excessive context and cost.
- **Files:** `agent/agent.py:460-462`, `api/server.py:93-94`
- **Severity:** LOW

### eval JSONL data files committed to repository

- **Issue:** 10+ `.jsonl` evaluation data files are committed under `data/`. While small individually, multiple copies of eval sets (smoke, run, aligned, mix520) create confusion about which is the authoritative evaluation set.
- **Files:** `data/eval_*.jsonl` (10 files)
- **Severity:** LOW

## Dependencies at Risk

### `chromadb>=0.5.0` — compatibility risk with pysqlite3

- **Risk:** ChromaDB requires `pysqlite3-binary` on many Linux systems due to the bundled SQLite version requirement. If the system Python uses the system sqlite3 (often < 3.35), ChromaDB fails at import time with an opaque error.
- **Impact:** The fallback to JSON file mode (`agent/memory.py:43`) masks this failure. The system degrades silently -- losing semantic search capability with no indication to the user.
- **Current mitigation:** `agent/memory.py` catches the exception and falls back to JSON files.
- **Severity:** MEDIUM

### `langchain-mcp-adapters>=0.1.0` — early-stage package

- **Risk:** `langchain-mcp-adapters` is a relatively new package (pre-1.0). Breaking API changes are likely. The MCP integration is entirely optional (gracefully degrades to empty tool list), but if it suddenly stops loading, the MCP tooling silently disappears.
- **Impact:** MCP tools (`fetch`, etc.) silently vanish; no user-facing alert.
- **Severity:** LOW

---

*Concerns audit: 2026-04-26*
