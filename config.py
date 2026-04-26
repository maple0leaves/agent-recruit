"""Global configuration for the recruitment system."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _resolve_path(path_value: str) -> str:
    """Resolve relative project paths against the project root."""
    path = Path(path_value)
    if path.is_absolute():
        return str(path)
    return str((BASE_DIR / path).resolve())

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")   # 留空则使用 OpenAI 官方；填 OpenRouter 地址则走 OpenRouter
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# RAG / Vector Store
VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "faiss")   # faiss | chroma
VECTOR_STORE_PATH = _resolve_path(os.getenv("VECTOR_STORE_PATH", "data/vector_store"))
RESUME_DIR = _resolve_path(os.getenv("RESUME_DIR", "data/resumes"))
# 使用本地 HuggingFace 模型，无需 OpenAI Key
# 中文推荐：BAAI/bge-small-zh-v1.5（小而快）或 shibing624/text2vec-base-chinese
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "openai")  # openai | huggingface
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
# 为 true 时：每次加载索引前比对简历目录指纹，有增删改则自动全量重建 FAISS 并刷新内存缓存
VECTOR_INDEX_AUTO_REBUILD = os.getenv("VECTOR_INDEX_AUTO_REBUILD", "true").lower() == "true"

# Rerank（API 模式，兼容 Cohere / Jina / aihubmix）
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "false").lower() == "true"
RERANK_MODEL = os.getenv("RERANK_MODEL", "jina-reranker-v2-base-multilingual")
RERANK_API_URL = os.getenv("RERANK_API_URL", "")   # 留空则自动从 OPENAI_BASE_URL 推导
RERANK_API_KEY = os.getenv("RERANK_API_KEY", "")   # 留空则复用 OPENAI_API_KEY

# ChromaDB Memory
CHROMA_MEMORY_PATH = _resolve_path(os.getenv("CHROMA_MEMORY_PATH", "data/chroma_memory"))

# LangSmith (optional)
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "recruitment-agent")


def init_langsmith() -> bool:
    """Activate LangSmith tracing by setting required env vars.

    Returns True if tracing was enabled, False otherwise.
    """
    if not LANGSMITH_TRACING or not LANGSMITH_API_KEY:
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    return True


# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ── Database ───────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/dev.db")

# ── JWT / Auth ─────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production-min-32-bytes!")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ── CORS ───────────────────────────────────────────────────────────────
# Frontend dev server + production domain
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000")
CORS_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
