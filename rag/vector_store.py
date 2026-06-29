"""Vector store builder for resume documents."""

import json
import os
import sys
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def _ensure_milvus_dir(uri: str) -> None:
    """Milvus Lite 的本地 .db 文件需要父目录存在（远程 uri 则忽略）。"""
    if "://" not in uri:
        Path(uri).parent.mkdir(parents=True, exist_ok=True)


def _make_client(uri: str):
    """Create a MilvusClient (Lite local file or remote http uri)."""
    from pymilvus import MilvusClient

    _ensure_milvus_dir(uri)
    return MilvusClient(uri)


def _collection_exists(uri: str, collection: str) -> bool:
    """检查 Milvus 集合是否已存在（Milvus Lite：先确认 db 文件存在）。"""
    if "://" not in uri and not Path(uri).exists():
        return False
    try:
        return _make_client(uri).has_collection(collection)
    except Exception:
        return False


class MilvusResumeStore:
    """轻量简历向量库封装（基于 pymilvus MilvusClient）。

    对外暴露 ``similarity_search(query, k)``，与原 FAISS 接口一致，
    供 ``rag.retriever.RerankRetriever`` 直接复用。
    """

    def __init__(self, uri: str, collection: str, embeddings):
        self._uri = uri
        self._collection = collection
        self._embeddings = embeddings
        self._client = _make_client(uri)

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        if not self._client.has_collection(self._collection):
            return []
        vector = self._embeddings.embed_query(query)
        hits = self._client.search(
            self._collection,
            data=[vector],
            limit=k,
            search_params={"metric_type": "COSINE"},
            output_fields=["text", "name", "source"],
        )
        docs: list[Document] = []
        for hit in hits[0]:
            entity = hit.get("entity", {})
            docs.append(
                Document(
                    page_content=entity.get("text", ""),
                    metadata={
                        "name": entity.get("name", ""),
                        "source": entity.get("source", ""),
                        "score": hit.get("distance"),
                    },
                )
            )
        return docs

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

RESUME_MANIFEST_NAME = "resume_manifest.json"


def _resume_catalog(resume_dir: str) -> dict:
    """简历目录指纹：用于判断是否需要相对磁盘索引重新建库。"""
    root = Path(resume_dir)
    files: list[dict] = []
    if not root.is_dir():
        return {"v": 1, "files": files}
    for f in sorted(root.iterdir()):
        if f.is_file() and f.suffix.lower() in (".txt", ".pdf"):
            try:
                st = f.stat()
                files.append(
                    {
                        "name": f.name,
                        "mtime": int(st.st_mtime),
                        "size": st.st_size,
                    }
                )
            except OSError:
                continue
    return {"v": 1, "files": files}


def _manifest_path(store_path: str) -> Path:
    return Path(store_path) / RESUME_MANIFEST_NAME


def _read_saved_catalog(store_path: str) -> dict | None:
    mp = _manifest_path(store_path)
    if not mp.is_file():
        return None
    try:
        return json.loads(mp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_resume_manifest(resume_dir: str, store_path: str) -> None:
    Path(store_path).mkdir(parents=True, exist_ok=True)
    catalog = _resume_catalog(resume_dir)
    _manifest_path(store_path).write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _invalidate_retriever_cache() -> None:
    try:
        from rag.retriever import invalidate_vector_store_cache

        invalidate_vector_store_cache()
    except Exception:
        pass


def _extract_pdf_text(file: Path) -> str:
    """Extract plain text from a PDF file using pymupdf (better CJK support)."""
    import fitz  # pymupdf

    doc = fitz.open(str(file))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def _get_embeddings():
    """Return the embedding model instance (OpenAI-compatible API)."""
    from config import EMBEDDING_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL

    from langchain_openai import OpenAIEmbeddings

    kwargs: dict = {"model": EMBEDDING_MODEL, "api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
        kwargs["default_headers"] = {
            "HTTP-Referer": "https://github.com/recruitment-agent",
        }
    return OpenAIEmbeddings(**kwargs)


def _load_resume_documents(resume_dir: str) -> list[Document]:
    """Load all .txt and .pdf resume files from the resume directory."""
    docs = []
    resume_path = Path(resume_dir)
    if not resume_path.exists():
        return docs

    for file in sorted(resume_path.iterdir()):
        if file.suffix.lower() == ".txt":
            text = file.read_text(encoding="utf-8")
        elif file.suffix.lower() == ".pdf":
            text = _extract_pdf_text(file)
        else:
            continue

        if not text.strip():
            print(f"[VectorStore] 警告：{file.name} 内容为空，已跳过")
            continue

        candidate_name = file.stem.replace("_", " ").title()
        docs.append(
            Document(
                page_content=text,
                metadata={"name": candidate_name, "source": str(file)},
            )
        )
    return docs


def build_vector_store(resume_dir: str, store_path: str) -> MilvusResumeStore:
    """Build and persist a Milvus collection from resume documents.

    简历目录下的 .txt/.pdf 切块后写入 Milvus 集合（全量重建，先 drop 旧集合）。
    ``store_path`` 仅用于存放目录指纹 manifest；向量数据存于 ``config.MILVUS_URI``。

    Args:
        resume_dir: Directory containing .txt / .pdf resume files
        store_path: Path to store the resume manifest (rebuild fingerprint)

    Returns:
        MilvusResumeStore wrapper instance
    """
    from pymilvus import DataType
    from config import MILVUS_URI, MILVUS_RESUME_COLLECTION

    docs = _load_resume_documents(resume_dir)
    if not docs:
        raise ValueError(f"No resume .txt or .pdf files found in: {resume_dir}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    split_docs = splitter.split_documents(docs)

    print("[VectorStore] 正在加载 Embedding 模型并写入 Milvus...")
    embeddings = _get_embeddings()
    vectors = embeddings.embed_documents([d.page_content for d in split_docs])
    dim = len(vectors[0])

    client = _make_client(MILVUS_URI)
    if client.has_collection(MILVUS_RESUME_COLLECTION):
        client.drop_collection(MILVUS_RESUME_COLLECTION)

    schema = client.create_schema(auto_id=True, enable_dynamic_field=False)
    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dim)
    schema.add_field("text", DataType.VARCHAR, max_length=8192)
    schema.add_field("name", DataType.VARCHAR, max_length=512)
    schema.add_field("source", DataType.VARCHAR, max_length=1024)

    index_params = client.prepare_index_params()
    index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="COSINE")
    client.create_collection(
        collection_name=MILVUS_RESUME_COLLECTION,
        schema=schema,
        index_params=index_params,
    )

    rows = []
    for doc, vec in zip(split_docs, vectors):
        rows.append(
            {
                "vector": vec,
                "text": doc.page_content[:8192],
                "name": str(doc.metadata.get("name", ""))[:512],
                "source": str(doc.metadata.get("source", ""))[:1024],
            }
        )
    client.insert(MILVUS_RESUME_COLLECTION, rows)
    client.flush(MILVUS_RESUME_COLLECTION)

    _write_resume_manifest(resume_dir, store_path)
    _invalidate_retriever_cache()
    print(f"[VectorStore] 构建完成，共 {len(split_docs)} 个文本块，已写入 Milvus 集合 {MILVUS_RESUME_COLLECTION}")
    return MilvusResumeStore(MILVUS_URI, MILVUS_RESUME_COLLECTION, embeddings)


def load_vector_store(store_path: str | None = None) -> MilvusResumeStore:
    """Load an existing Milvus collection (embeds only at query time).

    Args:
        store_path: 未使用，保留以兼容旧签名

    Returns:
        MilvusResumeStore wrapper instance
    """
    from config import MILVUS_URI, MILVUS_RESUME_COLLECTION

    return MilvusResumeStore(MILVUS_URI, MILVUS_RESUME_COLLECTION, _get_embeddings())


def get_or_build_vector_store(resume_dir: str, store_path: str) -> MilvusResumeStore:
    """加载已有 Milvus 集合；不存在则全量构建。

    当 ``config.VECTOR_INDEX_AUTO_REBUILD`` 为真时：若集合已存在但简历目录相对
    ``resume_manifest.json`` 有变化（增删改、替换），则自动重建并刷新检索缓存。
    """
    from config import VECTOR_INDEX_AUTO_REBUILD, MILVUS_URI, MILVUS_RESUME_COLLECTION

    if not _collection_exists(MILVUS_URI, MILVUS_RESUME_COLLECTION):
        return build_vector_store(resume_dir, store_path)

    if VECTOR_INDEX_AUTO_REBUILD:
        current = _resume_catalog(resume_dir)
        saved = _read_saved_catalog(store_path)
        if saved != current:
            print(
                "[VectorStore] 检测到简历目录与已保存索引不一致，自动重建向量索引…",
                flush=True,
            )
            return build_vector_store(resume_dir, store_path)

    return load_vector_store(store_path)
