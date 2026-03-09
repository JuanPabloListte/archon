# Archon — AI System Auditor

Archon is a SaaS backend that audits AI-adjacent backend systems for security, API design, and database hygiene issues. It uses rule-based static analysis, RAG-powered semantic search, and LLM agents (via Ollama) to produce actionable audit reports.

## Stack

- **FastAPI** — REST API
- **SQLModel + PostgreSQL** — ORM and primary database
- **pgvector** — Vector similarity search for RAG
- **Redis + Celery** — Background task queue
- **Sentence Transformers** — Local embeddings (`nomic-embed-text-v1`)
- **Ollama** — Local LLM inference (`llama3`)
- **Alembic** — Database migrations

## Project Structure

```
archon/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── config.py          # Settings via pydantic-settings
│   │   ├── database.py        # SQLModel engine and session
│   │   ├── api/v1/            # REST endpoints (auth, projects, connections, audits, reports, chat)
│   │   ├── models/db.py       # SQLModel table definitions
│   │   ├── core/security.py   # JWT + bcrypt auth
│   │   ├── services/          # OpenAPI parser, DB analyzer
│   │   ├── audit/             # Rule engine + audit rules (API, database, security)
│   │   ├── rag/               # Embeddings indexing + vector retrieval
│   │   ├── agents/            # LLM agents (query, auditor, advisor)
│   │   ├── reports/           # Health score + report generation
│   │   └── workers/           # Celery app + async tasks
│   ├── alembic/               # Database migration scripts
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
└── docker-compose.yml
```

## Quickstart

### Prerequisites

- Docker and Docker Compose
- [Ollama](https://ollama.com) running locally with `llama3` and `nomic-embed-text` models pulled

### 1. Pull Ollama models

```bash
ollama pull llama3
ollama pull nomic-embed-text
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env as needed
```

### 3. Start services

```bash
docker compose up --build
```

This starts:
- PostgreSQL with pgvector on port 5432
- Redis on port 6379
- FastAPI backend on port 8000
- Celery worker (ingestion, audit, reports queues)

### 4. Run database migrations (first time)

```bash
docker compose exec backend alembic upgrade head
```

### 5. Access the API

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Development (without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up PostgreSQL with pgvector and Redis locally, then:
cp .env.example .env
# Edit .env with your local connection strings

alembic upgrade head
uvicorn app.main:app --reload
```

Run Celery worker separately:

```bash
celery -A app.workers.celery_app worker --loglevel=info -Q ingestion,audit,reports
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login, get JWT token |
| GET/POST | `/api/v1/projects` | List / create projects |
| GET/DELETE | `/api/v1/projects/{id}` | Get / delete project |
| POST | `/api/v1/connections` | Add OpenAPI or database connection |
| GET | `/api/v1/connections/project/{id}` | List project connections |
| POST | `/api/v1/audits/run/{project_id}` | Trigger audit (async) |
| GET | `/api/v1/audits/findings/{project_id}` | Get audit findings |
| GET | `/api/v1/reports/{project_id}` | List reports |
| GET | `/api/v1/reports/{project_id}/latest` | Get latest report |
| POST | `/api/v1/chat` | Ask questions about your system (RAG + LLM) |

## Audit Rules

### API Rules
- **Missing Auth**: Flags POST/PUT/PATCH/DELETE endpoints without authentication
- **Wrong Verb**: Flags GET endpoints with creation/deletion path keywords
- **Duplicate Endpoint**: Detects duplicate method+path combinations

### Database Rules
- **Missing Index**: Foreign key columns without indexes, large tables without any index
- **Sensitive Column**: Detects plain-text sensitive columns (passwords, tokens, SSNs, etc.)

### Security Rules
- **Sensitive Response**: API responses that expose sensitive fields (password, token, API key, etc.)

## Health Score

Reports include a 0–100 health score:
- Critical finding: -25 points
- High finding: -15 points
- Medium finding: -8 points
- Low finding: -3 points
- Info finding: -1 point
