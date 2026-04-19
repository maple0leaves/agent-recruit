"""Vector store builder for resume documents."""

import json
import os
import sys
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

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


def build_vector_store(resume_dir: str, store_path: str) -> FAISS:
    """Build and persist a FAISS vector store from resume documents.

    Args:
        resume_dir: Directory containing .txt resume files
        store_path: Path to save the FAISS index

    Returns:
        FAISS vector store instance
    """
    docs = _load_resume_documents(resume_dir)
    if not docs:
        raise ValueError(f"No resume .txt or .pdf files found in: {resume_dir}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    split_docs = splitter.split_documents(docs)

    print(f"[VectorStore] 正在加载 Embedding 模型...")
    embeddings = _get_embeddings()
    store = FAISS.from_documents(split_docs, embeddings)
    store.save_local(store_path)
    _write_resume_manifest(resume_dir, store_path)
    _invalidate_retriever_cache()
    print(f"[VectorStore] 构建完成，共 {len(split_docs)} 个文本块，已保存到 {store_path}")
    return store


def load_vector_store(store_path: str) -> FAISS:
    """Load an existing FAISS vector store from disk.

    Args:
        store_path: Path where FAISS index is saved

    Returns:
        FAISS vector store instance
    """
    embeddings = _get_embeddings()
    store = FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
    return store


def get_or_build_vector_store(resume_dir: str, store_path: str) -> FAISS:
    """加载已有 FAISS；不存在则全量构建。

    当 ``config.VECTOR_INDEX_AUTO_REBUILD`` 为真时：若 ``index.faiss`` 已存在但
    简历目录相对 ``resume_manifest.json`` 有变化（增删改、替换），则自动重建并刷新检索缓存。
    """
    from config import VECTOR_INDEX_AUTO_REBUILD

    index_file = Path(store_path) / "index.faiss"
    if not index_file.exists():
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
