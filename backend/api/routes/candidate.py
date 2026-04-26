"""Candidate API routes: upload, list, get, update, status (RES-01 through RES-05)."""
import asyncio
import io
import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db
from backend.db.models.candidate import Candidate, CandidateStatus
from config import RESUME_DIR
from agent.tools import analyze_resume
from agent.schemas import CandidateInfo

router = APIRouter(prefix="/candidates", tags=["candidates"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB (D-02)
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


# ── Pydantic Schemas ──────────────────────────────────────────────────────────


class CandidateResponse(BaseModel):
    """Output schema for a single candidate (D-06)."""
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
    parsed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CandidateListResponse(BaseModel):
    """Paginated list response (RES-04)."""
    items: list[CandidateResponse]
    total: int
    page: int
    page_size: int


class CandidateUpdate(BaseModel):
    """Editable candidate fields (D-04)."""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: str | None = None
    education: str | None = None
    experience: str | None = None


class StatusUpdate(BaseModel):
    """Request body for pipeline status transitions (RES-05, D-09, D-14~D-16)."""
    status: str
    status_note: str

    @field_validator("status")
    @classmethod
    def validate_status_value(cls, v: str) -> str:
        valid_values = {s.value for s in CandidateStatus}
        if v not in valid_values:
            raise ValueError(
                f"无效的状态值: {v}，有效值：{', '.join(sorted(valid_values))}"
            )
        return v

    @field_validator("status_note")
    @classmethod
    def note_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("状态变更时备注为必填项")
        return v.strip()


# ── State Machine (D-14, D-15) ────────────────────────────────────────────────

_VALID_TRANSITIONS: dict[CandidateStatus, list[CandidateStatus]] = {
    CandidateStatus.NEW: [CandidateStatus.SCREENING, CandidateStatus.REJECTED],
    CandidateStatus.SCREENING: [CandidateStatus.INTERVIEW, CandidateStatus.REJECTED],
    CandidateStatus.INTERVIEW: [CandidateStatus.HIRED, CandidateStatus.REJECTED],
    CandidateStatus.HIRED: [],       # terminal (D-15)
    CandidateStatus.REJECTED: [],    # terminal (D-15)
}


# ── Text Extraction Helper ────────────────────────────────────────────────────


def _extract_text(raw_bytes: bytes, ext: str) -> str:
    """Extract plain text from PDF (fitz) or DOCX (python-docx) file bytes."""
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


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_candidate(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Upload resume, save to disk, extract text, parse via Agent, create candidate (RES-01, RES-02)."""
    # ── 1. Validate file extension ────────────────────────────────────────
    filename = file.filename or "resume.pdf"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        if ext == ".doc":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的格式。请将 .doc 文件另存为 .docx 格式后重新上传。",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"仅支持 PDF 和 Word (.docx) 格式，不支持 {ext} 文件。",
        )

    # ── 2. Read and validate file size ────────────────────────────────────
    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件内容为空",
        )
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过 10MB",
        )

    # ── 3. Save file to disk (D-07) ───────────────────────────────────────
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    relative_path = os.path.join("data/resumes", safe_filename)
    absolute_path = os.path.join(RESUME_DIR, safe_filename)
    os.makedirs(RESUME_DIR, exist_ok=True)
    with open(absolute_path, "wb") as f:
        f.write(raw)

    # ── 4. Extract text from file ─────────────────────────────────────────
    text = _extract_text(raw, ext)
    warnings: list[str] = []

    # ── 5. Parse via Agent (D-01, D-03) ───────────────────────────────────
    parsed = CandidateInfo()  # empty fallback (D-05)

    if text:
        try:
            def _parse():
                return analyze_resume.invoke({"resume_text": text})
            candidate_json = await asyncio.to_thread(_parse)
            parsed = CandidateInfo.model_validate_json(candidate_json)
        except Exception as e:
            warnings.append(f"简历解析未完全成功: {str(e)}")
            # D-05: partial success, continue with empty CandidateInfo
    else:
        warnings.append("未能从文件中提取到文字内容（可能是扫描版图片 PDF），请手动填写候选人信息")

    # ── 6. Create Candidate record (D-06) ─────────────────────────────────
    candidate = Candidate(
        name=parsed.name or "",
        email=parsed.email or "",
        phone="",
        skills=", ".join(parsed.skills) if parsed.skills else "",
        education=parsed.education or "",
        experience=parsed.summary or "",
        status=CandidateStatus.NEW,
        resume_file_path=relative_path,
        status_note="",
        parsed_at=datetime.now(timezone.utc) if parsed.name else None,
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)

    # ── 7. Build response ─────────────────────────────────────────────────
    result = CandidateResponse.model_validate(candidate).model_dump()
    if warnings:
        result["warnings"] = warnings
    return result


@router.get("")
async def list_candidates(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: str | None = Query(None, alias="status", description="Filter by pipeline status"),
    keyword: str | None = Query(None, description="Search in name, skills"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List candidates with pagination and search/filter (RES-04, D-11)."""
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

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # Fetch page
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
    """Get single candidate detail (RES-03)."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="候选人不存在",
        )
    return CandidateResponse.model_validate(candidate)


@router.put("/{candidate_id}")
async def update_candidate(
    candidate_id: int,
    data: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Update candidate writable fields (RES-03, D-04)."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="候选人不存在",
        )

    # Only update fields that were explicitly provided
    update_data = data.model_dump(exclude_none=True)
    for field_name, value in update_data.items():
        setattr(candidate, field_name, value)

    await db.commit()
    await db.refresh(candidate)
    return CandidateResponse.model_validate(candidate)


@router.patch("/{candidate_id}/status")
async def update_candidate_status(
    candidate_id: int,
    data: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Update pipeline status with transition validation (RES-05, D-14~D-17)."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="候选人不存在",
        )

    current_status: CandidateStatus = candidate.status
    target_status = CandidateStatus(data.status)

    # Validate transition
    allowed = _VALID_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态变更：无法从 {current_status.value} 变更为 {target_status.value}",
        )

    # Apply transition (status_note already validated by Pydantic)
    candidate.status = target_status
    candidate.status_note = data.status_note  # stripped value from validator
    await db.commit()
    await db.refresh(candidate)
    return CandidateResponse.model_validate(candidate)
