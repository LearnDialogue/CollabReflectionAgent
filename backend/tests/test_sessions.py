"""
Tests for session and chat endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.student import Student
from app.models.session import Session as ChatSession, SessionStatus
from app.models.message import Message, MessageRole


class TestCreateSession:
    """Tests for POST /sessions."""

    def test_create_session_student(
        self,
        client: TestClient,
        student_user: Student,
        student_headers: dict,
    ):
        """Test student can create a new session."""
        response = client.post("/sessions", headers=student_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["student_id"] == student_user.id
        assert data["status"] == "in_progress"
        assert data["current_stage"] == "greeting"
        assert "id" in data

    def test_create_session_admin_forbidden(
        self,
        client: TestClient,
        admin_user: Student,
        admin_headers: dict,
    ):
        """Test admin cannot create session (student role required)."""
        response = client.post("/sessions", headers=admin_headers)
        
        assert response.status_code == 403
        assert response.json()["detail"] == "Student access required"

    def test_create_session_unauthenticated(self, client: TestClient, db: Session):
        """Test unauthenticated user cannot create session."""
        response = client.post("/sessions")
        
        assert response.status_code == 403


class TestListSessions:
    """Tests for GET /sessions."""

    def test_list_own_sessions(
        self,
        client: TestClient,
        student_user: Student,
        student_headers: dict,
        db: Session,
    ):
        """Test student can list their own sessions."""
        # Create a session first
        session = ChatSession(
            student_id=student_user.id,
            status=SessionStatus.IN_PROGRESS,
            current_stage="greeting",
            prompt_version="v1.0",
            model_name="gpt-4o-mini",
        )
        db.add(session)
        db.commit()
        
        response = client.get("/sessions", headers=student_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["student_id"] == student_user.id


class TestChat:
    """Tests for POST /sessions/{id}/chat."""

    def test_send_message(
        self,
        client: TestClient,
        student_user: Student,
        student_headers: dict,
        db: Session,
    ):
        """Test sending a message and receiving response."""
        # Create session
        session = ChatSession(
            student_id=student_user.id,
            status=SessionStatus.IN_PROGRESS,
            current_stage="greeting",
            prompt_version="v1.0",
            model_name="gpt-4o-mini",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        response = client.post(
            f"/sessions/{session.id}/chat",
            headers=student_headers,
            json={"content": "Hello, I'm working on a robot arm project"},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check user message was recorded
        assert data["user_message"]["role"] == "user"
        assert data["user_message"]["content"] == "Hello, I'm working on a robot arm project"
        
        # Check assistant responded
        assert data["assistant_message"]["role"] == "assistant"
        assert len(data["assistant_message"]["content"]) > 0
        
        # Check session state
        assert data["session_status"] == "in_progress"

    def test_chat_advances_stage(
        self,
        client: TestClient,
        student_user: Student,
        student_headers: dict,
        db: Session,
    ):
        """Test saying 'next' advances the stage."""
        session = ChatSession(
            student_id=student_user.id,
            status=SessionStatus.IN_PROGRESS,
            current_stage="greeting",
            prompt_version="v1.0",
            model_name="gpt-4o-mini",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        response = client.post(
            f"/sessions/{session.id}/chat",
            headers=student_headers,
            json={"content": "Yes, let's continue to the next part"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_stage"] == "context_gathering"

    def test_chat_other_student_session_forbidden(
        self,
        client: TestClient,
        student_user: Student,
        student_headers: dict,
        admin_user: Student,
        db: Session,
    ):
        """Test student cannot chat in another student's session."""
        # Create session owned by a different user
        other_student = Student(
            username="otherstudent",
            password_hash="hash",
            role=student_user.role,
        )
        db.add(other_student)
        db.commit()
        
        session = ChatSession(
            student_id=other_student.id,
            status=SessionStatus.IN_PROGRESS,
            current_stage="greeting",
            prompt_version="v1.0",
            model_name="gpt-4o-mini",
        )
        db.add(session)
        db.commit()
        
        response = client.post(
            f"/sessions/{session.id}/chat",
            headers=student_headers,
            json={"content": "Hello"},
        )
        
        assert response.status_code == 403

    def test_chat_completed_session_rejected(
        self,
        client: TestClient,
        student_user: Student,
        student_headers: dict,
        db: Session,
    ):
        """Test cannot chat in completed session."""
        session = ChatSession(
            student_id=student_user.id,
            status=SessionStatus.COMPLETED,
            current_stage="wrap_up",
            prompt_version="v1.0",
            model_name="gpt-4o-mini",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        response = client.post(
            f"/sessions/{session.id}/chat",
            headers=student_headers,
            json={"content": "Hello"},
        )
        
        assert response.status_code == 400
        assert "already completed" in response.json()["detail"]


class TestMessagePersistence:
    """Tests for message persistence."""

    def test_messages_persisted(
        self,
        client: TestClient,
        student_user: Student,
        student_headers: dict,
        db: Session,
    ):
        """Test messages are persisted to database."""
        # Create session
        session = ChatSession(
            student_id=student_user.id,
            status=SessionStatus.IN_PROGRESS,
            current_stage="greeting",
            prompt_version="v1.0",
            model_name="gpt-4o-mini",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Send message
        client.post(
            f"/sessions/{session.id}/chat",
            headers=student_headers,
            json={"content": "Test message"},
        )
        
        # Fetch messages
        response = client.get(
            f"/sessions/{session.id}/messages",
            headers=student_headers,
        )
        
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 2  # user + assistant
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Test message"
        assert messages[1]["role"] == "assistant"
