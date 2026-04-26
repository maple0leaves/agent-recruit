"""FastAPI server exposing the recruitment agent as REST endpoints."""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from config import CORS_ORIGINS
from backend.api.deps import get_current_user, get_db

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent.schemas import CandidateApproval, MatchResult, RecruitmentInput, RecruitmentOutput
from agent.skills import build_skill_context, get_skill_tools, load_all_skills, match_skills
from main import recruitment_graph, recruitment_graph_hitl, run
from backend.db.models.match_session import MatchSession
from backend.db.models.jd import JD
from backend.db.models.candidate import Candidate
from backend.api.routes.auth import router as auth_router
from backend.api.routes.jd import router as jd_router
from backend.api.routes.candidate import router as candidate_router

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="Multi-Agent Recruitment System",
    description="基于 LangChain + LangGraph 的多 Agent 智能招聘系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(jd_router)
app.include_router(candidate_router)


def _parse_match_results(match_results: list) -> list[MatchResult]:
    """Normalize match result payloads into MatchResult models."""
    parsed_results: list[MatchResult] = []
    for item in match_results:
        if isinstance(item, MatchResult):
            parsed_results.append(item)
        elif isinstance(item, dict):
            parsed_results.append(MatchResult(**item))
    return parsed_results


@app.get("/", include_in_schema=False)
async def frontend():
    """Serve the frontend single-page app."""
    return FileResponse(str(STATIC_DIR / "index.html"))


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/recruit", response_model=RecruitmentOutput)
async def recruit(request: RecruitmentInput, _user: dict = Depends(get_current_user)):
    """Run the full recruitment workflow."""
    try:
        result = await asyncio.to_thread(
            run,
            user_input=request.user_input,
            resume_text=request.resume_text or "",
        )
        parsed_results = _parse_match_results(result.get("match_results", []))

        return RecruitmentOutput(
            final_report=result.get("final_report", ""),
            match_results=parsed_results,
            classification=result.get("classification", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class HITLStartRequest(BaseModel):
    user_input: str
    resume_text: Optional[str] = None
    thread_id: Optional[str] = None


class HITLResumeRequest(BaseModel):
    """Request body to resume HITL workflow with per-candidate approvals (D-09)."""
    thread_id: str
    approvals: list[CandidateApproval] = Field(description="逐候选人审核结果列表")


@app.post("/recruit/hitl/start")
async def hitl_start(request: HITLStartRequest, _user: dict = Depends(get_current_user)):
    """Start a HITL recruitment workflow (pauses before reviewer for HR approval)."""
    from uuid import uuid4
    thread_id = request.thread_id if request.thread_id is not None else f"hitl-{uuid4().hex}"
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "user_input": request.user_input,
        "resume_text": request.resume_text,
        "jd_info": None,
        "candidates": [],
        "match_results": [],
        "final_report": "",
        "classification": "",
        "next_action": "",
        "hr_approved": None,
        "hr_feedback": "",
        "messages": [],
    }
    result = await asyncio.to_thread(recruitment_graph_hitl.invoke, initial_state, config=config)
    parsed_results = _parse_match_results(result.get("match_results", []))
    final_report = result.get("final_report", "")
    classification = result.get("classification", "")

    if final_report:
        return {
            "status": "completed",
            "thread_id": thread_id,
            "classification": classification,
            "match_results": parsed_results,
            "final_report": final_report,
            "message": "流程已直接完成，无需 HR 审核。",
        }

    return {
        "status": "waiting_for_hr",
        "thread_id": thread_id,
        "classification": classification,
        "match_results": parsed_results,
        "final_report": "",
        "message": "系统已暂停，等待 HR 审核。请调用 /recruit/hitl/resume 提交审核结果。",
    }


@app.post("/recruit/hitl/resume")
async def hitl_resume(
    request: HITLResumeRequest,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Resume the HITL workflow after HR per-candidate review (APRV-01, D-12).

    Accepts per-candidate approvals list. Builds candidate_decisions dict from
    approvals, passes to graph via invoke. Updates MatchSession record.
    """
    config = {"configurable": {"thread_id": request.thread_id}}

    # Build candidate_decisions from approvals (D-09, D-11)
    candidate_decisions = {a.candidate_name: a.approved for a in request.approvals}
    feedback_payload = [a.model_dump() for a in request.approvals]

    result = await asyncio.to_thread(
        recruitment_graph_hitl.invoke,
        {
            "candidate_decisions": candidate_decisions,
            "hr_feedback": json.dumps(feedback_payload, ensure_ascii=False),
        },
        config=config,
    )

    # Update MatchSession record (D-13)
    try:
        from sqlalchemy import select as sa_select
        match_result = await db.execute(
            sa_select(MatchSession).where(MatchSession.thread_id == request.thread_id)
        )
        match_session = match_result.scalar_one_or_none()
        if match_session:
            approved_count = sum(1 for a in request.approvals if a.approved)
            rejected_count = sum(1 for a in request.approvals if not a.approved)
            match_session.status = "approved" if approved_count > 0 else "rejected"
            match_session.approved_count = approved_count
            match_session.rejected_count = rejected_count
            await db.commit()
    except Exception as exc:
        logger.warning(f"Failed to update MatchSession: {exc}")

    parsed_results = _parse_match_results(result.get("match_results", []))
    return {
        "status": "completed",
        "final_report": result.get("final_report", ""),
        "match_results": parsed_results,
    }


@app.get("/dashboard/stats")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Dashboard stats aggregation (D-13, DASH-01).

    Returns 3 key metrics: active JD count, total candidates, pending approvals.
    Uses SQLAlchemy aggregate queries. No caching -- page-load refresh per D-14.
    """
    from sqlalchemy import func, select as sa_select

    active_jds_result, total_candidates_result, pending_approvals_result = await asyncio.gather(
        db.execute(sa_select(func.count()).select_from(JD).where(JD.status == "active")),
        db.execute(sa_select(func.count()).select_from(Candidate)),
        db.execute(
            sa_select(func.count())
            .select_from(MatchSession)
            .where(MatchSession.status == "pending")
        ),
    )

    return {
        "active_jds": active_jds_result.scalar() or 0,
        "total_candidates": total_candidates_result.scalar() or 0,
        "pending_approvals": pending_approvals_result.scalar() or 0,
    }


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), _user: dict = Depends(get_current_user)):
    """Accept a PDF or plain-text resume file and return its extracted text."""
    filename = (file.filename or "").lower()
    if not (filename.endswith(".pdf") or filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="仅支持 .pdf 或 .txt 格式的简历文件")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="文件内容为空")

    page_count = 1
    if filename.endswith(".pdf"):
        try:
            import io
            import fitz

            doc = fitz.open(stream=io.BytesIO(raw), filetype="pdf")
            page_count = len(doc)
            pages = [page.get_text() for page in doc]
            doc.close()
            text = "\n".join(pages).strip()
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"PDF 解析失败：{e}")
    else:
        try:
            text = raw.decode("utf-8").strip()
        except UnicodeDecodeError:
            text = raw.decode("gbk", errors="replace").strip()

    if not text:
        raise HTTPException(
            status_code=422,
            detail="未能从文件中提取到文字内容（可能是扫描版图片 PDF，暂不支持）",
        )

    return {"text": text, "filename": file.filename, "pages": page_count}


def _sse_event(event: str, data: dict) -> str:
    payload = json.dumps({"event": event, "data": data}, ensure_ascii=False)
    return f"data: {payload}\n\n"


async def _stream_recruitment(user_input: str, resume_text: str, request: Request):
    """Generator that streams LangGraph node events as SSE.

    Includes:
    - 120-second timeout via asyncio.wait_for
    - Client disconnect detection via request.is_disconnected()
    - [DONE] sentinel on all terminal paths
    """
    from uuid import uuid4

    config = {"configurable": {"thread_id": f"stream-{uuid4().hex}"}}
    initial_state = {
        "user_input": user_input,
        "resume_text": resume_text or None,
        "jd_info": None,
        "candidates": [],
        "match_results": [],
        "final_report": "",
        "classification": "",
        "next_action": "",
        "hr_approved": None,
        "hr_feedback": "",
        "messages": [],
    }

    all_skills = load_all_skills()
    matched = match_skills(user_input, all_skills)
    if matched:
        skill_ctx = build_skill_context(matched)
        tool_names = get_skill_tools(matched)
        yield _sse_event(
            "progress",
            {
                "message": f"已激活技能: {', '.join(s.name for s in matched)}",
                "skill_tools": tool_names,
                "skill_context_preview": skill_ctx[:200],
            },
        )

    TIMEOUT_SECONDS = 120

    try:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _run_graph():
            try:
                for chunk in recruitment_graph.stream(initial_state, config=config):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            loop.call_soon_threadsafe(queue.put_nowait, None)

        # Run with timeout
        stream_task = asyncio.create_task(
            asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _run_graph),
                timeout=TIMEOUT_SECONDS,
            )
        )

        progress_map = {
            "triage_router": "请求分类完成",
            "planner_agent": "任务规划完成",
            "worker_agent": "工具执行完成",
            "reviewer_agent": "审核报告生成完成",
            "single_resume_agent": "简历解析评估完成",
        }

        final_state: dict = {}

        while True:
            done, pending = await asyncio.wait(
                [stream_task, asyncio.ensure_future(queue.get())],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Check for client disconnect
            if await request.is_disconnected():
                stream_task.cancel()
                yield _sse_event("done", {})
                return

            # Check for timeout
            if stream_task in done and stream_task.exception() is not None:
                exc = stream_task.exception()
                if isinstance(exc, asyncio.TimeoutError):
                    yield _sse_event("error", {"message": "请求超时，请稍后重试"})
                    yield _sse_event("done", {})
                    return
                raise exc

            if stream_task.done():
                # Stream completed normally
                break

            # Process queue items
            item = queue.get_nowait() if not stream_task.done() else None
            if item is None:
                break
            if isinstance(item, Exception):
                raise item

            for node_name, node_output in item.items():
                yield _sse_event("status", {"node": node_name, "status": "completed"})

                if isinstance(node_output, dict) and node_output.get("messages"):
                    for msg in node_output["messages"]:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                yield _sse_event(
                                    "tool_call",
                                    {
                                        "tool": tc["name"],
                                        "args": tc.get("args", {}),
                                    },
                                )

                if node_name in progress_map:
                    yield _sse_event("progress", {"message": progress_map[node_name]})

                if isinstance(node_output, dict):
                    final_state.update(node_output)

        # Send final result
        parsed_results = _parse_match_results(final_state.get("match_results", []))
        yield _sse_event(
            "result",
            {
                "final_report": final_state.get("final_report", ""),
                "match_results": [r.model_dump() for r in parsed_results],
                "classification": final_state.get("classification", ""),
            },
        )

    except asyncio.TimeoutError:
        yield _sse_event("error", {"message": "请求超时，请稍后重试"})
    except Exception as e:
        logger.exception("Streaming recruitment failed")
        yield _sse_event("error", {"message": str(e)})
    finally:
        yield _sse_event("done", {})


class HITLStreamRequest(BaseModel):
    """Request body for streaming HITL matching (D-01, D-04)."""
    jd_id: int = Field(description="Job Description ID to match candidates against")


class HITLReverseRequest(BaseModel):
    """Request body for reverse matching (MATCH-04, D-02)."""
    candidate_id: int = Field(description="Candidate ID to find matching JDs for")


async def _stream_hitl_recruitment(user_input: str, jd_id: int, request: Request, db: AsyncSession):
    """Generator that streams LangGraph HITL events as SSE.

    Uses recruitment_graph_hitl (with interrupt_before=["reviewer_agent"]) so the
    graph streams progress until the reviewer interrupt, then sends hitl_pause.
    """
    from uuid import uuid4

    thread_id = f"hitl-stream-{uuid4().hex}"
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "user_input": user_input,
        "resume_text": None,
        "jd_info": None,
        "candidates": [],
        "match_results": [],
        "final_report": "",
        "classification": "",
        "next_action": "",
        "hr_approved": None,
        "hr_feedback": "",
        "candidate_decisions": {},
        "messages": [],
    }

    TIMEOUT_SECONDS = 120

    try:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _run_hitl_graph():
            try:
                for chunk in recruitment_graph_hitl.stream(initial_state, config=config):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            except Exception as exc:
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            loop.call_soon_threadsafe(queue.put_nowait, None)

        stream_task = asyncio.create_task(
            asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _run_hitl_graph),
                timeout=TIMEOUT_SECONDS,
            )
        )

        progress_map = {
            "triage_router": "正在分析需求...",
            "planner_agent": "正在规划搜索策略...",
            "worker_agent": "正在搜索并评分候选人...",
            "reviewer_agent": "正在生成审核报告...",
        }

        final_state: dict = {}
        match_results_sent: set[str] = set()

        while True:
            done, pending = await asyncio.wait(
                [stream_task, asyncio.ensure_future(queue.get())],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if await request.is_disconnected():
                stream_task.cancel()
                yield _sse_event("done", {})
                return

            if stream_task in done and stream_task.exception() is not None:
                exc = stream_task.exception()
                if isinstance(exc, asyncio.TimeoutError):
                    yield _sse_event("error", {"message": "请求超时，请稍后重试"})
                    yield _sse_event("done", {})
                    return
                raise exc

            if stream_task.done():
                break

            item = queue.get_nowait() if not stream_task.done() else None
            if item is None:
                break
            if isinstance(item, Exception):
                raise item

            for node_name, node_output in item.items():
                yield _sse_event("status", {"node": node_name, "status": "completed"})

                if isinstance(node_output, dict) and node_output.get("messages"):
                    for msg in node_output["messages"]:
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                yield _sse_event(
                                    "tool_call",
                                    {
                                        "tool": tc["name"],
                                        "args": tc.get("args", {}),
                                    },
                                )

                if node_name in progress_map:
                    yield _sse_event("progress", {"message": progress_map[node_name]})

                if isinstance(node_output, dict):
                    final_state.update(node_output)

                # Progressive match_result emission (D-07)
                if isinstance(node_output, dict) and node_output.get("match_results"):
                    for result in node_output["match_results"]:
                        candidate_name = result.get("candidate_name", "") if isinstance(result, dict) else getattr(result, "candidate_name", "")
                        if candidate_name and candidate_name not in match_results_sent:
                            match_results_sent.add(candidate_name)
                            if isinstance(result, dict):
                                yield _sse_event("match_result", result)
                            else:
                                yield _sse_event("match_result", result.model_dump())

        # Stream ended (hit interrupt_before=["reviewer_agent"])
        parsed_results = _parse_match_results(final_state.get("match_results", []))

        # Create MatchSession record for dashboard tracking (D-13)
        match_session = None
        if parsed_results:
            try:
                match_session = MatchSession(
                    jd_id=jd_id,
                    thread_id=thread_id,
                    status="pending",
                    total_candidates=len(parsed_results),
                )
                db.add(match_session)
                await db.commit()
                await db.refresh(match_session)  # IMPORT: get session.id for hitl_pause
            except Exception as exc:
                logger.warning(f"Failed to create MatchSession: {exc}")

        yield _sse_event("hitl_pause", {
            "match_results": [r.model_dump() for r in parsed_results],
            "thread_id": thread_id,
            "session_id": match_session.id if match_session else None,
        })

    except asyncio.TimeoutError:
        yield _sse_event("error", {"message": "请求超时，请稍后重试"})
    except Exception as e:
        logger.exception("Streaming HITL recruitment failed")
        yield _sse_event("error", {"message": str(e)})
    finally:
        yield _sse_event("done", {})


async def _stream_reverse_matching(candidate_id: int, request: Request, db: AsyncSession):
    """Generator that scores active JDs against the given candidate's skills.

    Simpler than _stream_hitl_recruitment -- does NOT run the LangGraph agent.
    Instead, computes skill-overlap scores for each active JD.
    (MATCH-04, D-02)
    """
    from uuid import uuid4

    thread_id = f"reverse-{uuid4().hex}"

    # Fetch candidate
    from sqlalchemy import select as sa_select
    result = await db.execute(
        sa_select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        yield _sse_event("error", {"message": "候选人不存在"})
        yield _sse_event("done", {})
        return

    # Parse candidate skills
    candidate_skills = _parse_skills(candidate.skills)

    # Fetch all active JDs
    jd_result = await db.execute(
        sa_select(JD).where(JD.status == "active")
    )
    active_jds = jd_result.scalars().all()

    if not active_jds:
        yield _sse_event("error", {"message": "暂无活跃职位"})
        yield _sse_event("done", {})
        return

    TIMEOUT_SECONDS = 120

    try:
        # Compute scores for each JD
        scored_results = []
        for jd in active_jds:
            jd_skills = _parse_skills(jd.skills)
            intersection = set(candidate_skills) & set(jd_skills)
            union = set(candidate_skills) | set(jd_skills)
            score = int(len(intersection) / len(union) * 100) if union else 0
            matched_skills = list(intersection)
            missing_skills = [s for s in jd_skills if s not in candidate_skills]

            result_item = MatchResult(
                candidate_name=jd.title,
                match_score=score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                recommendation="反向匹配",
                should_proceed=False,
            )
            scored_results.append(result_item)

            # Yield match_result event for each
            yield _sse_event("match_result", result_item.model_dump())

        # Sort for the hitl_pause event
        scored_results.sort(key=lambda r: r.match_score, reverse=True)

        # Create MatchSession with candidate_id
        match_session = None
        if scored_results:
            try:
                import json as _json
                match_session = MatchSession(
                    jd_id=None,
                    candidate_id=candidate_id,
                    thread_id=thread_id,
                    status="pending",
                    total_candidates=len(scored_results),
                    results_json=_json.dumps(
                        [r.model_dump() for r in scored_results],
                        ensure_ascii=False,
                    ),
                )
                db.add(match_session)
                await db.commit()
                await db.refresh(match_session)
            except Exception as exc:
                logger.warning(f"Failed to create MatchSession: {exc}")

        yield _sse_event("hitl_pause", {
            "match_results": [r.model_dump() for r in scored_results],
            "thread_id": thread_id,
            "session_id": match_session.id if match_session else None,
        })

    except Exception as e:
        logger.exception("Streaming reverse matching failed")
        yield _sse_event("error", {"message": str(e)})
    finally:
        yield _sse_event("done", {})


def _parse_skills(skills_str: str) -> list[str]:
    """Parse a skills string into a list of skill names."""
    if not skills_str:
        return []
    # Try comma-separated, then fall back to whitespace-split
    parts = [s.strip() for s in skills_str.split(",")]
    if len(parts) > 1:
        return [p for p in parts if p]
    return [p for p in skills_str.split() if p]


@app.post("/recruit/stream")
async def recruit_stream(
    request: RecruitmentInput,
    http_request: Request,
    _user: dict = Depends(get_current_user),
):
    """SSE streaming endpoint for the recruitment workflow."""
    return StreamingResponse(
        _stream_recruitment(request.user_input, request.resume_text or "", http_request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/recruit/hitl/stream")
async def hitl_stream(
    request: HITLStreamRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """SSE streaming endpoint for HITL matching (D-01, D-04).

    Accepts jd_id, fetches the JD, constructs user_input, and starts
    the HITL LangGraph streaming. Returns SSE events for pipeline progress,
    tool calls, candidate results, and final hitl_pause.
    """
    from backend.db.models.jd import JD
    from sqlalchemy import select

    result = await db.execute(select(JD).where(JD.id == request.jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="JD 不存在")

    # Construct user_input from JD fields for the agent
    user_input = (
        f"招聘{jd.title}，"
        f"部门：{jd.department}，"
        f"要求技能：{jd.skills}，"
        f"{jd.experience_years}年经验，"
        f"学历要求：{jd.education}，"
        f"薪资范围：{jd.salary_min}-{jd.salary_max}。"
        f"{jd.description}"
    )

    return StreamingResponse(
        _stream_hitl_recruitment(user_input, request.jd_id, http_request, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/recruit/hitl/reverse-stream")
async def hitl_reverse_stream(
    request: HITLReverseRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """SSE streaming endpoint for reverse matching (MATCH-04, D-02).

    Accepts candidate_id, fetches the candidate and all active JDs,
    computes skill-overlap scores, and streams results as SSE events.
    """
    return StreamingResponse(
        _stream_reverse_matching(request.candidate_id, http_request, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/skills")
async def list_skills(_user: dict = Depends(get_current_user)):
    """List all available skills with name, description, tools, and trigger."""
    skills = load_all_skills()
    return [
        {
            "name": s.name,
            "description": s.description,
            "tools": s.tools,
            "trigger": s.trigger,
        }
        for s in skills
    ]


@app.post("/admin/rebuild-index")
async def rebuild_index(_user: dict = Depends(get_current_user)):
    """Rebuild the resume vector store index from the data/resumes directory."""
    from config import RESUME_DIR, VECTOR_STORE_PATH
    from rag.vector_store import build_vector_store

    try:
        await asyncio.to_thread(build_vector_store, RESUME_DIR, VECTOR_STORE_PATH)
        from rag.retriever import invalidate_vector_store_cache

        invalidate_vector_store_cache()
        return {"status": "ok", "message": "向量索引已重建，检索缓存已刷新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    from config import API_HOST, API_PORT

    uvicorn.run("api.server:app", host=API_HOST, port=API_PORT, reload=True)
