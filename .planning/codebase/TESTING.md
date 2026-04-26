# Testing Patterns

**Analysis Date:** 2026-04-26

## Test Framework

**No unit test framework is configured.** There are no `pytest`, `unittest`, or `vitest` configurations. The project has:
- No `pytest.ini`, `conftest.py`, or `pyproject.toml` test config
- No `tox.ini` or `noxfile.py`
- No files matching `test_*.py`, `*_test.py`, `*.test.py`, or `*.spec.py`

**Structured evaluation** is performed through standalone Python scripts in the `scripts/` directory, not through a formal test framework. These scripts exercise the system end-to-end and measure retrieval metrics.

## Test Scripts

There are 5 scripts in `scripts/`, each designed to be run directly from the project root:

| Script | Purpose | Type |
|--------|---------|------|
| `scripts/eval_rag_metrics.py` | Offline RAG retrieval metrics (Recall@K, MRR, latency) | Offline eval |
| `scripts/eval_end_to_end.py` | Full LangGraph workflow evaluation (Recall@K, MRR, wall time) | End-to-end eval |
| `scripts/gen_eval_from_category.py` | Generate weakly-labeled eval JSONL from testdataset Category | Data generation |
| `scripts/synth_aligned_eval_llm.py` | Generate LLM-aligned eval JSONL with resume-specific JDs | Data generation |
| `scripts/materialize_multi_pool.py` | Symlink PDFs from multiple Categories into one pool | Test data setup |

**Run commands** (always from project root `/root/project/hellojobs`):

```bash
# RAG retrieval metrics
python scripts/eval_rag_metrics.py
python scripts/eval_rag_metrics.py --top-k 5 --eval data/eval_retrieval.jsonl

# End-to-end workflow eval
python scripts/eval_end_to_end.py
python scripts/eval_end_to_end.py --eval data/eval_end_to_end.jsonl --top-k 5 --limit 3

# Generate eval data from testdataset
python scripts/gen_eval_from_category.py --category INFORMATION-TECHNOLOGY --n 120 --lines 50 --out data/eval_it_retrieval.jsonl

# Generate LLM-aligned eval
python scripts/synth_aligned_eval_llm.py --resumes-dir data/eval_pools/IT_eval_run --lines 10 --out-retrieval data/eval_it_aligned_retrieval.jsonl

# Build multi-category pool
python scripts/materialize_multi_pool.py --out data/eval_pools/mix_520 --spec INFORMATION-TECHNOLOGY:120,ENGINEERING:100
```

## Eval Data Format

**Retrieval eval JSONL** (`data/eval_*_retrieval.jsonl`):

```jsonl
{"query": "招聘熟悉 Java Spring Cloud 与 Redis 的后端开发", "relevant": ["zhang_wei.pdf"]}
{"query": "云原生 Go 开发 Kubernetes Operator", "relevant": ["li_ming.pdf"]}
```

Each row has:
- `query`: The search query text
- `relevant`: List of expected relevant resume filenames

**End-to-end eval JSONL** (`data/eval_*_e2e.jsonl`):

```jsonl
{"user_input": "我司急招一名熟悉 Java、Spring Cloud、Redis ...", "relevant_files": ["zhang_wei.pdf"], "expected_names": ["张伟", "Zhang Wei"]}
{"user_input": "招聘云原生方向实习生：要求 Go、gRPC、Kubernetes ...", "relevant_files": ["li_ming.pdf"], "expected_names": ["李明", "Li Ming"]}
```

Each row has:
- `user_input`: Full natural language job description (processed by triage -> planner -> worker -> reviewer)
- `relevant_files`: Expected resume filenames
- `expected_names`: Optional candidate name strings for fuzzy matching

**Available eval datasets** in `data/`:

| File | Description | Source |
|------|-------------|--------|
| `eval_retrieval.jsonl` | Chinese JD queries, main resume pool | Hand-crafted, ~10 rows |
| `eval_end_to_end.jsonl` | Chinese JD + expected names, main pool | Hand-crafted, ~11 rows |
| `eval_it_smoke_retrieval.jsonl` | IT Category smoke test retrieval | Generated |
| `eval_it_smoke_e2e.jsonl` | IT Category smoke test e2e | Generated |
| `eval_it_run_retrieval.jsonl` | IT Category run retrieval | Generated |
| `eval_it_run_e2e.jsonl` | IT Category run e2e | Generated |
| `eval_it_aligned_retrieval.jsonl` | IT Category, LLM-aligned JD retrieval | `synth_aligned_eval_llm.py` |
| `eval_it_aligned_e2e.jsonl` | IT Category, LLM-aligned JD e2e | `synth_aligned_eval_llm.py` |
| `eval_mix520_aligned_retrieval.jsonl` | Mix 520 pool, LLM-aligned retrieval | `synth_aligned_eval_llm.py` |
| `eval_mix520_aligned_e2e.jsonl` | Mix 520 pool, LLM-aligned e2e | `synth_aligned_eval_llm.py` |

## RAG Evaluation Approach

**Script:** `scripts/eval_rag_metrics.py`

**Metrics computed:**
- **Recall@K**: For each query, checks whether any relevant document appears in the top-K results. 1.0 if hit, 0.0 if miss. Averaged across all queries.
- **MRR (Mean Reciprocal Rank)**: 1 / rank_of_first_relevant. 0 if no hit. Averaged across all queries.
- **Latency (P50 and mean)**: Wall-clock time of `retriever.invoke()` in milliseconds.

**Implementation pattern:**

```python
retriever = get_retriever(top_k=args.top_k)
for row in rows:
    q = row["query"]
    want = {Path(x).name for x in row.get("relevant", [])}
    t0 = time.perf_counter()
    docs = retriever.invoke(q)
    latencies.append((time.perf_counter() - t0) * 1000.0)
    # Check hit at each position
    hit_at = None
    for i, n in enumerate(doc_sources(docs), start=1):
        if n in want:
            hit_at = i
            break
    recalls.append(1.0 if hit_at is not None else 0.0)
    mrrs.append(1.0 / hit_at if hit_at else 0.0)
```

**Match criteria:** Ground-truth matching uses the filename extracted from `doc.metadata["source"]`, comparing the `Path(f).name` against the `relevant` list in the eval row. This is a file-level match, not a semantic judgment.

**Dependencies for running:** Requires a built FAISS index pointing to a candidate pool containing the relevant files. Set `RESUME_DIR` environment variable and rebuild index:

```bash
export RESUME_DIR=/root/project/hellojobs/data/eval_pools/mix_520
python scripts/eval_rag_metrics.py --eval data/eval_mix520_aligned_retrieval.jsonl --top-k 5
```

## End-to-End Evaluation Approach

**Script:** `scripts/eval_end_to_end.py`

**Metrics computed:**
- **Recall@K** -- same concept but on the final `match_results` after the full LangGraph pipeline
- **MRR** -- rank of first hit in the sorted match_results
- **any_hit** (implied via Recall binary value)
- **num_matches** -- count of match_results returned
- **wall_time_ms** -- total wall-clock time for `run()`
- **tool_calls / rag_retrievals** -- from `get_run_metrics()` observability module

**Implementation flow:**

```python
from main import run
from agent.observability import get_run_metrics

for idx, row in enumerate(rows, start=1):
    ui = row["user_input"]
    t0 = time.perf_counter()
    state = run(user_input=ui, resume_text="")
    wall_ms.append((time.perf_counter() - t0) * 1000.0)
    metrics = get_run_metrics()
    matches = normalize_matches(state.get("match_results") or [])
    r = recall_at_k(matches, row, args.top_k)
    m = mrr(matches, row)
```

**Match criteria (`is_hit` function):**

```python
def is_hit(row: dict, m: dict) -> bool:
    files = row.get("relevant_files") or row.get("relevant") or []
    names = row.get("expected_names") or []
    src = (m.get("resume_source") or "").lower()
    cn = (m.get("candidate_name") or "").strip().lower()
    # Match by filename in resume_source
    for f in files:
        base = Path(str(f)).name.lower()
        if base and (base in src or src.endswith("/" + base)):
            return True
    # Match by candidate_name
    for n in names:
        nlow = str(n).strip().lower()
        if nlow in cn or cn in nlow:
            return True
    return False
```

## Test Data Infrastructure

**Resume dataset:** Uses Kaggle's [Resume Dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset) stored in `testdataset/`:
- `testdataset/data/<CATEGORY>/` -- ~2484 PDF resumes across ~24 categories
- `testdataset/Resume/Resume.csv` -- metadata with ID, text, HTML, category
- Language: English primarily

**Data generation scripts:**

1. **`scripts/gen_eval_from_category.py`** -- Randomly samples N PDFs from a single Category, creates "weak label" eval JSONL (template JD + random relevant file)

2. **`scripts/synth_aligned_eval_llm.py`** -- Reads resume PDF excerpts, sends them to the configured LLM to generate aligned job descriptions, produces eval JSONL where the query is genuinely relevant to the target resume. Uses `_build_llm()` from the main agent with `with_structured_output(BatchJD)`.

3. **`scripts/materialize_multi_pool.py`** -- Creates a unified directory of symlinks pointing to PDFs sampled from multiple categories, enabling larger candidate pools with cross-category interference.

**Candidate memory persistence:** `data/candidate_memory.json` stores evaluation records (candidate name, position, match score, decision, timestamp) written by `save_candidate_record()` during the e2e workflow.

## Known Eval Results (from `testdataset/TEST_SUMMARY.md`)

| Setup | Metric | Value |
|-------|--------|-------|
| Weak label, 80 IT PDFs | Recall@5 | ~0.04 |
| LLM-aligned, 80 IT PDFs (8 rows) | Recall@5 | 1.0 |
| LLM-aligned, 80 IT PDFs (8 rows) | MRR | 0.875 |
| LLM-aligned, 520 mix PDFs (12 rows) | Recall@5 | 0.9167 |
| LLM-aligned, 520 mix PDFs (12 rows) | MRR | 0.8611 |
| LLM-aligned, 520 mix PDFs (12 rows) | Retrieval latency P50 | ~486 ms |
| E2E, 520 mix PDFs (12 rows) | Recall@5 | 0.8333 |
| E2E, 520 mix PDFs (12 rows) | MRR | 0.8333 |
| E2E, 520 mix PDFs (12 rows) | Avg wall time | ~19.1 s/run |
| E2E, 520 mix PDFs (12 rows) | Median wall time | ~17.4 s/run |
| E2E, main pool (11 rows) | Avg wall time | ~12.4 s/run |

## Coverage

**No coverage tool configured.** There is no `.coveragerc`, `pyproject.toml` coverage section, or `pytest-cov` in `requirements.txt`.

## CI/CD

**No CI configuration detected** -- no `.github/workflows/`, `.gitlab-ci.yml`, or other CI pipeline configuration.

## What Is NOT Tested

- **Individual agent node functions** (`planner_agent`, `worker_agent`, `reviewer_agent`, `single_resume_agent`) -- no unit tests
- **Tool functions** (`search_candidates`, `analyze_resume`, `score_match`, `memory functions`) -- no unit tests
- **API endpoints** (`/recruit`, `/recruit/stream`, `/upload-resume`, `/skills`, `/admin/rebuild-index`) -- no API tests
- **Edge cases** (empty inputs, malformed PDFs, network failures, API timeouts) -- not tested
- **RAG reranking** (disabled by default; only tested when `RERANK_ENABLED=true` manually)
- **MCP tool integration** (depends on external servers; no mock tests)

## Testing Gaps

| Area | Gap | Risk |
|------|-----|------|
| Agent logic | No unit tests for node functions | Changes to routing logic may break workflow without detection |
| Tool functions | No unit tests for individual tools | LLM parsing changes may produce invalid output silently |
| API routes | No integration tests | HTTP error handling and response schemas not validated |
| Edge cases | Empty resume, unparseable PDF, timeout scenarios | Production failures not covered |
| Rerank | Disabled by default, no tests when enabled | Rerank integration may break after dependency updates |
| Observability | Metrics collection not tested | Regressions in latency tracking would go unnoticed |
| Regression | No automated CI pipeline | Changes land without any safety net |

## Dependencies for Testing

**Test/benchmark dependencies** (from `requirements.txt`):
- `pymupdf>=1.24.0` -- PDF text extraction (used by both main code and eval scripts)
- `langchain-core`, `langchain-openai` -- needed by eval scripts for imports

**No test-specific dependencies** -- no pytest, hypothesis, factory_boy, or mock libraries.

---

*Testing analysis: 2026-04-26*
