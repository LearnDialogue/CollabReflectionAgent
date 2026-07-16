"""
Student model - represents users of the system.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserRole(str, PyEnum):
    """User roles in the system."""
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class Student(Base):
    """
    Student model representing users who participate in reflection sessions.
    Also used for admin accounts.
    """
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    display_name = Column(String(255), nullable=True)
    pronouns = Column(String(50), nullable=True)
    tone_pref = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    sessions = relationship("Session", back_populates="student", cascade="all, delete-orphan")
    safety_incidents = relationship("SafetyIncident", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student(id={self.id}, username={self.username}, role={self.role})>"
