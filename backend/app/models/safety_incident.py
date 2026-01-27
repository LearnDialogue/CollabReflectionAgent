"""
SafetyIncident model - tracks safety-related incidents detected in messages.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SafetyIncident(Base):
    """
    SafetyIncident model tracking safety concerns detected in messages.
    Used for monitoring and admin notification.
    """
    __tablename__ = "safety_incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    category = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    notified = Column(Boolean, nullable=False, default=False)
    notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="safety_incidents")
    session = relationship("Session", back_populates="safety_incidents")
    message = relationship("Message", back_populates="safety_incidents")

    def __repr__(self):
        return f"<SafetyIncident(id={self.id}, category={self.category}, severity={self.severity})>"
