"""Message schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.message import MessageRole


class MessageCreate(BaseModel):
    """Internal: create a message record."""

    session_id: UUID
    role: MessageRole
    content: str
    stage_id: str


class MessageRead(BaseModel):
    """Message response."""

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    stage_id: str
    llm_metadata: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    """User sends a chat message."""

    content: str


class ChatResponse(BaseModel):
    """Agent reply to a chat message."""

    user_message: MessageRead
    assistant_message: MessageRead
    session_status: str
    current_stage: str
