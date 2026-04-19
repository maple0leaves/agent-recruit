"""Retriever interface for the recruitment RAG pipeline.

Two-stage retrieval: FAISS similarity search → CrossEncoder reranking.
"""

from __future__ import annotations

import sys
import os
from typing import Optional

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_vector_store = None


def invalidate_vector_store_cache() -> None:
    """丢弃内存中的 FAISS 实例。在磁盘上 ``build_vector_store`` 之后调用，避免仍用旧索引。"""
    global _vector_store
    _vector_store = None


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        from config import RESUME_DIR, VECTOR_STORE_PATH
        from rag.vector_store import get_or_build_vector_store

        _vector_store = get_or_build_vector_store(RESUME_DIR, VECTOR_STORE_PATH)
    return _vector_store


class RerankRetriever(BaseRetriever):
    """FAISS retrieval + CrossEncoder reranking.

    First retrieves ``top_k * fetch_k_multiplier`` candidates via dense
    vector search, then rescores them with a CrossEncoder and returns
    the top ``top_k``.
    """

    top_k: int = 5
    fetch_k_multiplier: int = 3

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> list[Document]:
        from rag.reranker import rerank_documents

        fetch_k = self.top_k * self.fetch_k_multiplier
        store = _get_vector_store()
        candidates = store.similarity_search(query, k=fetch_k)
        return rerank_documents(query, candidates, self.top_k)


def get_retriever(top_k: int = 5) -> RerankRetriever:
    """Return a two-stage retriever (FAISS + CrossEncoder rerank).

    Drop-in replacement for the previous single-stage retriever.
    The caller interface (``retriever.invoke(query)``) stays the same.
    """
    return RerankRetriever(top_k=top_k)
