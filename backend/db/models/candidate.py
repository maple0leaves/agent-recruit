"""Candidate ORM model and CandidateStatus pipeline enum."""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, func
from backend.db.engine import Base


class CandidateStatus(str, enum.Enum):
    """Pipeline status enum (D-08): new -> screening -> interview -> hired | rejected."""
    NEW = "new"
    SCREENING = "screening"
    INTERVIEW = "interview"
    HIRED = "hired"
    REJECTED = "rejected"


class Candidate(Base):
    """Candidate model -- core entity for Phase 3 resume management (D-06)."""

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(200), nullable=False, default="")
    phone = Column(String(50), nullable=False, default="")
    skills = Column(String(2000), nullable=False, default="")
    education = Column(String(500), nullable=False, default="")
    experience = Column(Text, nullable=False, default="")
    status = Column(Enum(CandidateStatus), nullable=False, default=CandidateStatus.NEW, index=True)
    resume_file_path = Column(String(500), nullable=False, default="")
    status_note = Column(String(1000), nullable=False, default="")
    parsed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
