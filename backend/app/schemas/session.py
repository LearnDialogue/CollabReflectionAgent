"""Session schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.session import SessionStatus


class SessionCreate(BaseModel):
    """Create a new session (student)."""

    pass  # No fields required; student_id comes from JWT


class SessionRead(BaseModel):
    """Session response."""

    id: UUID
    student_id: UUID
    status: SessionStatus
    current_stage: str
    prompt_version: str
    model_name: str
    started_at: datetime
    completed_at: datetime | None = None
    evaluation_data: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class SessionList(BaseModel):
    """Paginated list of sessions."""

    items: list[SessionRead]
    total: int
    page: int
    page_size: int
