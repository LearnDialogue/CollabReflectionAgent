# AgenticRoboticsEvaluator - System Document

## Project Overview

**Project Name:** AgenticRoboticsEvaluator  
**Purpose:** A chat-only MVP for a near-peer reflective agent used weekly after robotics meetings  
**Current Phase:** D1 (Foundation)  
**Date:** January 27, 2026  

### Core Design Principles

1. **Deterministic & Research-Friendly**: The backend enforces a fixed multi-stage reflection protocol
2. **No LangChain/LangGraph**: Custom "FlowEngine" implementation (finite-state/stage controller)
3. **Structured Outputs**: System designed for structured JSON outputs from models (implemented later)
4. **Complete Audit Trail**: All transcripts + structured summaries stored for research purposes
5. **Admin Exports**: Support for data export and analysis

---

## D1 Scope (Foundation)

D1 delivers a **runnable skeleton** with:
- Repository layout and Docker infrastructure
- Database schema and migrations
- Authentication system (JWT + roles)
- Basic session/message endpoints
- Minimal chat UI that hits the backend

**Explicitly NOT in D1:**
- Real LLM integration (placeholder responses only)
- Stage advancement logic (FlowEngine structure created but not active)
- Session summaries population
- Safety incident detection
- Export functionality
- Comprehensive frontend testing

---

## Technology Stack (Locked for D1)

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12 + FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Frontend | React + TypeScript (Next.js) |
| Local Dev | Docker Compose |
| Auth | JWT with bcrypt password hashing |
| Backend Tests | pytest |
| Config | Environment variables (.env) |

---

## Repository Structure

```
/AgenticRoboticsEvaluator
├── /backend
│   ├── /app
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── /core
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Settings from environment
│   │   │   └── security.py            # JWT + password hashing
│   │   ├── /db
│   │   │   ├── __init__.py
│   │   │   ├── session.py             # Database session management
│   │   │   └── base.py                # SQLAlchemy base + model imports
│   │   ├── /models
│   │   │   ├── __init__.py
│   │   │   ├── student.py             # Student model
│   │   │   ├── session.py             # Session model
│   │   │   ├── message.py             # Message model
│   │   │   ├── session_summary.py     # SessionSummary model
│   │   │   └── safety_incident.py     # SafetyIncident model
│   │   ├── /schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # Login request/response schemas
│   │   │   ├── student.py             # Student schemas
│   │   │   ├── session.py             # Session schemas
│   │   │   └── message.py             # Message schemas
│   │   ├── /api
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                # Dependency injection (get_db, get_current_user)
│   │   │   └── /routes
│   │   │       ├── __init__.py
│   │   │       ├── auth.py            # /auth/* endpoints
│   │   │       ├── admin.py           # /admin/* endpoints
│   │   │       ├── sessions.py        # /sessions/* endpoints
│   │   │       └── health.py          # /health endpoint
│   │   └── /services
│   │       ├── __init__.py
│   │       └── flow_engine.py         # FlowEngine (stage controller)
│   ├── /alembic
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── /versions
│   │       └── 001_initial_schema.py  # Initial migration
│   ├── /tests
│   │   ├── __init__.py
│   │   ├── conftest.py                # pytest fixtures
│   │   ├── test_auth.py               # Auth endpoint tests
│   │   └── test_sessions.py           # Session/message tests
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── seed_admin.py                  # Script to create first admin
│
├── /frontend
│   ├── /src
│   │   ├── /app
│   │   │   ├── layout.tsx             # Root layout
│   │   │   ├── page.tsx               # Home (redirect to login)
│   │   │   ├── /login
│   │   │   │   └── page.tsx           # Login page
│   │   │   └── /chat
│   │   │       └── page.tsx           # Chat page
│   │   ├── /components
│   │   │   ├── ChatMessage.tsx        # Single message component
│   │   │   └── ChatInput.tsx          # Message input component
│   │   ├── /lib
│   │   │   └── api.ts                 # API client functions
│   │   └── /types
│   │       └── index.ts               # TypeScript types
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   └── .env.example
│
├── /infra
│   └── docker-compose.yml             # Docker Compose configuration
│
└── /docs
    ├── SYSTEM.md                      # This document
    └── SETUP.md                       # Setup/running instructions
```

---

## Database Schema

### Entity Relationship Overview

```
students (1) ──────< (N) sessions (1) ──────< (N) messages
    │                       │
    │                       └──────< (1) session_summaries
    │                       │
    └──────────────────────< (N) safety_incidents >──────── messages
```

### Table Definitions

#### 1. `students`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Unique identifier |
| username | VARCHAR(255) | UNIQUE, NOT NULL | Login username |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hashed password |
| role | ENUM('STUDENT', 'ADMIN') | NOT NULL, default 'STUDENT' | User role |
| display_name | VARCHAR(255) | NULLABLE | Preferred display name |
| pronouns | VARCHAR(50) | NULLABLE | User's pronouns |
| tone_pref | VARCHAR(100) | NULLABLE | Preferred agent tone |
| created_at | TIMESTAMP | NOT NULL, default NOW() | Account creation time |

#### 2. `sessions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Unique identifier |
| student_id | UUID | FK -> students.id, NOT NULL | Owning student |
| status | ENUM('ACTIVE', 'COMPLETED') | NOT NULL, default 'ACTIVE' | Session state |
| current_stage | VARCHAR(50) | NOT NULL | Current reflection stage ID |
| prompt_version | VARCHAR(20) | NOT NULL | Version of prompts used |
| model_name | VARCHAR(100) | NOT NULL | LLM model identifier |
| started_at | TIMESTAMP | NOT NULL, default NOW() | Session start time |
| completed_at | TIMESTAMP | NULLABLE | Session completion time |

#### 3. `messages`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Unique identifier |
| session_id | UUID | FK -> sessions.id, NOT NULL | Parent session |
| role | ENUM('user', 'assistant') | NOT NULL | Message author role |
| content | TEXT | NOT NULL | Message content |
| stage_id | VARCHAR(50) | NOT NULL | Stage at time of message |
| created_at | TIMESTAMP | NOT NULL, default NOW() | Message creation time |

#### 4. `session_summaries`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| session_id | UUID | PK, FK -> sessions.id | Session reference |
| event_summary | TEXT | NULLABLE | Summary of recalled event |
| challenges | TEXT | NULLABLE | Identified challenges |
| strategies | TEXT | NULLABLE | Discussed strategies |
| next_goal | TEXT | NULLABLE | Goal set for next week |
| share_plan_json | JSONB | NULLABLE | Structured sharing plan |
| created_at | TIMESTAMP | NOT NULL, default NOW() | Summary creation time |

#### 5. `safety_incidents`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, default uuid_generate_v4() | Unique identifier |
| student_id | UUID | FK -> students.id, NOT NULL | Related student |
| session_id | UUID | FK -> sessions.id, NULLABLE | Related session |
| message_id | UUID | FK -> messages.id, NOT NULL | Triggering message |
| category | VARCHAR(100) | NOT NULL | Incident category |
| severity | VARCHAR(50) | NOT NULL | Severity level |
| notified | BOOLEAN | NOT NULL, default FALSE | Notification sent flag |
| notified_at | TIMESTAMP | NULLABLE | Notification time |
| created_at | TIMESTAMP | NOT NULL, default NOW() | Incident detection time |

---

## API Endpoints

### Authentication (`/auth`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/login` | None | Authenticate and receive JWT |
| GET | `/auth/me` | JWT | Get current user info |

#### POST /auth/login
**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```
**Response (200):**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

#### GET /auth/me
**Response (200):**
```json
{
  "id": "uuid",
  "username": "string",
  "role": "STUDENT | ADMIN",
  "display_name": "string | null",
  "pronouns": "string | null",
  "tone_pref": "string | null"
}
```

### Admin (`/admin`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/admin/students` | ADMIN | Create student account |
| POST | `/admin/students/{id}/reset-password` | ADMIN | Reset student password |

#### POST /admin/students
**Request:**
```json
{
  "username": "string",
  "password": "string",
  "display_name": "string | null",
  "pronouns": "string | null",
  "tone_pref": "string | null"
}
```
**Response (201):**
```json
{
  "id": "uuid",
  "username": "string",
  "role": "STUDENT",
  "display_name": "string | null",
  "pronouns": "string | null",
  "tone_pref": "string | null",
  "created_at": "datetime"
}
```

#### POST /admin/students/{id}/reset-password
**Request:**
```json
{
  "new_password": "string"
}
```
**Response (200):**
```json
{
  "message": "Password reset successfully"
}
```

### Sessions (`/sessions`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/sessions` | STUDENT | Create new reflection session |
| POST | `/sessions/{session_id}/messages` | STUDENT | Send message in session |

#### POST /sessions
**Response (201):**
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "status": "ACTIVE",
  "current_stage": "RECALL_EVENT",
  "prompt_version": "v1",
  "model_name": "placeholder",
  "started_at": "datetime"
}
```

#### POST /sessions/{session_id}/messages
**Request:**
```json
{
  "content": "string"
}
```
**Response (201):**
```json
{
  "user_message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "user",
    "content": "string",
    "stage_id": "string",
    "created_at": "datetime"
  },
  "assistant_message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "Thanks — tell me more.",
    "stage_id": "string",
    "created_at": "datetime"
  }
}
```

### Health (`/health`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | None | Health check |

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "datetime"
}
```

---

## FlowEngine Design

### Reflection Protocol Stages (D1 Hardcoded)

```python
STAGES = [
    "RECALL_EVENT",        # Student recalls a specific event from the robotics meeting
    "ANALYZE_INTERACTION", # Analyze what happened and why
    "CHALLENGES_STRATEGIES", # Identify challenges and potential strategies
    "SET_GOAL",           # Set a concrete goal for next week
    "PLAN_SHARE",         # Plan how/what to share with team
]
```

### FlowEngine Interface (D1)

```python
class FlowEngine:
    STAGES: list[str]
    
    @staticmethod
    def get_current_stage(session: Session) -> str:
        """Return the current stage ID for a session."""
        
    @staticmethod
    def advance_stage(session: Session) -> str | None:
        """Advance to next stage. Returns new stage or None if complete."""
```

### Future Enhancements (Post-D1)
- Stage configuration moved to `flow_config.yaml`
- Per-stage prompt templates
- Conditional stage transitions
- Stage completion criteria

---

## Authentication & Security

### JWT Configuration
- Algorithm: HS256
- Expiration: 24 hours (configurable)
- Payload: `{ sub: user_id, role: role, exp: expiry }`

### Password Handling
- Hashing: bcrypt with auto-generated salt
- Minimum password length: 8 characters (enforced in schema)

### Role-Based Access Control
| Role | Permissions |
|------|-------------|
| STUDENT | Create sessions, send messages, view own data |
| ADMIN | All STUDENT permissions + create students, reset passwords |

### CORS Configuration
- Allowed origins: `http://localhost:3000` (D1)
- Allowed methods: GET, POST, PUT, DELETE
- Allowed headers: Authorization, Content-Type

---

## Docker Infrastructure

### Services

```yaml
services:
  postgres:
    image: postgres:15
    ports: 5432:5432
    volumes: postgres_data:/var/lib/postgresql/data
    
  backend:
    build: ../backend
    ports: 8000:8000
    depends_on: postgres
    
  frontend:
    build: ../frontend
    ports: 3000:3000
    depends_on: backend
```

### Environment Variables

#### Backend (.env)
```
DATABASE_URL=postgresql://user:password@postgres:5432/evaluator
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### Frontend (.env)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Testing Strategy (D1)

### Backend Tests (pytest)

| Test File | Coverage |
|-----------|----------|
| `test_auth.py` | Login success, login failure, /me endpoint |
| `test_sessions.py` | Create session, send message, message storage |

### Test Database
- Use separate test database or transaction rollback
- Fixtures for test user creation

---

## Frontend Architecture (D1)

### Pages

1. **`/login`** - Login form
   - Username/password inputs
   - Submit calls `POST /auth/login`
   - Store JWT in localStorage
   - Redirect to `/chat` on success

2. **`/chat`** - Chat interface
   - "Start Session" button (if no active session)
   - Message list (scrollable)
   - Message input with send button
   - Display both user and assistant messages

### State Management (D1 Simple)
- JWT stored in localStorage
- Current session ID in component state
- Messages array in component state

### API Client
- Axios or fetch wrapper
- Automatic Authorization header injection
- Base URL from environment

---

## D1 Definition of Done

Running `docker compose up --build` successfully boots all services. The following workflow is possible:

1. ✅ Run seed script to create admin account
2. ✅ Login as admin via UI or API
3. ✅ Create student account via admin endpoint
4. ✅ Login as student via UI
5. ✅ Click "Start Session" to create new session
6. ✅ Send message in chat UI
7. ✅ See placeholder assistant response
8. ✅ Verify data in database:
   - Session record exists with correct student_id
   - Messages exist with correct session_id and stage_id
   - Both user and assistant messages logged

---

## File Creation Checklist

### Backend Files
- [ ] `/backend/app/__init__.py`
- [ ] `/backend/app/main.py`
- [ ] `/backend/app/core/__init__.py`
- [ ] `/backend/app/core/config.py`
- [ ] `/backend/app/core/security.py`
- [ ] `/backend/app/db/__init__.py`
- [ ] `/backend/app/db/session.py`
- [ ] `/backend/app/db/base.py`
- [ ] `/backend/app/models/__init__.py`
- [ ] `/backend/app/models/student.py`
- [ ] `/backend/app/models/session.py`
- [ ] `/backend/app/models/message.py`
- [ ] `/backend/app/models/session_summary.py`
- [ ] `/backend/app/models/safety_incident.py`
- [ ] `/backend/app/schemas/__init__.py`
- [ ] `/backend/app/schemas/auth.py`
- [ ] `/backend/app/schemas/student.py`
- [ ] `/backend/app/schemas/session.py`
- [ ] `/backend/app/schemas/message.py`
- [ ] `/backend/app/api/__init__.py`
- [ ] `/backend/app/api/deps.py`
- [ ] `/backend/app/api/routes/__init__.py`
- [ ] `/backend/app/api/routes/auth.py`
- [ ] `/backend/app/api/routes/admin.py`
- [ ] `/backend/app/api/routes/sessions.py`
- [ ] `/backend/app/api/routes/health.py`
- [ ] `/backend/app/services/__init__.py`
- [ ] `/backend/app/services/flow_engine.py`
- [ ] `/backend/alembic/env.py`
- [ ] `/backend/alembic/script.py.mako`
- [ ] `/backend/alembic/versions/001_initial_schema.py`
- [ ] `/backend/tests/__init__.py`
- [ ] `/backend/tests/conftest.py`
- [ ] `/backend/tests/test_auth.py`
- [ ] `/backend/tests/test_sessions.py`
- [ ] `/backend/alembic.ini`
- [ ] `/backend/Dockerfile`
- [ ] `/backend/requirements.txt`
- [ ] `/backend/.env.example`
- [ ] `/backend/seed_admin.py`

### Frontend Files
- [ ] `/frontend/src/app/layout.tsx`
- [ ] `/frontend/src/app/page.tsx`
- [ ] `/frontend/src/app/login/page.tsx`
- [ ] `/frontend/src/app/chat/page.tsx`
- [ ] `/frontend/src/components/ChatMessage.tsx`
- [ ] `/frontend/src/components/ChatInput.tsx`
- [ ] `/frontend/src/lib/api.ts`
- [ ] `/frontend/src/types/index.ts`
- [ ] `/frontend/Dockerfile`
- [ ] `/frontend/package.json`
- [ ] `/frontend/tsconfig.json`
- [ ] `/frontend/next.config.js`
- [ ] `/frontend/.env.example`

### Infrastructure Files
- [ ] `/infra/docker-compose.yml`

### Documentation Files
- [ ] `/docs/SYSTEM.md` (this file)
- [ ] `/docs/SETUP.md`

---

## Implementation Order

1. **Phase 1: Infrastructure**
   - Create folder structure
   - Docker Compose configuration
   - Backend Dockerfile
   - Frontend Dockerfile
   - Environment example files

2. **Phase 2: Backend Core**
   - Config and security modules
   - Database session management
   - SQLAlchemy models
   - Alembic migrations

3. **Phase 3: Backend API**
   - Pydantic schemas
   - API dependencies
   - Auth endpoints
   - Admin endpoints
   - Session endpoints
   - Health endpoint
   - FlowEngine placeholder

4. **Phase 4: Backend Tests**
   - Test configuration
   - Auth tests
   - Session tests

5. **Phase 5: Frontend**
   - Next.js setup
   - API client
   - Login page
   - Chat page
   - Components

6. **Phase 6: Documentation**
   - SETUP.md with complete instructions

---

## Notes for Future Phases

### D2 (Flow & Prompts)
- Implement stage advancement logic
- Add stage-specific prompts
- Move stages to YAML configuration

### D3 (LLM Integration)
- Integrate actual LLM (OpenAI/Anthropic)
- Structured JSON output parsing
- Response validation

### D4 (Summaries & Safety)
- Automatic session summary generation
- Safety incident detection
- Admin notification system

### D5 (Export & Analytics)
- Admin data export endpoints
- Research-friendly data formats
- Basic analytics dashboard

---

---

## Appendix: TutorSiteScratch Analysis

### Overview of TutorSiteScratch

After thorough examination of `/Users/aman/projects/TutorSiteScratch`, here's what exists:

**Backend**: Java + Spring Boot (NOT Python/FastAPI)
- Uses Flyway for migrations (not Alembic)
- JWT authentication with Spring Security
- Complex domain model: users, sessions, tutors, subjects, chat channels, time proposals, recurring series, question bank, file storage
- REST API with `/api/v1` prefix

**Frontend**: React + TypeScript + Vite (NOT Next.js)
- Uses React Router (not Next.js app router)
- TanStack Query for data fetching
- shadcn/ui components (Radix primitives)
- Tailwind CSS with custom theme
- Complex features: multi-account sessions, chat with file attachments, calendars, recurring scheduling

### What We CANNOT Directly Reuse

| Component | Reason |
|-----------|--------|
| Backend code | Java/Spring ≠ Python/FastAPI |
| Migrations | Flyway SQL ≠ Alembic Python |
| Auth implementation | Spring Security ≠ FastAPI + python-jose |
| API client | Uses Vite proxy, not Next.js API routes |
| Chat system | Complex channels/groups/files - way beyond our MVP |
| Most pages | Tutor-specific: scheduling, subjects, question bank |
| Router setup | React Router ≠ Next.js App Router |

### What We CAN Adapt (Minimal/Patterns Only)

#### 1. Frontend UI Components (Simplify for Next.js)

These shadcn/ui-style components are reusable patterns:

```
/frontend/src/components/ui/
├── button.tsx      ✅ Adapt (remove rose-900 branding, use neutral)
├── card.tsx        ✅ Adapt 
├── input.tsx       ✅ Adapt
├── label.tsx       ✅ Adapt
├── dialog.tsx      ⚠️ Maybe later (not needed for D1)
└── others          ❌ Skip for D1
```

**Action**: Don't copy these directly. Use `npx shadcn@latest add button card input label` in Next.js project instead - it's cleaner.

#### 2. Auth Pattern (Conceptual Only)

The `AuthContext.tsx` shows a pattern:
- Store JWT in localStorage
- Context provides `{ user, token, login, logout, isAuthenticated }`
- Interceptor adds `Authorization: Bearer ${token}` header

**Action**: Implement fresh in our codebase. Their version has multi-session complexity we don't need.

#### 3. API Client Pattern (Conceptual Only)

```typescript
// Pattern to follow (simplified):
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('jwt_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

**Action**: Implement fresh, simpler version.

#### 4. Login Page Structure (Visual Layout Only)

The login page has nice structure:
- Card centered on page
- Form with email/password
- Error display
- Link to register

**Action**: Build fresh with Next.js patterns, but similar visual structure.

### What We Should NOT Take

| Item | Why Skip |
|------|----------|
| `ChatWindow.tsx` | Too complex - channels, file attachments, session panels |
| `MessageThread.tsx` | ~600 lines, handles files/media/intersection observers |
| `ChatSidebar.tsx` | Complex channel management, pinning, groups |
| `useChat.ts` hook | TanStack Query + complex channel logic |
| `AuthContext.tsx` | Multi-session support, page reload on switch |
| Most UI components | We'll use shadcn/ui fresh install |
| Any pages | All tutor-specific |
| Docker config | Too minimal (just postgres), we need full stack |

### Recommended Approach

**DO NOT copy files from TutorSiteScratch.**

Instead:

1. **UI Components**: Use `npx shadcn@latest init` in Next.js and add components fresh
2. **Auth**: Write simple `AuthContext` with single-user JWT storage
3. **API Client**: Write simple axios/fetch wrapper
4. **Chat UI**: Build from scratch - our needs are much simpler:
   - No channels (1 session = 1 conversation)
   - No file attachments (D1)
   - No groups
   - No read receipts
   - Simple message list + input

### D1 Chat Component Spec (What We Actually Need)

```typescript
// Our chat is MUCH simpler than TutorSiteScratch:

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  stage_id: string;
  created_at: string;
}

interface ChatProps {
  sessionId: string;
  messages: Message[];
  onSendMessage: (content: string) => void;
  isLoading: boolean;
}

// That's it. No channels, no files, no groups, no read status.
```

### Summary: Build Fresh, Don't Copy

The TutorSiteScratch codebase is:
1. Wrong backend stack (Java vs Python)
2. Wrong frontend framework (Vite vs Next.js)
3. Overcomplicated for our MVP (tutoring platform vs reflection chat)

**Recommendation**: Use TutorSiteScratch only as **visual inspiration** for:
- Login page layout
- Card-based UI aesthetic
- Message bubble styling

Build everything from scratch using:
- `create-next-app` with TypeScript
- `shadcn/ui` for components
- Simple custom `AuthContext`
- Simple custom chat components

This will be **faster and cleaner** than adapting their code.

---

*Document Version: 1.1*  
*Last Updated: January 27, 2026*  
*Added: TutorSiteScratch analysis appendix*
