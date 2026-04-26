"""User ORM model and role enum."""
import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, func
from backend.db.engine import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring-manager"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.RECRUITER)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
