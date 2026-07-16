"""
SessionSummary model - stores structured summaries of completed sessions.

Contains BOTH the original general-purpose columns (event_summary, challenges,
strategies, next_goal) AND SRL-aligned columns that map to the self-regulated
learning cycle. Both sets coexist to support different analysis lenses.

Note: The SRL-aligned column names still use the original ELT terminology
(concrete_experience, reflective_observation, etc.) in the database to avoid
a migration. Their semantic interpretation has been updated to SRL phases.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class SessionSummary(Base):
    """
    SessionSummary model storing structured extraction from a session.
    Created/updated after session completion.

    General-purpose columns capture practical outcomes.
    SRL columns capture the regulatory cycle for research analysis.
    """
    __tablename__ = "session_summaries"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), primary_key=True)

    # --- General-purpose summaries (original columns) ---
    event_summary = Column(Text, nullable=True)
    challenges = Column(Text, nullable=True)
    strategies = Column(Text, nullable=True)
    next_goal = Column(Text, nullable=True)
    share_plan_json = Column(JSONB, nullable=True)

    # --- SRL-aligned summaries (regulatory cycle) ---
    # Column names retain ELT terminology for database compatibility
    concrete_experience = Column(Text, nullable=True)       # SRL: Task understanding — what the team was working on
    reflective_observation = Column(Text, nullable=True)    # SRL: Planning — how the team planned their approach
    abstract_conceptualization = Column(Text, nullable=True) # SRL: Monitoring — how the team tracked and adjusted
    active_experimentation = Column(Text, nullable=True)    # SRL: Adaptation — what the student will try differently

    # Timestamps
    created_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    session = relationship("Session", back_populates="summary")

    def __repr__(self):
        return f"<SessionSummary(session_id={self.session_id})>"
