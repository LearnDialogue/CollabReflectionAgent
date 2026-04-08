# Agentic Robotics Evaluator

A conversational AI agent designed to help robotics students reflect on their learning through Socratic questioning and guided dialogue. The agent guides students through structured reflection sessions, helping them articulate challenges, explore solutions, and plan next steps.

---

## Quick Start

```bash
# Clone and start everything
git clone <repo-url>
cd AgenticRoboticsEvaluator/infra
docker compose up --build

# Open the app (admin user is auto-created on first run)
open http://localhost:3000
```

**Login:** `admin` / `admin123`

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current Status](#current-status)
3. [Architecture](#architecture)
4. [Tech Stack](#tech-stack)
5. [Quick Start](#quick-start)
6. [Project Structure](#project-structure)
7. [Key Components Explained](#key-components-explained)
8. [What's Working vs. What's Planned](#whats-working-vs-whats-planned)
9. [Development Guide](#development-guide)
10. [Documentation](#documentation)

---

## Project Overview

### The Problem
Robotics students benefit from reflecting on their projects, but coaches have limited time for 1:1 conversations. Students need a supportive "near-peer" they can talk to weekly after team meetings.

### The Solution
A chat-based AI agent that:
- Guides students through a **7-stage reflection protocol**
- Uses **Socratic questioning** (asks questions rather than giving answers)
- Maintains **conversation history** across sessions
- Includes **safety monitoring** for concerning content (planned)
- Provides **session summaries** for coaches to review (planned)

### Design Principles
- **Near-peer tone**: Friendly and supportive, not authoritative
- **Student-driven**: The student leads the conversation
- **Scaffolded reflection**: Structured stages ensure meaningful dialogue
- **Privacy-conscious**: Minimal data collection, clear boundaries

---

## Current Status

The core system is fully functional with LLM integration, a dashboard UI, and post-session evaluation.

| Layer | Status | Description |
|-------|--------|-------------|
| Infrastructure | Complete | Docker Compose with PostgreSQL, backend, and frontend |
| Database | Complete | All tables created via Alembic migrations |
| Authentication | Complete | JWT-based login with role support |
| API | Complete | All CRUD endpoints for sessions, messages, users |
| LLM Integration | Complete | Llama 3.3 70B via UF Navigator, JSON mode, retry logic, structured responses |
| Dashboard UI | Complete | Session sidebar, chat, stage progress, metadata display |
| Post-Session Eval | Complete | Automated scoring, student profiling, recommendations |
| Safety Monitoring | Planned | Database table exists, detection logic not yet implemented |

**What you can do right now:**
1. Log in as admin or student
2. Start a chat session and have a real conversation with the AI tutor
3. Watch the agent progress through 7 reflection stages automatically
4. View LLM metadata and routing decisions on each message
5. See a full evaluation when the session completes
6. Inspect any session with detailed metadata on the inspect page

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                   │
│                    (Next.js 14 + TypeScript)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │ Login Page  │  │  Dashboard  │  │  AuthContext (JWT storage)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │
│                            │                                         │
│                    /api/* proxy                                      │
└────────────────────────────┼────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           BACKEND                                    │
│                    (FastAPI + SQLAlchemy)                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      API Routes                               │   │
│  │  /auth/*  │  /sessions/*  │  /stages  │  /admin/*  │ /health │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              FlowEngine + LLM Client + Evaluator              │   │
│  │                                                               │   │
│  │  prompts.py ──► flow_engine.py ──► llm_client.py (Navigator) │   │
│  │                        │                                      │   │
│  │                        ▼                                      │   │
│  │              session_evaluator.py (post-session)              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                            │                                         │
│                            ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   SQLAlchemy Models                           │   │
│  │  Student │ Session │ Message │ SessionSummary │ SafetyIncident│   │
│  │                                                               │   │
│  │  JSONB columns: messages.llm_metadata, sessions.evaluation_data│   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┼────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL 15                                 │
│         students │ sessions │ messages │ session_summaries          │
│                        │ safety_incidents                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Why These Technologies?

| Layer | Technology | Purpose | Why We Chose It |
|-------|------------|---------|-----------------|
| **Frontend** | Next.js 14 | React framework with App Router | Server-side rendering, built-in routing, great DX |
| | TypeScript | Type safety | Catch errors at compile-time, better autocomplete |
| | Tailwind CSS | Utility-first styling | Rapid UI development, consistent design |
| | Axios | HTTP client | Simple API calls with interceptors for auth |
| **Backend** | FastAPI | Async Python web framework | Fast, automatic API docs, modern Python async/await |
| | SQLAlchemy 2.0 | ORM (Object-Relational Mapper) | Write Python objects instead of SQL queries, database-agnostic |
| | Alembic | Database migrations | Version control for database schema changes |
| | Pydantic | Request/response validation | Automatic data validation and serialization |
| | python-jose | JWT token handling | Secure stateless authentication |
| | bcrypt | Password hashing | Industry-standard password security |
| **Database** | PostgreSQL 15 | Relational database | ACID compliance, JSON support, scalability |
| **Infrastructure** | Docker Compose | Container orchestration | One-command setup, consistent environments |

### Key Architecture Decisions

**SQLAlchemy (ORM)**
- **What:** Translates Python objects to database tables
- **Why:** Instead of writing raw SQL, you work with Python classes
- **Example:** `db.query(Student).filter(Student.username == "admin")` vs `SELECT * FROM students WHERE username = 'admin'`
- **Benefit:** Type-safe, IDE autocomplete, database-agnostic (switch from PostgreSQL to MySQL without code changes)

**FastAPI**
- **What:** Modern async Python web framework
- **Why:** Built-in data validation (Pydantic), auto-generated API docs, excellent async support
- **Benefit:** Automatic `/docs` endpoint with interactive API testing

**JWT Authentication**
- **What:** JSON Web Tokens for stateless auth
- **Why:** No server-side session storage needed, works great for APIs
- **How:** User logs in → receives token → includes token in every request

**Docker Compose**
- **What:** Multi-container orchestration
- **Why:** Ensures everyone runs the same PostgreSQL version, Python version, Node version
- **Benefit:** `docker compose up` works identically on Mac, Windows, Linux

---

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Setup Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd AgenticRoboticsEvaluator

# 2. Start all services (builds containers on first run)
cd infra
docker compose up --build

# 3. Open the application (admin user created automatically on first run)
open http://localhost:3000
```

### Default Credentials
- **Username:** `admin`
- **Password:** `admin123`

### Ports
| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend API | 8000 | http://localhost:8000 |
| PostgreSQL | 5433 | localhost:5433 |

---

## Project Structure

```
AgenticRoboticsEvaluator/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py              # Auth and DB dependency injection
│   │   │   └── routes/
│   │   │       ├── auth.py          # Login, get current user
│   │   │       ├── sessions.py      # Create sessions, chat endpoint
│   │   │       ├── stages.py        # Stage registry endpoint
│   │   │       ├── admin.py         # Admin user/session management
│   │   │       └── health.py        # Health check
│   │   │
│   │   ├── core/
│   │   │   ├── config.py            # Environment configuration
│   │   │   ├── prompts.py           # All LLM prompts and stage definitions
│   │   │   └── security.py          # JWT and password hashing
│   │   │
│   │   ├── models/
│   │   │   ├── student.py           # User model
│   │   │   ├── session.py           # Session with evaluation_data JSONB
│   │   │   ├── message.py           # Message with llm_metadata JSONB
│   │   │   ├── session_summary.py   # Not yet used
│   │   │   └── safety_incident.py   # Not yet used
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── student.py
│   │   │   ├── session.py
│   │   │   ├── message.py
│   │   │   └── llm.py               # LLM response validation
│   │   │
│   │   ├── services/
│   │   │   ├── flow_engine.py       # Stage logic and LLM orchestration
│   │   │   ├── llm_client.py        # LLM client (UF Navigator / any OpenAI-compatible API)
│   │   │   └── session_evaluator.py # Post-session evaluation
│   │   │
│   │   └── main.py
│   │
│   ├── alembic/versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_message_metadata.py
│   │   └── 003_add_session_evaluation.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── seed_admin.py
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── login/page.tsx
│   │   │   ├── chat/page.tsx        # Legacy chat page
│   │   │   └── dashboard/
│   │   │       ├── page.tsx         # Main dashboard with chat
│   │   │       └── [sessionId]/inspect/page.tsx  # Session inspector
│   │   │
│   │   ├── components/
│   │   │   ├── MessageCard.tsx      # Chat bubble with metadata toggle
│   │   │   ├── MetadataPanel.tsx    # LLM metadata display
│   │   │   └── StageProgressBar.tsx # Stage progress visualization
│   │   │
│   │   └── lib/
│   │       ├── api.ts
│   │       └── auth-context.tsx
│   │
│   ├── package.json
│   └── Dockerfile
│
├── infra/
│   ├── docker-compose.yml
│   └── .env
│
└── docs/
    ├── SYSTEM.md
    ├── SETUP.md
    └── TASKS_D1.md
```

---

## Key Components Explained

### FlowEngine

Located in `backend/app/services/flow_engine.py`. This orchestrates each turn of conversation:

1. Loads the full conversation history for the session
2. Builds a system prompt from the Prompt Registry using the current stage config
3. Calls the LLM client to get a response
4. Validates the JSON response and extracts the student-facing text
5. Checks the routing signal and advances to the next stage if needed

### Prompt Registry

Located in `backend/app/core/prompts.py`. This is the single source of truth for all LLM instructions. It contains:

- The agent persona and behavioral guidelines
- The JSON response format the LLM must follow
- The STAGE_REGISTRY dictionary with all 7 stages
- The post-session evaluation prompt

Each stage in STAGE_REGISTRY has a goal, system prompt, completion criteria, and max turn count.

### LLM Client

Located in `backend/app/services/llm_client.py`. Wraps LLM API calls (via UF Navigator) with:

- JSON mode to ensure structured responses
- Retry logic with exponential backoff
- Fallback to echo response if all retries fail
- LLMResult object with token usage, response time, and attempt count

### Session Evaluator

Located in `backend/app/services/session_evaluator.py`. Runs one LLM call after a session completes to produce:

- Overall quality score with justification
- Student profile with personal details, communication style, and memory hooks
- Tutor performance analysis
- Recommendations for future sessions

### The 7 Conversation Stages

```
1. greeting            - Build rapport, learn student's name
2. context_gathering   - Understand what they're working on
3. problem_exploration - Dig into specific challenges
4. guided_reflection   - Socratic questioning
5. solution_brainstorm - Explore solutions without giving answers
6. action_planning     - Commit to next steps
7. wrap_up             - Summarize and close
```

### Authentication Flow

```
1. User submits username/password to POST /auth/login
2. Backend validates credentials, returns JWT token
3. Frontend stores token in localStorage
4. All subsequent requests include Authorization: Bearer <token>
5. Backend validates token on each request via dependency injection
```

### Database Models

| Model | Table | Purpose | Status |
|-------|-------|---------|--------|
| Student | students | Users, both students and admins | Used |
| Session | sessions | Chat session with stage tracking and evaluation_data | Used |
| Message | messages | Individual messages with llm_metadata | Used |
| SessionSummary | session_summaries | Structured extraction from sessions | Not used yet |
| SafetyIncident | safety_incidents | Flagged concerning messages | Not used yet |

---

## What's Next

These are the logical next steps:

1. **Safety monitoring** - Run a parallel check on each student message to detect concerning content. The database table exists, needs detection logic.

2. **Session summaries** - Auto-generate a coach-readable summary after each session. The table exists, needs a second post-session LLM call.

3. **Cross-session memory** - Use the student profile from evaluation to seed future sessions so the agent remembers the student.

4. **Admin dashboard** - Build a proper admin interface for viewing all sessions, reading evaluations, and managing users.

5. **Multi-model support** - Add Claude or other providers. The LLM client already accepts a model parameter.

---

## Development Guide

### Running the Application

```bash
# Start all services
cd infra
docker compose up

# Start with rebuild (after code changes to Dockerfile)
docker compose up --build

# Stop all services
docker compose down

# Stop and remove volumes (clears database)
docker compose down -v
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

### Running Tests

```bash
docker compose exec backend pytest -v
```

### Database Access

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U evaluator -d evaluator

# Common queries
SELECT * FROM students;
SELECT * FROM sessions;
SELECT * FROM messages ORDER BY created_at DESC LIMIT 10;
```

### API Documentation

When the backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Hot Reloading

Both frontend and backend support hot reloading:
- **Backend:** Changes to Python files auto-restart uvicorn
- **Frontend:** Next.js fast refresh on file save

---

## Documentation

| Document | Description |
|----------|-------------|
| [SYSTEM.md](docs/SYSTEM.md) | Complete technical specification with data models, API contracts, and architecture decisions |
| [SETUP.md](docs/SETUP.md) | Detailed setup instructions with troubleshooting |
| [TASKS_D1.md](docs/TASKS_D1.md) | Implementation checklist for D1 milestone |

---

## Contributing

1. Create a feature branch from `main`
2. Make changes with clear commit messages
3. Ensure tests pass: `docker compose exec backend pytest`
4. Submit a pull request

---

## License

MIT
