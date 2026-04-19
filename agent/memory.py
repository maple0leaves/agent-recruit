"""Memory management for the recruitment agent system.

Short-term memory: handled automatically by LangGraph message state.
Long-term memory: ChromaDB vector store with semantic search,
with graceful fallback to JSON file store when ChromaDB is unavailable.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEMORY_FILE = PROJECT_ROOT / "data" / "candidate_memory.json"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_memory"
_COLLECTION_NAME = "candidate_records"

_chroma_collection = None
_chroma_available = False
_chroma_initialized = False


def _get_collection():
    """Lazy-initialize ChromaDB and return the collection, or None on failure."""
    global _chroma_collection, _chroma_available, _chroma_initialized
    if _chroma_initialized:
        return _chroma_collection
    _chroma_initialized = True
    try:
        import chromadb

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _chroma_collection = client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        _chroma_available = True
        logger.info("ChromaDB 初始化成功，路径: %s", CHROMA_DIR)
    except Exception as exc:
        _chroma_available = False
        logger.warning("ChromaDB 不可用，降级为 JSON 文件模式: %s", exc)
    return _chroma_collection


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


def _enrich_record(meta: dict, document: str, distance: float | None = None) -> dict:
    rec = {
        "candidate_name": meta.get("candidate_name", ""),
        **_meta_to_record(meta),
        "document": document,
    }
    if distance is not None:
        rec["similarity"] = round(1.0 - distance, 4)
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

    collection = _get_collection()
    if collection is not None:
        try:
            doc = _build_document(candidate_name, position, match_score, decision)
            doc_id = f"{candidate_name}_{uuid4().hex[:8]}"
            collection.add(
                ids=[doc_id],
                documents=[doc],
                metadatas=[
                    {
                        "candidate_name": candidate_name,
                        "position": position,
                        "match_score": match_score,
                        "decision": decision,
                        "timestamp": timestamp,
                    }
                ],
            )
            logger.info("ChromaDB 记录已保存: %s", doc_id)
        except Exception as exc:
            logger.error("ChromaDB 写入失败: %s", exc)


def get_candidate_history(candidate_name: str) -> list[dict]:
    """Retrieve historical records for a candidate (exact metadata filter)."""
    collection = _get_collection()
    if collection is not None:
        try:
            results = collection.get(where={"candidate_name": candidate_name})
            if results and results["ids"]:
                records = [_meta_to_record(m) for m in results["metadatas"]]
                logger.info(
                    "ChromaDB 返回 %d 条记录 (候选人: %s)",
                    len(records),
                    candidate_name,
                )
                return records
        except Exception as exc:
            logger.warning("ChromaDB 查询失败，降级为 JSON: %s", exc)

    data = _load_memory()
    return data.get(candidate_name, [])


# ── New semantic search API ──────────────────────────────────────────────────


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
    collection = _get_collection()
    if collection is None:
        logger.warning("search_memory 需要 ChromaDB，当前不可用")
        return []

    try:
        count = collection.count()
        if count == 0:
            return []
        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, count),
        )
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0] if results.get("distances") else [None] * len(ids)

        records = [
            _enrich_record(metas[i], docs[i], dists[i]) for i in range(len(ids))
        ]
        logger.info("search_memory 返回 %d 条结果 (query: %s)", len(records), query[:60])
        return records
    except Exception as exc:
        logger.error("search_memory 失败: %s", exc)
        return []


def search_candidate_similar(
    candidate_name: str, top_k: int = 3
) -> list[dict]:
    """Find other candidates with similar backgrounds.

    Uses the target candidate's most recent record as the semantic query seed,
    then excludes the target's own records from results.

    Args:
        candidate_name: Reference candidate name
        top_k: Maximum number of similar candidates to return

    Returns:
        List of records for similar (other) candidates.
    """
    collection = _get_collection()
    if collection is None:
        logger.warning("search_candidate_similar 需要 ChromaDB，当前不可用")
        return []

    try:
        own = collection.get(where={"candidate_name": candidate_name})
        if not own or not own["ids"]:
            logger.info("未找到候选人记录: %s", candidate_name)
            return []

        timestamps = [m.get("timestamp", "") for m in own["metadatas"]]
        latest_idx = max(range(len(timestamps)), key=lambda i: timestamps[i])
        seed_doc = own["documents"][latest_idx]
        own_id_set = set(own["ids"])

        count = collection.count()
        if count == 0:
            return []
        fetch_k = min(top_k + len(own_id_set), count)

        results = collection.query(query_texts=[seed_doc], n_results=fetch_k)
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0] if results.get("distances") else [None] * len(ids)

        records = []
        for i in range(len(ids)):
            if ids[i] in own_id_set:
                continue
            records.append(_enrich_record(metas[i], docs[i], dists[i]))
            if len(records) >= top_k:
                break

        logger.info(
            "找到 %d 个与 %s 相似的候选人", len(records), candidate_name
        )
        return records
    except Exception as exc:
        logger.error("search_candidate_similar 失败: %s", exc)
        return []
