# Agentic Robotics Evaluator - Setup Guide

This guide walks you through setting up and running the D1 Foundation MVP.

## Prerequisites

- **Docker Desktop** (includes Docker & Docker Compose)
  - macOS: `brew install --cask docker`
  - Or download from https://docker.com/products/docker-desktop

- **Git** (to clone the repository)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AgenticRoboticsEvaluator
```

### 2. Environment Setup

Copy the example environment files:

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` with your settings:
```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/evaluator
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

> ⚠️ **Important**: Change `SECRET_KEY` to a secure random string in production!

### 3. Start the Application

Build and start all services:

```bash
cd infra
docker compose up --build
```

This will:
- Start PostgreSQL on port 5432
- Start the FastAPI backend on port 8000
- Start the Next.js frontend on port 3000

Wait for all services to be ready. You should see:
```
backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000
frontend-1  | ▲ Next.js 14.x.x
frontend-1  | - Local: http://localhost:3000
```

### 4. Run Database Migrations

In a new terminal, run:

```bash
docker compose exec backend alembic upgrade head
```

### 5. Create Admin User

```bash
docker compose exec backend python seed_admin.py admin admin123
```

This creates an admin account:
- Username: `admin`
- Password: `admin123`

> ⚠️ **Important**: Change the admin password in production!

## Verification Workflow

### Step 1: Verify Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok"}
```

### Step 2: Login as Admin

Open your browser to http://localhost:3000/login

Login with:
- Username: `admin`
- Password: `admin123`

You should see the chat page (admin can view but not create sessions).

### Step 3: Create a Student Account

Using curl or an API client:

```bash
# Get admin token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Create student
curl -X POST http://localhost:8000/admin/students \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "username": "student1",
    "password": "student123",
    "display_name": "Test Student",
    "pronouns": "they/them",
    "tone_pref": "friendly"
  }'
```

### Step 4: Login as Student

1. Go to http://localhost:3000/login
2. Login with `student1` / `student123`
3. You should be redirected to the chat page

### Step 5: Start a Reflection Session

1. Type a message in the chat input
2. Press Send or Enter
3. You should see:
   - Your message (right-aligned, blue)
   - Assistant reply (left-aligned, gray)
4. Try typing "next" to advance stages
5. The stage indicator in the header should update

### Step 6: Verify Data Persistence

1. Refresh the page - your messages should still be there
2. Check the database:

```bash
docker compose exec postgres psql -U postgres -d evaluator -c "SELECT * FROM messages;"
```

## Development Commands

### View Logs
```bash
docker compose logs -f backend
docker compose logs -f frontend
```

### Run Backend Tests
```bash
docker compose exec backend pytest -v
```

### Access Database
```bash
docker compose exec postgres psql -U postgres -d evaluator
```

Useful queries:
```sql
-- List all students
SELECT id, username, role, display_name FROM students;

-- List all sessions
SELECT id, student_id, status, current_stage FROM sessions;

-- List messages for a session
SELECT id, role, content, stage_id FROM messages WHERE session_id = 1 ORDER BY created_at;
```

### Stop Services
```bash
docker compose down
```

### Reset Everything (including database)
```bash
docker compose down -v
docker compose up --build
```

## Troubleshooting

### "Connection refused" errors
- Ensure Docker is running
- Wait for all services to start (can take 30-60 seconds)
- Check logs: `docker compose logs`

### Database migration fails
- Ensure PostgreSQL is fully started before running migrations
- Try: `docker compose exec backend alembic upgrade head`

### Frontend can't connect to backend
- Check that backend is running on port 8000
- The Next.js rewrite proxy should forward `/api/*` to the backend

### "Invalid token" errors
- Token may have expired (8 hour default)
- Log out and log in again
- Clear localStorage in browser dev tools

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Next.js        │────▶│  FastAPI        │────▶│  PostgreSQL     │
│  Frontend       │     │  Backend        │     │  Database       │
│  :3000          │     │  :8000          │     │  :5432          │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- **Frontend**: React UI with Tailwind CSS, handles auth state
- **Backend**: REST API with JWT auth, manages sessions & messages
- **Database**: Stores users, sessions, messages, summaries

## Next Steps (D2)

After D1 is verified working, D2 will add:
- LLM integration (replace placeholder responses)
- Safety guardrails
- Stage-specific prompting
- Session summaries
- Enhanced UI components
