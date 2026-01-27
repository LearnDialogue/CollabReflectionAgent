"""Authentication routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import DBSession, CurrentUser
from app.core.security import verify_password, create_access_token
from app.models.student import Student
from app.schemas.auth import LoginRequest, Token
from app.schemas.student import StudentRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: DBSession) -> Token:
    """
    Authenticate user and return JWT token.
    """
    user = db.query(Student).filter(Student.username == request.username).first()

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=StudentRead)
def get_current_user_info(current_user: CurrentUser) -> Student:
    """
    Get current authenticated user's info.
    """
    return current_user
