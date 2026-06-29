"""Candidate API routes: upload, list, get, update, and status changes."""
import asyncio
import io
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.schemas import CandidateInfo
from agent.tools import analyze_resume
from backend.api.deps import get_current_user, get_db, require_role
from backend.db.engine import async_session
from backend.db.models.candidate import Candidate, CandidateStatus
from config import RESUME_DIR

router = APIRouter(prefix="/candidates", tags=["candidates"])
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class CandidateResponse(BaseModel):
    """Output schema for a single candidate."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str
    skills: str
    education: str
    experience: str
    status: str
    resume_file_path: str
    status_note: str
    parse_status: str
    parsed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CandidateListResponse(BaseModel):
    """Paginated list response."""
    items: list[CandidateResponse]
    total: int
    page: int
    page_size: int


class CandidateUploadFailure(BaseModel):
    """Per-file failure returned by the batch upload endpoint."""
    filename: str
    error: str


class CandidateBatchUploadResponse(BaseModel):
    """Batch upload response with per-file success and failure details."""
    items: list[dict]
    failures: list[CandidateUploadFailure]
    success_count: int
    failure_count: int
    total_count: int


class CandidateUpdate(BaseModel):
    """Editable candidate fields."""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: str | None = None
    education: str | None = None
    experience: str | None = None


class StatusUpdate(BaseModel):
    """Request body for pipeline status transitions."""
    status: str
    status_note: str

    @field_validator("status")
    @classmethod
    def validate_status_value(cls, v: str) -> str:
        valid_values = {s.value for s in CandidateStatus}
        if v not in valid_values:
            raise ValueError(
                f"Invalid status: {v}. Valid values: {', '.join(sorted(valid_values))}"
            )
        return v

    @field_validator("status_note")
    @classmethod
    def note_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Status note is required")
        return v.strip()


_VALID_TRANSITIONS: dict[CandidateStatus, list[CandidateStatus]] = {
    CandidateStatus.NEW: [CandidateStatus.SCREENING, CandidateStatus.REJECTED],
    CandidateStatus.SCREENING: [CandidateStatus.INTERVIEW, CandidateStatus.REJECTED],
    CandidateStatus.INTERVIEW: [CandidateStatus.HIRED, CandidateStatus.REJECTED],
    CandidateStatus.HIRED: [],
    CandidateStatus.REJECTED: [],
}


def _clip(value: str, max_length: int) -> str:
    return value[:max_length] if value else ""


def _clip_note(value: str) -> str:
    return _clip(value, 1000)


def _initial_candidate_name(filename: str) -> str:
    stem = Path(filename).stem.strip()
    return _clip(stem or "解析中候选人", 200)


def _extract_text(raw_bytes: bytes, ext: str) -> str:
    """Extract plain text from PDF or DOCX bytes."""
    if ext == ".pdf":
        import fitz

        doc = fitz.open(stream=io.BytesIO(raw_bytes), filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
    elif ext == ".docx":
        from docx import Document

        doc = Document(io.BytesIO(raw_bytes))
        text = "\n".join(p.text for p in doc.paragraphs)
    else:
        text = ""
    return text.strip()


def _candidate_to_dict(
    candidate: Candidate,
    filename: str | None = None,
    warnings: list[str] | None = None,
) -> dict:
    result = CandidateResponse.model_validate(candidate).model_dump()
    if filename:
        result["filename"] = filename
    if warnings:
        result["warnings"] = warnings
    return result


def _resume_path_for_delete(resume_file_path: str) -> Path | None:
    """Resolve a stored resume path to a file under RESUME_DIR."""
    if not resume_file_path:
        return None

    filename = Path(resume_file_path).name
    if not filename:
        return None

    resume_dir = Path(RESUME_DIR).resolve()
    candidate_path = (resume_dir / filename).resolve()
    try:
        candidate_path.relative_to(resume_dir)
    except ValueError:
        return None
    return candidate_path


async def _mark_parse_failed(candidate_id: int, message: str) -> None:
    async with async_session() as db:
        candidate = await db.get(Candidate, candidate_id)
        if not candidate:
            return
        candidate.status_note = _clip_note(message)
        await db.commit()


async def _apply_parse_result(candidate_id: int, parsed: CandidateInfo) -> None:
    async with async_session() as db:
        candidate = await db.get(Candidate, candidate_id)
        if not candidate:
            return

        candidate.name = _clip(parsed.name, 200) or candidate.name
        candidate.email = _clip(parsed.email, 200)
        candidate.skills = _clip(", ".join(parsed.skills), 2000) if parsed.skills else ""
        candidate.education = _clip(parsed.education, 500)
        candidate.experience = parsed.summary or ""
        candidate.parsed_at = datetime.utcnow()
        candidate.status_note = "简历解析完成"
        await db.commit()


async def _parse_candidate_resume_background(
    candidate_id: int,
    absolute_path: str,
    ext: str,
) -> None:
    """Run the expensive AI parsing after the upload response has returned."""
    try:
        raw = await asyncio.to_thread(Path(absolute_path).read_bytes)
        text = await asyncio.to_thread(_extract_text, raw, ext)
        if not text:
            await _mark_parse_failed(
                candidate_id,
                "后台解析未提取到文本，可能是扫描版 PDF 或文件内容为空",
            )
            return

        def _parse() -> str:
            return analyze_resume.invoke({"resume_text": text})

        candidate_json = await asyncio.to_thread(_parse)
        parsed = CandidateInfo.model_validate_json(candidate_json)
        await _apply_parse_result(candidate_id, parsed)
    except Exception as exc:
        logger.exception("Background resume parsing failed for candidate %s", candidate_id)
        await _mark_parse_failed(candidate_id, f"后台解析失败: {exc}")


async def _create_candidate_from_upload(
    file: UploadFile,
    db: AsyncSession,
    background_tasks: BackgroundTasks,
) -> dict:
    """Validate and persist one resume, then enqueue AI parsing in the background."""
    filename = file.filename or "resume.pdf"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        if ext == ".doc":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported format. Please save .doc as .docx and upload again.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF and Word (.docx) files are supported, not {ext}.",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size cannot exceed 10MB",
        )

    safe_filename = f"{uuid.uuid4().hex}{ext}"
    relative_path = os.path.join("data/resumes", safe_filename)
    absolute_path = os.path.join(RESUME_DIR, safe_filename)
    os.makedirs(RESUME_DIR, exist_ok=True)
    with open(absolute_path, "wb") as f:
        f.write(raw)

    candidate = Candidate(
        name=_initial_candidate_name(filename),
        email="",
        phone="",
        skills="",
        education="",
        experience="",
        status=CandidateStatus.NEW,
        resume_file_path=relative_path,
        status_note="简历已上传，正在后台解析",
        parsed_at=None,
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)

    background_tasks.add_task(
        _parse_candidate_resume_background,
        candidate.id,
        absolute_path,
        ext,
    )
    return _candidate_to_dict(candidate, filename=filename)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_candidate(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_role("admin", "recruiter")),
):
    """Upload one resume, create a candidate immediately, and parse asynchronously."""
    return await _create_candidate_from_upload(file, db, background_tasks)


@router.post("/upload/batch", status_code=status.HTTP_201_CREATED)
async def upload_candidates_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_role("admin", "recruiter")),
):
    """Upload multiple resumes and enqueue background parsing per accepted file."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please select at least one resume file",
        )

    items: list[dict] = []
    failures: list[CandidateUploadFailure] = []

    for file in files:
        filename = file.filename or "unnamed file"
        try:
            items.append(
                await _create_candidate_from_upload(file, db, background_tasks)
            )
        except HTTPException as exc:
            await db.rollback()
            failures.append(
                CandidateUploadFailure(filename=filename, error=str(exc.detail))
            )
        except Exception as exc:
            await db.rollback()
            failures.append(
                CandidateUploadFailure(filename=filename, error=f"Upload failed: {exc}")
            )

    return CandidateBatchUploadResponse(
        items=items,
        failures=failures,
        success_count=len(items),
        failure_count=len(failures),
        total_count=len(files),
    )


@router.get("")
async def list_candidates(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by pipeline status"
    ),
    keyword: str | None = Query(None, description="Search in name, skills"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List candidates with pagination and search/filter."""
    base_query = select(Candidate)

    if status_filter:
        base_query = base_query.where(Candidate.status == status_filter)
    if keyword:
        pattern = f"%{keyword}%"
        base_query = base_query.where(
            or_(
                Candidate.name.ilike(pattern),
                Candidate.skills.ilike(pattern),
            )
        )

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    data_query = (
        base_query.order_by(Candidate.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(data_query)).scalars().all()

    return CandidateListResponse(
        items=[CandidateResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get single candidate detail."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate does not exist",
        )
    return CandidateResponse.model_validate(candidate)


@router.put("/{candidate_id}")
async def update_candidate(
    candidate_id: int,
    data: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Update candidate writable fields."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate does not exist",
        )

    update_data = data.model_dump(exclude_none=True)
    for field_name, value in update_data.items():
        setattr(candidate, field_name, value)

    await db.commit()
    await db.refresh(candidate)
    return CandidateResponse.model_validate(candidate)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_role("admin", "recruiter")),
):
    """Delete a candidate and its uploaded resume file."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate does not exist",
        )

    resume_path = _resume_path_for_delete(candidate.resume_file_path)
    await db.delete(candidate)
    await db.commit()

    if resume_path and resume_path.exists():
        try:
            resume_path.unlink()
        except OSError:
            logger.warning("Failed to delete resume file %s", resume_path, exc_info=True)


@router.patch("/{candidate_id}/status")
async def update_candidate_status(
    candidate_id: int,
    data: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_role("admin", "recruiter")),
):
    """Update pipeline status with transition validation."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate does not exist",
        )

    current_status: CandidateStatus = candidate.status
    target_status = CandidateStatus(data.status)

    allowed = _VALID_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid status transition: cannot change "
                f"{current_status.value} to {target_status.value}"
            ),
        )

    candidate.status = target_status
    candidate.status_note = data.status_note
    await db.commit()
    await db.refresh(candidate)
    return CandidateResponse.model_validate(candidate)
