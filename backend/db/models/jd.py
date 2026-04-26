"""JD ORM model with EducationLevel and JDStatus enums."""
import enum
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, func
from backend.db.engine import Base


class EducationLevel(str, enum.Enum):
    HIGH_SCHOOL = "高中"
    ASSOCIATE = "大专"
    BACHELOR = "本科"
    MASTER = "硕士"
    PHD = "博士"
    ANY = "不限"


class JDStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class JD(Base):
    """Job Description model — core entity for Phase 2 JD management."""

    __tablename__ = "jds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    department = Column(String(100), nullable=False)
    skills = Column(String(1000), nullable=False)
    experience_years = Column(Integer, nullable=False, default=0)
    education = Column(Enum(EducationLevel), nullable=False, default=EducationLevel.ANY)
    salary_min = Column(Integer, nullable=False)
    salary_max = Column(Integer, nullable=False)
    description = Column(Text, nullable=False, default="")
    status = Column(Enum(JDStatus), nullable=False, default=JDStatus.DRAFT, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
