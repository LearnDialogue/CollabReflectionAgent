"""Student schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.student import UserRole


class StudentBase(BaseModel):
    """Base student fields."""

    username: str
    display_name: str | None = None
    pronouns: str | None = None
    tone_pref: str | None = None


class StudentCreate(StudentBase):
    """Create a new student (admin only)."""

    password: str
    role: UserRole = UserRole.STUDENT


class StudentUpdate(BaseModel):
    """Update student profile (self or admin)."""

    display_name: str | None = None
    pronouns: str | None = None
    tone_pref: str | None = None
    password: str | None = None  # Admin can reset password


class StudentRead(StudentBase):
    """Student response (excludes password_hash)."""

    id: UUID
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
