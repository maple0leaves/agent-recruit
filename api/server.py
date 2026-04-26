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
from pydantic import BaseModel
from config import CORS_ORIGINS
from backend.api.deps import get_current_user

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent.schemas import MatchResult, RecruitmentInput, RecruitmentOutput
from agent.skills import build_skill_context, get_skill_tools, load_all_skills, match_skills
from main import recruitment_graph, recruitment_graph_hitl, run
from backend.api.routes.auth import router as auth_router

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
    thread_id: str
    hr_approved: bool
    hr_feedback: str = ""


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
async def hitl_resume(request: HITLResumeRequest, _user: dict = Depends(get_current_user)):
    """Resume the HITL workflow after HR review."""
    config = {"configurable": {"thread_id": request.thread_id}}
    result = await asyncio.to_thread(
        recruitment_graph_hitl.invoke,
        {
            "hr_approved": request.hr_approved,
            "hr_feedback": request.hr_feedback,
        },
        config=config,
    )
    parsed_results = _parse_match_results(result.get("match_results", []))

    return {
        "status": "completed",
        "final_report": result.get("final_report", ""),
        "match_results": parsed_results,
        "hr_approved": request.hr_approved,
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
