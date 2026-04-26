"""MatchSession ORM model for tracking matching sessions and pending approvals."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from backend.db.engine import Base


class MatchSession(Base):
    """Track matching sessions for dashboard stats (D-13) and pending approvals tracking."""

    __tablename__ = "match_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jd_id = Column(Integer, nullable=True, index=True)
    candidate_id = Column(Integer, nullable=True, index=True)
    thread_id = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    total_candidates = Column(Integer, nullable=False, default=0)
    approved_count = Column(Integer, nullable=False, default=0)
    rejected_count = Column(Integer, nullable=False, default=0)
    results_json = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
