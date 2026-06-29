"""Tool definitions for the recruitment agent system."""

import hashlib
import json
import logging
import re
from functools import lru_cache
from pathlib import Path

from langchain_core.tools import tool

from agent.schemas import CandidateInfo, MatchResult

# 模块级缓存：避免每次工具调用都新建 LLM 客户端 + 重新绑定结构化输出 schema。
# 这两个对象是无状态的，可安全跨线程共享。
_LLM_RESUME_PARSER = None
_LLM_MATCH_SCORER = None


def _get_resume_parser():
    """Return a process-wide singleton LLM bound to CandidateInfo schema."""
    global _LLM_RESUME_PARSER
    if _LLM_RESUME_PARSER is None:
        from agent.agent import _build_structured_llm

        _LLM_RESUME_PARSER = _build_structured_llm(CandidateInfo)
    return _LLM_RESUME_PARSER


def _get_match_scorer():
    """Return a process-wide singleton LLM bound to MatchResult schema."""
    global _LLM_MATCH_SCORER
    if _LLM_MATCH_SCORER is None:
        from agent.agent import _build_structured_llm

        _LLM_MATCH_SCORER = _build_structured_llm(MatchResult)
    return _LLM_MATCH_SCORER


def _read_resume_file_uncached(file_path: str) -> str:
    """Read resume content from a .txt or .pdf file."""
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        import fitz

        doc = fitz.open(str(path))
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(pages)
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=256)
def _read_resume_file(file_path: str) -> str:
    """Cached resume reader. PDF/TXT 解析结果按文件路径缓存，避免反复读盘。"""
    return _read_resume_file_uncached(file_path)


def _keyword_search_candidates(query: str, top_k: int) -> str:
    """Fallback candidate search when vector embeddings are unavailable."""
    from config import RESUME_DIR

    resume_path = Path(RESUME_DIR)
    if not resume_path.exists():
        return json.dumps([], ensure_ascii=False)

    terms = [
        term.lower()
        for term in re.findall(r"[a-zA-Z0-9+#.]+|[\u4e00-\u9fff]{2,}", query)
        if len(term.strip()) >= 2
    ]
    scored: list[tuple[int, Path, str]] = []

    for file in sorted(resume_path.iterdir()):
        if not file.is_file() or file.suffix.lower() not in (".txt", ".pdf"):
            continue
        try:
            resume_text = _read_resume_file(str(file))
        except Exception as exc:
            logger.warning("Keyword fallback skipped unreadable resume %s: %s", file, exc)
            continue

        lower_text = resume_text.lower()
        score = sum(lower_text.count(term) for term in terms)
        if score > 0:
            scored.append((score, file, resume_text))

    if not scored:
        for file in sorted(resume_path.iterdir())[:top_k]:
            if file.is_file() and file.suffix.lower() in (".txt", ".pdf"):
                try:
                    scored.append((0, file, _read_resume_file(str(file))))
                except Exception:
                    continue

    results = []
    for _, file, resume_text in sorted(scored, key=lambda item: item[0], reverse=True)[:top_k]:
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text)
        results.append(
            {
                "name": file.stem.replace("_", " ").title(),
                "email": email_match.group(0) if email_match else "",
                "content": resume_text[:500],
                "source": str(file),
            }
        )
    return json.dumps(results, ensure_ascii=False)


@lru_cache(maxsize=512)
def _analyze_resume_cached(text_hash: str, resume_text: str) -> str:
    """LLM 解析的进程内缓存。同一份简历重复出现时直接返回上次结果。

    Key 用 ``text_hash``（md5），原文也作为参数传入是为了避免 hash 冲突时
    误用旧结果（lru_cache 用全部参数做 key，但只有 text_hash 实际产生哈希）。
    """
    from agent.prompt import RESUME_PARSE_PROMPT

    result = _get_resume_parser().invoke(RESUME_PARSE_PROMPT.format(resume_text=resume_text))
    return result.model_dump_json(ensure_ascii=False)


@tool
def search_candidates(query: str, top_k: int = 5) -> str:
    """Search candidate resumes from the vector store using semantic similarity.

    Args:
        query: Search query, e.g. "Python engineer 3 years experience"
        top_k: Number of candidates to return

    Returns:
        JSON string of matched candidate summaries
    """
    from config import LLM_FORCE_FALLBACK

    if LLM_FORCE_FALLBACK:
        logger.info("LLM fallback mode enabled; using keyword candidate search")
        return _keyword_search_candidates(query, top_k)

    from rag.retriever import get_retriever

    try:
        retriever = get_retriever(top_k=top_k)
        docs = retriever.invoke(query)
    except Exception as exc:
        logger.warning("Vector candidate search failed, using keyword fallback: %s", exc)
        return _keyword_search_candidates(query, top_k)
    results = []
    seen_sources: set[str] = set()

    for doc in docs:
        source = doc.metadata.get("source", "")
        if source and source in seen_sources:
            continue
        if source:
            seen_sources.add(source)

        # 优先复用 vector store 已切好的 chunk，避免重复打开 PDF。
        # 仅当 chunk 明显是被切片的片段（无邮箱且很短）才回退去读全文。
        resume_text = doc.page_content
        needs_full_text = source and len(resume_text) < 400 and "@" not in resume_text
        if needs_full_text and Path(source).exists():
            resume_text = _read_resume_file(source)

        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text)
        # 注意：tool 返回值会进入 LangGraph messages，会被后续 LLM 调用反复
        # 重发。这里只回传摘要 + source 引用，避免全文污染上下文；worker
        # 拿到 source 后通过 _read_resume_file（已带 LRU 缓存）取全文。
        results.append(
            {
                "name": doc.metadata.get("name", "Unknown"),
                "email": email_match.group(0) if email_match else doc.metadata.get("email", ""),
                "content": resume_text[:500],
                "source": source,
            }
        )
    return json.dumps(results, ensure_ascii=False)


@tool
def analyze_resume(resume_text: str) -> str:
    """Parse and extract structured information from a resume text."""
    text_hash = hashlib.md5(resume_text.encode("utf-8")).hexdigest()
    return _analyze_resume_cached(text_hash, resume_text)


@tool
def score_match(candidate_json: str, jd_json: str) -> str:
    """Evaluate the match between a candidate and a job description."""
    from agent.prompt import MATCH_SCORING_PROMPT

    result = _get_match_scorer().invoke(
        MATCH_SCORING_PROMPT.format(
            candidate_info=candidate_json,
            jd_info=jd_json,
        )
    )
    return result.model_dump_json(ensure_ascii=False)


@tool
def query_candidate_history(candidate_name: str) -> str:
    """Query historical interview and evaluation records for a candidate."""
    from agent.memory import get_candidate_history

    history = get_candidate_history(candidate_name)
    return json.dumps(
        {
            "candidate": candidate_name,
            "history": history,
            "note": "Historical records loaded from local memory store" if history else "No historical records found",
        },
        ensure_ascii=False,
    )


@tool
def send_interview_invite(
    candidate_name: str,
    candidate_email: str,
    interview_time: str,
    position: str,
) -> str:
    """Send an interview invitation email to a candidate."""
    return (
        f"[模拟发送] 面试邀请已发送给 {candidate_name}（{candidate_email}），"
        f"岗位：{position}，时间：{interview_time}"
    )


@tool
def send_rejection_email(candidate_name: str, candidate_email: str, position: str) -> str:
    """Send a polite rejection email to a candidate."""
    return (
        f"[模拟发送] 婉拒邮件已发送给 {candidate_name}（{candidate_email}），"
        f"岗位：{position}"
    )


logger = logging.getLogger(__name__)

_BUILTIN_TOOLS = [
    search_candidates,
    analyze_resume,
    score_match,
    query_candidate_history,
    send_interview_invite,
    send_rejection_email,
]

ALL_TOOLS: list = list(_BUILTIN_TOOLS)
TOOLS_BY_NAME: dict = {t.name: t for t in ALL_TOOLS}


def _load_mcp_tools_safe() -> list:
    try:
        from agent.mcp_tools import get_mcp_tools_sync

        return get_mcp_tools_sync()
    except Exception as exc:
        logger.debug("MCP tools unavailable: %s", exc)
        return []


def _merge_mcp_tools(mcp_tools: list) -> None:
    """Merge MCP tools into the global registry, avoiding name collisions."""
    builtin_names = {t.name for t in _BUILTIN_TOOLS}
    new_tools = [t for t in mcp_tools if t.name not in builtin_names]
    ALL_TOOLS.clear()
    ALL_TOOLS.extend(_BUILTIN_TOOLS)
    ALL_TOOLS.extend(new_tools)
    TOOLS_BY_NAME.clear()
    TOOLS_BY_NAME.update({t.name: t for t in ALL_TOOLS})


def get_all_tools(refresh_mcp: bool = False) -> list:
    """Return the full tool list. Set refresh_mcp=True to reload MCP tools."""
    if refresh_mcp:
        _merge_mcp_tools(_load_mcp_tools_safe())
    return list(ALL_TOOLS)


_initial_mcp = _load_mcp_tools_safe()
if _initial_mcp:
    _merge_mcp_tools(_initial_mcp)
    logger.info("Registered %d MCP tool(s)", len(_initial_mcp))
