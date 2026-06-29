"""JD CRUD API routes: list, create, get, update, status, templates."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_user, get_db, require_role
from backend.config.templates import TEMPLATES
from backend.db.models.jd import JD, EducationLevel, JDStatus

router = APIRouter(prefix="/jd", tags=["jd"])


# ── Pydantic Schemas ────────────────────────────────────────────────────────


class JDSchema(BaseModel):
    """Input schema for creating and updating a JD."""
    title: str
    department: str
    skills: str = ""
    experience_years: int = 0
    education: str = "不限"
    salary_min: int = 0
    salary_max: int = 0
    description: str = ""

    @field_validator("title")
    @classmethod
    def title_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("职位名称不能为空")
        return v.strip()


class JDResponse(BaseModel):
    """Output schema for a single JD."""
    id: int
    title: str
    department: str
    skills: str
    experience_years: int
    education: str
    salary_min: int
    salary_max: int
    description: str
    status: str
    created_at: datetime
    updated_at: datetime


class JDListResponse(BaseModel):
    """Paginated list response."""
    items: list[JDResponse]
    total: int
    page: int
    page_size: int


class StatusUpdate(BaseModel):
    """Request body for status transitions."""
    status: str

    @field_validator("status")
    @classmethod
    def validate_status_value(cls, v: str) -> str:
        valid_values = {s.value for s in JDStatus}
        if v not in valid_values:
            raise ValueError(f"无效的状态值: {v}，有效值：{', '.join(sorted(valid_values))}")
        return v


# ── Helper ──────────────────────────────────────────────────────────────────


def _jd_to_dict(jd: JD) -> dict:
    """Convert JD ORM object to a dict suitable for JDResponse."""
    return {
        "id": jd.id,
        "title": jd.title,
        "department": jd.department,
        "skills": jd.skills,
        "experience_years": jd.experience_years,
        "education": jd.education.value if isinstance(jd.education, EducationLevel) else jd.education,
        "salary_min": jd.salary_min,
        "salary_max": jd.salary_max,
        "description": jd.description,
        "status": jd.status.value if isinstance(jd.status, JDStatus) else jd.status,
        "created_at": jd.created_at.isoformat() if hasattr(jd.created_at, "isoformat") else jd.created_at,
        "updated_at": jd.updated_at.isoformat() if hasattr(jd.updated_at, "isoformat") else jd.updated_at,
    }


# ── Status Transition Map (D-12) ────────────────────────────────────────────

_VALID_TRANSITIONS: dict[JDStatus, list[JDStatus]] = {
    JDStatus.DRAFT: [JDStatus.ACTIVE],
    JDStatus.ACTIVE: [JDStatus.CLOSED],
    JDStatus.CLOSED: [JDStatus.ACTIVE],
}


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.get("/templates")
async def list_templates(
    _user: dict = Depends(get_current_user),
):
    """Return hardcoded 3-5 JD templates (D-09, D-11)."""
    return TEMPLATES


@router.get("")
async def list_jds(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status"),
    keyword: str | None = Query(None, description="Search in title, department, skills"),
    date_from: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List JDs with server-side pagination and filtering (D-07, D-08)."""
    # Build base query
    base_query = select(JD)

    # Apply filters
    if status:
        base_query = base_query.where(JD.status == status)

    if keyword:
        pattern = f"%{keyword}%"
        base_query = base_query.where(
            or_(
                JD.title.ilike(pattern),
                JD.department.ilike(pattern),
                JD.skills.ilike(pattern),
            )
        )

    if date_from:
        base_query = base_query.where(JD.updated_at >= date_from)

    if date_to:
        base_query = base_query.where(JD.updated_at <= f"{date_to} 23:59:59")

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch page
    data_query = (
        base_query.order_by(JD.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    data_result = await db.execute(data_query)
    jds = data_result.scalars().all()

    return JDListResponse(
        items=[JDResponse(**_jd_to_dict(jd)) for jd in jds],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_jd(
    data: JDSchema,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_role("admin", "recruiter")),
):
    """Create a new JD (JD-01, D-14)."""
    jd = JD(
        title=data.title,
        department=data.department,
        skills=data.skills,
        experience_years=data.experience_years,
        education=data.education,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        description=data.description,
    )
    db.add(jd)
    await db.commit()
    await db.refresh(jd)
    return JDResponse(**_jd_to_dict(jd))


@router.get("/{jd_id}")
async def get_jd(
    jd_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get a single JD by ID."""
    result = await db.execute(select(JD).where(JD.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD 不存在",
        )
    return JDResponse(**_jd_to_dict(jd))


@router.put("/{jd_id}")
async def update_jd(
    jd_id: int,
    data: JDSchema,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_role("admin", "recruiter")),
):
    """Update all fields of an existing JD (JD-02, D-14)."""
    result = await db.execute(select(JD).where(JD.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD 不存在",
        )

    jd.title = data.title
    jd.department = data.department
    jd.skills = data.skills
    jd.experience_years = data.experience_years
    jd.education = data.education
    jd.salary_min = data.salary_min
    jd.salary_max = data.salary_max
    jd.description = data.description

    await db.commit()
    await db.refresh(jd)
    return JDResponse(**_jd_to_dict(jd))


@router.delete("/{jd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_jd(
    jd_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_role("admin", "recruiter")),
):
    """Delete an existing JD."""
    result = await db.execute(select(JD).where(JD.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD 不存在",
        )

    await db.delete(jd)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{jd_id}/status")
async def update_jd_status(
    jd_id: int,
    data: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_role("admin", "recruiter")),
):
    """Update JD status with D-12 state machine enforcement."""
    result = await db.execute(select(JD).where(JD.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JD 不存在",
        )

    current_status = jd.status
    new_status = JDStatus(data.status)

    allowed = _VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态转换：不能从「{current_status.value}」到「{new_status.value}」",
        )

    jd.status = new_status
    await db.commit()
    await db.refresh(jd)
    return JDResponse(**_jd_to_dict(jd))
