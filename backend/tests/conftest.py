"""
Pytest fixtures for backend tests.
"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import SessionLocal
from app.api.deps import get_db
from app.models.student import Student, UserRole
from app.core.security import get_password_hash, create_access_token


# In-memory SQLite for testing
SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override database dependency with test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create test client with database."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def admin_user(db: Session) -> Student:
    """Create an admin user for testing."""
    admin = Student(
        username="testadmin",
        password_hash=get_password_hash("adminpass123"),
        role=UserRole.ADMIN,
        display_name="Test Admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def student_user(db: Session) -> Student:
    """Create a student user for testing."""
    student = Student(
        username="teststudent",
        password_hash=get_password_hash("studentpass123"),
        role=UserRole.STUDENT,
        display_name="Test Student",
        pronouns="they/them",
        tone_pref="friendly",
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@pytest.fixture(scope="function")
def admin_token(admin_user: Student) -> str:
    """Generate JWT token for admin user."""
    return create_access_token(
        data={"sub": admin_user.username, "role": admin_user.role.value}
    )


@pytest.fixture(scope="function")
def student_token(student_user: Student) -> str:
    """Generate JWT token for student user."""
    return create_access_token(
        data={"sub": student_user.username, "role": student_user.role.value}
    )


@pytest.fixture(scope="function")
def admin_headers(admin_token: str) -> dict:
    """Authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def student_headers(student_token: str) -> dict:
    """Authorization headers for student user."""
    return {"Authorization": f"Bearer {student_token}"}
