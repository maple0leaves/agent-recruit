"""Tool definitions for the recruitment agent system."""

import json
import logging
import re
from pathlib import Path

from langchain_core.tools import tool

from agent.schemas import CandidateInfo, MatchResult


def _read_resume_file(file_path: str) -> str:
    """Read resume content from a .txt or .pdf file."""
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        import fitz

        doc = fitz.open(str(path))
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(pages)
    return path.read_text(encoding="utf-8")


@tool
def search_candidates(query: str, top_k: int = 5) -> str:
    """Search candidate resumes from the vector store using semantic similarity.

    Args:
        query: Search query, e.g. "Python engineer 3 years experience"
        top_k: Number of candidates to return

    Returns:
        JSON string of matched candidate summaries
    """
    from rag.retriever import get_retriever

    retriever = get_retriever(top_k=top_k)
    docs = retriever.invoke(query)
    results = []
    seen_sources: set[str] = set()

    for doc in docs:
        source = doc.metadata.get("source", "")
        if source and source in seen_sources:
            continue
        if source:
            seen_sources.add(source)

        resume_text = doc.page_content
        if source and Path(source).exists():
            resume_text = _read_resume_file(source)

        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume_text)
        results.append(
            {
                "name": doc.metadata.get("name", "Unknown"),
                "email": email_match.group(0) if email_match else doc.metadata.get("email", ""),
                "content": resume_text[:500],
                "resume_text": resume_text,
                "source": source,
            }
        )
    return json.dumps(results, ensure_ascii=False)


@tool
def analyze_resume(resume_text: str) -> str:
    """Parse and extract structured information from a resume text."""
    from agent.prompt import RESUME_PARSE_PROMPT
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from agent.agent import _build_llm

    llm = _build_llm()
    llm_structured = llm.with_structured_output(CandidateInfo)
    result = llm_structured.invoke(RESUME_PARSE_PROMPT.format(resume_text=resume_text))
    return result.model_dump_json(ensure_ascii=False)


@tool
def score_match(candidate_json: str, jd_json: str) -> str:
    """Evaluate the match between a candidate and a job description."""
    from agent.prompt import MATCH_SCORING_PROMPT
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from agent.agent import _build_llm

    llm = _build_llm()
    llm_structured = llm.with_structured_output(MatchResult)
    result = llm_structured.invoke(
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
