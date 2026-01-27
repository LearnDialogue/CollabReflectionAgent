"""
SessionSummary model - stores structured summaries of completed sessions.
"""

from datetime import datetime

from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class SessionSummary(Base):
    """
    SessionSummary model storing structured extraction from a session.
    Created/updated as the session progresses through stages.
    """
    __tablename__ = "session_summaries"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), primary_key=True)
    event_summary = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)
    strategies = Column(Text, nullable=True)
    next_goal = Column(Text, nullable=True)
    share_plan_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="summary")

    def __repr__(self):
        return f"<SessionSummary(session_id={self.session_id})>"
