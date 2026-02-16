"""Admin routes for user and session management."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func

from app.api.deps import DBSession, AdminUser
from app.core.security import get_password_hash
from app.models.student import Student
from app.models.session import Session as ChatSession
from app.models.message import Message
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate
from app.schemas.session import SessionList, SessionRead
from app.schemas.message import MessageRead

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/students", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    student_in: StudentCreate,
    db: DBSession,
    admin: AdminUser,
) -> Student:
    """
    Create a new student account (admin only).
    """
    # Check if username already exists
    existing = db.query(Student).filter(Student.username == student_in.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    student = Student(
        username=student_in.username,
        password_hash=get_password_hash(student_in.password),
        role=student_in.role,
        display_name=student_in.display_name,
        pronouns=student_in.pronouns,
        tone_pref=student_in.tone_pref,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    return student


@router.get("/students", response_model=list[StudentRead])
def list_students(
    db: DBSession,
    admin: AdminUser,
    skip: int = 0,
    limit: int = 100,
) -> list[Student]:
    """
    List all students (admin only).
    """
    students = db.query(Student).offset(skip).limit(limit).all()
    return students


@router.get("/students/{student_id}", response_model=StudentRead)
def get_student(
    student_id: UUID,
    db: DBSession,
    admin: AdminUser,
) -> Student:
    """
    Get a specific student by ID (admin only).
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )
    return student


@router.patch("/students/{student_id}", response_model=StudentRead)
def update_student(
    student_id: UUID,
    student_in: StudentUpdate,
    db: DBSession,
    admin: AdminUser,
) -> Student:
    """
    Update a student's profile (admin only).
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    update_data = student_in.model_dump(exclude_unset=True)

    # Handle password update separately
    if "password" in update_data and update_data["password"]:
        student.password_hash = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(student, field, value)

    db.commit()
    db.refresh(student)

    return student


@router.get("/sessions", response_model=SessionList)
def list_all_sessions(
    db: DBSession,
    admin: AdminUser,
    page: int = 1,
    page_size: int = 20,
) -> SessionList:
    """
    List all sessions across all students (admin only).
    """
    offset = (page - 1) * page_size

    total = db.query(func.count(ChatSession.id)).scalar() or 0
    sessions = (
        db.query(ChatSession)
        .order_by(ChatSession.started_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return SessionList(
        items=[SessionRead.model_validate(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sessions/{session_id}", response_model=SessionRead)
def get_session_admin(
    session_id: UUID,
    db: DBSession,
    admin: AdminUser,
) -> ChatSession:
    """
    Get a specific session by ID (admin only).
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return session


@router.get("/sessions/{session_id}/messages", response_model=list[MessageRead])
def get_session_messages_admin(
    session_id: UUID,
    db: DBSession,
    admin: AdminUser,
) -> list[Message]:
    """
    Get all messages for a session with full metadata (admin only).
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    messages = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return messages
