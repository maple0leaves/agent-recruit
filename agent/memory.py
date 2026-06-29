"""Memory management for the recruitment agent system.

Short-term memory: handled automatically by LangGraph message state.
Long-term memory: Milvus (Lite) vector store with semantic search,
with graceful fallback to a JSON file store when Milvus / embeddings
are unavailable.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMORY_FILE = PROJECT_ROOT / "data" / "candidate_memory.json"

_milvus_client = None
_milvus_available = False
_milvus_initialized = False
_collection_ready = False


def _get_client():
    """Lazy-initialize the Milvus (Lite) client, or None on failure."""
    global _milvus_client, _milvus_available, _milvus_initialized
    if _milvus_initialized:
        return _milvus_client
    _milvus_initialized = True
    try:
        from pymilvus import MilvusClient
        from config import MILVUS_URI

        if "://" not in MILVUS_URI:
            Path(MILVUS_URI).parent.mkdir(parents=True, exist_ok=True)
        _milvus_client = MilvusClient(MILVUS_URI)
        _milvus_available = True
        logger.info("Milvus 记忆库初始化成功: %s", MILVUS_URI)
    except Exception as exc:
        _milvus_available = False
        logger.warning("Milvus 不可用，降级为 JSON 文件模式: %s", exc)
    return _milvus_client


def _embed(text: str) -> list[float] | None:
    """Embed a text via the shared embedding backend (network-dependent)."""
    try:
        from rag.vector_store import _get_embeddings

        return _get_embeddings().embed_query(text)
    except Exception as exc:
        logger.warning("记忆 embedding 失败（需要可用的 embedding 服务）: %s", exc)
        return None


def _ensure_collection(vector_dim: int) -> bool:
    """Create the candidate_records collection on first use. Returns readiness."""
    global _collection_ready
    client = _get_client()
    if client is None:
        return False
    if _collection_ready:
        return True
    try:
        from pymilvus import DataType
        from config import MILVUS_MEMORY_COLLECTION

        if client.has_collection(MILVUS_MEMORY_COLLECTION):
            _collection_ready = True
            return True

        schema = client.create_schema(auto_id=True, enable_dynamic_field=False)
        schema.add_field("id", DataType.INT64, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=vector_dim)
        schema.add_field("candidate_name", DataType.VARCHAR, max_length=256)
        schema.add_field("position", DataType.VARCHAR, max_length=256)
        schema.add_field("match_score", DataType.INT64)
        schema.add_field("decision", DataType.VARCHAR, max_length=64)
        schema.add_field("timestamp", DataType.VARCHAR, max_length=64)
        schema.add_field("document", DataType.VARCHAR, max_length=4096)

        index_params = client.prepare_index_params()
        index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="COSINE")
        client.create_collection(
            collection_name=MILVUS_MEMORY_COLLECTION,
            schema=schema,
            index_params=index_params,
        )
        _collection_ready = True
        logger.info("Milvus 集合已创建: %s (dim=%d)", MILVUS_MEMORY_COLLECTION, vector_dim)
        return True
    except Exception as exc:
        logger.error("创建 Milvus 集合失败: %s", exc)
        return False


# ── JSON fallback ────────────────────────────────────────────────────────────


def _load_memory() -> dict:
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    return {}


def _save_memory(data: dict) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEMORY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── Helpers ──────────────────────────────────────────────────────────────────

_DECISION_LABELS = {
    "approved": "批准录用",
    "recommended": "推荐面试",
    "hold": "暂缓考虑",
    "rejected": "未通过筛选",
}


def _build_document(
    candidate_name: str, position: str, match_score: int, decision: str
) -> str:
    label = _DECISION_LABELS.get(decision, decision)
    return (
        f"候选人{candidate_name}，应聘{position}，"
        f"匹配分数{match_score}，决定：{label}"
    )


def _meta_to_record(meta: dict) -> dict:
    return {
        "position": meta.get("position", ""),
        "match_score": int(meta.get("match_score", 0)),
        "decision": meta.get("decision", ""),
        "timestamp": meta.get("timestamp", ""),
    }


def _enrich_record(meta: dict, document: str, similarity: float | None = None) -> dict:
    rec = {
        "candidate_name": meta.get("candidate_name", ""),
        **_meta_to_record(meta),
        "document": document,
    }
    if similarity is not None:
        rec["similarity"] = round(float(similarity), 4)
    return rec


# ── Public API (backward-compatible) ─────────────────────────────────────────


def save_candidate_record(
    candidate_name: str, match_score: int, position: str, decision: str
) -> None:
    """Persist a candidate evaluation result to long-term memory."""
    timestamp = datetime.now().isoformat()

    data = _load_memory()
    data.setdefault(candidate_name, []).append(
        {
            "position": position,
            "match_score": match_score,
            "decision": decision,
            "timestamp": timestamp,
        }
    )
    _save_memory(data)
    logger.info("JSON 记录已保存: %s / %s", candidate_name, position)

    client = _get_client()
    if client is None:
        return
    doc = _build_document(candidate_name, position, match_score, decision)
    vector = _embed(doc)
    if vector is None:
        logger.warning("跳过 Milvus 写入（embedding 不可用）: %s", candidate_name)
        return
    if not _ensure_collection(len(vector)):
        return
    try:
        from config import MILVUS_MEMORY_COLLECTION

        client.insert(
            MILVUS_MEMORY_COLLECTION,
            [
                {
                    "vector": vector,
                    "candidate_name": candidate_name,
                    "position": position,
                    "match_score": int(match_score),
                    "decision": decision,
                    "timestamp": timestamp,
                    "document": doc,
                }
            ],
        )
        logger.info("Milvus 记录已保存: %s", candidate_name)
    except Exception as exc:
        logger.error("Milvus 写入失败: %s", exc)


def get_candidate_history(candidate_name: str) -> list[dict]:
    """Retrieve historical records for a candidate (exact metadata filter).

    纯标量过滤，不需要 embedding，因此即使外网/embedding 不可用也能工作。
    """
    client = _get_client()
    if client is not None:
        try:
            from config import MILVUS_MEMORY_COLLECTION

            if client.has_collection(MILVUS_MEMORY_COLLECTION):
                rows = client.query(
                    MILVUS_MEMORY_COLLECTION,
                    filter=f'candidate_name == "{candidate_name}"',
                    output_fields=["candidate_name", "position", "match_score", "decision", "timestamp"],
                )
                if rows:
                    records = [_meta_to_record(r) for r in rows]
                    logger.info("Milvus 返回 %d 条记录 (候选人: %s)", len(records), candidate_name)
                    return records
        except Exception as exc:
            logger.warning("Milvus 查询失败，降级为 JSON: %s", exc)

    data = _load_memory()
    return data.get(candidate_name, [])


# ── Semantic search API ──────────────────────────────────────────────────────


def search_memory(query: str, top_k: int = 5) -> list[dict]:
    """Search candidate history by semantic similarity.

    Args:
        query: Natural language query, e.g. "有 Python 经验的高分候选人"
        top_k: Maximum number of results to return

    Returns:
        List of matching records sorted by relevance. Each dict contains
        candidate_name, position, match_score, decision, timestamp,
        document, and similarity.
    """
    client = _get_client()
    if client is None:
        logger.warning("search_memory 需要 Milvus，当前不可用")
        return []
    try:
        from config import MILVUS_MEMORY_COLLECTION

        if not client.has_collection(MILVUS_MEMORY_COLLECTION):
            return []
        vector = _embed(query)
        if vector is None:
            return []
        hits = client.search(
            MILVUS_MEMORY_COLLECTION,
            data=[vector],
            limit=top_k,
            search_params={"metric_type": "COSINE"},
            output_fields=["candidate_name", "position", "match_score", "decision", "timestamp", "document"],
        )
        records = []
        for hit in hits[0]:
            entity = hit.get("entity", {})
            records.append(_enrich_record(entity, entity.get("document", ""), hit.get("distance")))
        logger.info("search_memory 返回 %d 条结果 (query: %s)", len(records), query[:60])
        return records
    except Exception as exc:
        logger.error("search_memory 失败: %s", exc)
        return []


def search_candidate_similar(candidate_name: str, top_k: int = 3) -> list[dict]:
    """Find other candidates with similar backgrounds.

    Uses the target candidate's most recent record as the semantic query seed,
    then excludes the target's own records from results.

    Args:
        candidate_name: Reference candidate name
        top_k: Maximum number of similar candidates to return

    Returns:
        List of records for similar (other) candidates.
    """
    client = _get_client()
    if client is None:
        logger.warning("search_candidate_similar 需要 Milvus，当前不可用")
        return []
    try:
        from config import MILVUS_MEMORY_COLLECTION

        if not client.has_collection(MILVUS_MEMORY_COLLECTION):
            return []

        own = client.query(
            MILVUS_MEMORY_COLLECTION,
            filter=f'candidate_name == "{candidate_name}"',
            output_fields=["timestamp", "document"],
        )
        if not own:
            logger.info("未找到候选人记录: %s", candidate_name)
            return []

        latest = max(own, key=lambda r: r.get("timestamp", ""))
        seed_doc = latest.get("document", "")
        if not seed_doc:
            return []
        vector = _embed(seed_doc)
        if vector is None:
            return []

        hits = client.search(
            MILVUS_MEMORY_COLLECTION,
            data=[vector],
            limit=top_k + len(own) + 1,
            search_params={"metric_type": "COSINE"},
            output_fields=["candidate_name", "position", "match_score", "decision", "timestamp", "document"],
        )
        records = []
        for hit in hits[0]:
            entity = hit.get("entity", {})
            if entity.get("candidate_name") == candidate_name:
                continue
            records.append(_enrich_record(entity, entity.get("document", ""), hit.get("distance")))
            if len(records) >= top_k:
                break
        logger.info("找到 %d 个与 %s 相似的候选人", len(records), candidate_name)
        return records
    except Exception as exc:
        logger.error("search_candidate_similar 失败: %s", exc)
        return []
