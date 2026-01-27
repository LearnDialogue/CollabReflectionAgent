# D1 Foundation - Implementation Tasks

## Purpose

Build a **runnable skeleton** of the AgenticRoboticsEvaluator that demonstrates:
1. A student can log in
2. A student can start a reflection session
3. A student can send messages and see (placeholder) assistant replies
4. All data is persisted to PostgreSQL
5. An admin can create student accounts

**End State**: `docker compose up --build` → working app with login, chat, and database persistence.

---

## Task Checklist

### Phase 1: Project Infrastructure

#### 1.1 Create Directory Structure
- [x] Create `/backend` folder
- [x] Create `/backend/app` folder
- [x] Create `/backend/app/core` folder
- [x] Create `/backend/app/db` folder
- [x] Create `/backend/app/models` folder
- [x] Create `/backend/app/schemas` folder
- [x] Create `/backend/app/api` folder
- [x] Create `/backend/app/api/routes` folder
- [x] Create `/backend/app/services` folder
- [x] Create `/backend/alembic` folder
- [x] Create `/backend/alembic/versions` folder
- [x] Create `/backend/tests` folder
- [x] Create `/frontend` folder
- [x] Create `/frontend/src` folder
- [x] Create `/frontend/src/app` folder
- [x] Create `/frontend/src/app/login` folder
- [x] Create `/frontend/src/app/chat` folder
- [x] Create `/frontend/src/components` folder
- [x] Create `/frontend/src/lib` folder
- [x] Create `/frontend/src/types` folder
- [x] Create `/infra` folder

#### 1.2 Docker & Infrastructure Files
- [x] Create `/infra/docker-compose.yml` with postgres, backend, frontend services
- [x] Create `/backend/Dockerfile` (Python 3.12 + FastAPI)
- [x] Create `/backend/requirements.txt` with all Python dependencies
- [x] Create `/backend/.env.example` with environment variable templates
- [x] Create `/frontend/Dockerfile` (Node + Next.js)
- [x] Create `/frontend/.env.example` with environment variable templates

---

### Phase 2: Backend Core Setup

#### 2.1 Application Entry & Config
- [x] Create `/backend/app/__init__.py` (empty)
- [x] Create `/backend/app/main.py` (FastAPI app, CORS, router includes)
- [x] Create `/backend/app/core/__init__.py` (empty)
- [x] Create `/backend/app/core/config.py` (Settings class with env vars)
- [x] Create `/backend/app/core/security.py` (password hashing + JWT functions)

#### 2.2 Database Setup
- [x] Create `/backend/app/db/__init__.py` (empty)
- [x] Create `/backend/app/db/session.py` (SQLAlchemy engine + session)
- [x] Create `/backend/app/db/base.py` (Base class + import all models)

#### 2.3 SQLAlchemy Models
- [x] Create `/backend/app/models/__init__.py` (export all models)
- [x] Create `/backend/app/models/student.py` (Student model with id, username, password_hash, role, display_name, pronouns, tone_pref, created_at)
- [x] Create `/backend/app/models/session.py` (Session model with id, student_id, status, current_stage, prompt_version, model_name, started_at, completed_at)
- [x] Create `/backend/app/models/message.py` (Message model with id, session_id, role, content, stage_id, created_at)
- [x] Create `/backend/app/models/session_summary.py` (SessionSummary model)
- [x] Create `/backend/app/models/safety_incident.py` (SafetyIncident model)

#### 2.4 Alembic Migrations
- [x] Create `/backend/alembic.ini` (Alembic config file)
- [x] Create `/backend/alembic/env.py` (migration environment)
- [x] Create `/backend/alembic/script.py.mako` (migration template)
- [x] Create `/backend/alembic/versions/001_initial_schema.py` (create all tables)

---

### Phase 3: Backend API Implementation

#### 3.1 Pydantic Schemas
- [x] Create `/backend/app/schemas/__init__.py` (export all schemas)
- [x] Create `/backend/app/schemas/auth.py` (LoginRequest, TokenResponse, UserResponse)
- [x] Create `/backend/app/schemas/student.py` (StudentCreate, StudentResponse, PasswordReset)
- [x] Create `/backend/app/schemas/session.py` (SessionCreate, SessionResponse)
- [x] Create `/backend/app/schemas/message.py` (MessageCreate, MessageResponse, MessagePairResponse)

#### 3.2 API Dependencies
- [x] Create `/backend/app/api/__init__.py` (empty)
- [x] Create `/backend/app/api/deps.py` (get_db, get_current_user, require_admin, require_student)

#### 3.3 API Routes
- [x] Create `/backend/app/api/routes/__init__.py` (empty)
- [x] Create `/backend/app/api/routes/health.py` (GET /health endpoint)
- [x] Create `/backend/app/api/routes/auth.py` (POST /auth/login, GET /auth/me)
- [x] Create `/backend/app/api/routes/admin.py` (POST /admin/students, POST /admin/students/{id}/reset-password)
- [x] Create `/backend/app/api/routes/sessions.py` (POST /sessions, POST /sessions/{id}/messages)

#### 3.4 Services
- [x] Create `/backend/app/services/__init__.py` (empty)
- [x] Create `/backend/app/services/flow_engine.py` (STAGES list, get_current_stage, advance_stage)

#### 3.5 Seed Script
- [x] Create `/backend/seed_admin.py` (script to create initial admin user)

---

### Phase 4: Backend Tests

#### 4.1 Test Setup
- [x] Create `/backend/tests/__init__.py` (empty)
- [x] Create `/backend/tests/conftest.py` (pytest fixtures: test client, test db, test user)

#### 4.2 Test Files
- [x] Create `/backend/tests/test_auth.py` (test login success, login failure, /me endpoint)
- [x] Create `/backend/tests/test_sessions.py` (test create session, send message, message persistence)

---

### Phase 5: Frontend Setup

#### 5.1 Next.js Project Files
- [x] Create `/frontend/package.json` (dependencies: next, react, axios, tailwindcss, etc.)
- [x] Create `/frontend/tsconfig.json` (TypeScript config)
- [x] Create `/frontend/next.config.js` (Next.js config with API rewrites)
- [x] Create `/frontend/tailwind.config.js` (Tailwind config)
- [x] Create `/frontend/postcss.config.js` (PostCSS config)

#### 5.2 App Structure
- [x] Create `/frontend/src/app/layout.tsx` (root layout with AuthProvider)
- [x] Create `/frontend/src/app/page.tsx` (redirect to /login)
- [x] Create `/frontend/src/app/globals.css` (Tailwind imports + base styles)

#### 5.3 Shared Code
- [x] Create `/frontend/src/lib/api.ts` (axios client with auth interceptor)
- [x] Create `/frontend/src/lib/auth-context.tsx` (AuthContext: user, token, login, logout)

---

### Phase 6: Frontend Pages

#### 6.1 Login Page
- [x] Create `/frontend/src/app/login/page.tsx`
  - [x] Username input field
  - [x] Password input field
  - [x] Submit button
  - [x] Error message display
  - [x] Call POST /auth/login on submit
  - [x] Store JWT in localStorage
  - [x] Redirect to /chat on success

#### 6.2 Chat Page
- [x] Create `/frontend/src/app/chat/page.tsx`
  - [x] Check authentication (redirect to /login if not)
  - [x] "Start Session" button (calls POST /sessions)
  - [x] Display current session info
  - [x] Message list component
  - [x] Message input component
  - [x] Send message (calls POST /sessions/{id}/messages)
  - [x] Display user messages (right-aligned)
  - [x] Display assistant messages (left-aligned)
  - [x] Auto-scroll to latest message
  - [x] Logout button

---

### Phase 7: Documentation

#### 7.1 Setup Guide
- [x] Create `/docs/SETUP.md`
  - [x] Prerequisites (Docker, Docker Compose)
  - [x] Clone repository instructions
  - [x] Environment setup (.env files)
  - [x] `docker compose up --build` command
  - [x] Run migrations command
  - [x] Create admin user (seed script)
  - [x] Login as admin workflow
  - [x] Create student workflow
  - [x] Login as student workflow
  - [x] Start session and chat workflow
  - [x] Verify data in database instructions

---

### Phase 8: Integration Testing

#### 8.1 Manual Verification Checklist
- [ ] `docker compose up --build` starts all services
- [ ] PostgreSQL is accessible on port 5432
- [ ] Backend health check passes (GET http://localhost:8000/health)
- [ ] Frontend loads on http://localhost:3000
- [ ] Run seed script creates admin user
- [ ] Admin can login
- [ ] Admin can create student account
- [ ] Student can login
- [ ] Student can start session
- [ ] Student can send message
- [ ] Placeholder assistant reply appears
- [ ] Messages persist across page refresh
- [ ] Session data exists in database

---

## File Count Summary

| Category | Files |
|----------|-------|
| Backend Python | 24 |
| Backend Config | 5 |
| Frontend TypeScript | 14 |
| Frontend Config | 5 |
| Infrastructure | 1 |
| Documentation | 2 |
| **Total** | **51 files** |

---

## Execution Order

1. **Phase 1** - Infrastructure (can't do anything without folders and Docker)
2. **Phase 2** - Backend core (need config/db before anything else)
3. **Phase 3** - Backend API (need models before routes)
4. **Phase 4** - Backend tests (verify backend works)
5. **Phase 5** - Frontend setup (need structure before pages)
6. **Phase 6** - Frontend pages (the actual UI)
7. **Phase 7** - Documentation (how to run it)
8. **Phase 8** - Integration testing (verify everything works together)

---

## Definition of Done

All boxes checked above AND:
- [ ] `docker compose up --build` completes without errors
- [ ] Full workflow works: admin login → create student → student login → start session → send message → see reply
- [ ] Data verified in PostgreSQL (students, sessions, messages tables have data)
- [ ] Backend tests pass: `pytest` in backend container
- [ ] No console errors in browser

---

*Last Updated: January 27, 2026*
