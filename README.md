# Archon — AI System Auditor

Archon is an AI-powered SaaS platform that audits backend systems. It analyzes REST APIs and databases, detects security and performance issues using rule-based analysis combined with AI reasoning, and generates technical reports with health scores.

![License](https://img.shields.io/badge/license-MIT-blue) ![Python](https://img.shields.io/badge/python-3.11-blue) ![Next.js](https://img.shields.io/badge/next.js-14-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)

---

## Features

- **Multi-source ingestion** — connect via OpenAPI/Swagger URL or database connection string
- **Rule-based audit engine** — deterministic checks for auth, HTTP verbs, SQL, security patterns
- **AI review pass** — post-audit AI layer that filters false positives, adjusts severity, and detects issues rules can't see
- **RAG-powered AI Chat** — ask natural language questions about your system using context retrieved from the audit
- **Health score** — weighted 0–100 score per project based on finding severity
- **Reports** — full JSON reports with findings breakdown by severity and category
- **Multi-provider AI** — bring your own key: Claude, ChatGPT, Gemini, Groq, Mistral, Ollama, or any OpenAI-compatible API
- **Google OAuth** — sign in with Google or email/password
- **Per-user encrypted credentials** — API keys stored encrypted with Fernet (AES-128)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + SQLModel + PostgreSQL 16 + pgvector |
| Frontend | Next.js 14 (App Router) + Tailwind CSS + TypeScript |
| Queue | Celery + Redis |
| Embeddings | SentenceTransformers (`nomic-embed-text-v1`) + pgvector |
| AI (default) | Ollama — bring your own model |
| Auth | JWT (HS256) + Google OAuth 2.0 |

---

## Project Structure

```
archon/
├── backend/
│   ├── app/
│   │   ├── api/v1/             # auth, users, projects, connections, audits, reports, chat, credentials
│   │   ├── audit/
│   │   │   ├── engine.py       # audit orchestrator
│   │   │   ├── ai_reviewer.py  # AI post-audit pass
│   │   │   └── rules/          # api/, database/, security/
│   │   ├── agents/             # query_agent, auditor_agent, advisor_agent
│   │   ├── core/               # security (JWT), crypto (Fernet)
│   │   ├── models/db.py        # SQLModel table definitions
│   │   ├── rag/                # embeddings.py, retriever.py (pgvector)
│   │   ├── reports/            # generator.py (health score + JSON)
│   │   ├── services/           # openapi_parser, db_analyzer, ai_client
│   │   └── workers/            # celery_app.py, tasks.py
│   ├── alembic/                # DB migrations
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── (auth)/         # login, register, OAuth callback
│       │   └── (dashboard)/    # dashboard, projects, findings, report, chat, credentials
│       ├── components/         # UI, layout, chat, findings
│       └── lib/                # api.ts, auth.ts, i18n.tsx, theme.tsx
└── docker-compose.yml
```

---

## Audit Rules

| Rule | Category | Severity |
|---|---|---|
| Endpoint missing authentication | API | High |
| Wrong HTTP verb for operation | API | Medium |
| Duplicate endpoint paths | API | Low |
| Missing index on FK / large table | Database | Medium / High |
| Sensitive column names exposed | Database | High |
| Sensitive data in API responses | Security | High |

After rules run, the **AI review pass** uses the active user credential to:
- Dismiss false positives (e.g. missing index on a 3-row table)
- Adjust severity based on context (e.g. unprotected `/admin` → Critical)
- Add new findings the rules can't detect (e.g. missing rate limiting, insecure naming patterns)

AI-detected findings are marked with an **✦ AI detected** badge in the UI.

---

## Health Score

```
score = 100 - Σ(severity_weight × finding_count)

critical = 25 pts
high     = 15 pts
medium   =  8 pts
low      =  3 pts
info     =  1 pt

Score ≥ 80 → LOW risk
Score ≥ 60 → MEDIUM risk
Score ≥ 40 → HIGH risk
Score  < 40 → CRITICAL risk
```

---

## Getting Started

### Prerequisites

- Docker + Docker Compose
- Node.js 18+
- Python 3.11+
- (Optional) Ollama for local AI — [ollama.ai](https://ollama.ai)

### 1. Clone the repo

```bash
git clone https://github.com/your-username/archon.git
cd archon
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
DATABASE_URL=postgresql://archon:archon@localhost:5433/archon
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-long-random-secret-key

# Optional: Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### 3. Start infrastructure

```bash
docker-compose up db redis -d
```

### 4. Run backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

alembic upgrade head
uvicorn app.main:app --reload
```

### 5. Run frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 6. (Optional) Start Celery worker

```bash
cd backend
celery -A app.workers.celery_app worker --loglevel=info -Q ingestion,audit,reports
```

> Without the Celery worker, ingestion and audit tasks run synchronously.

---

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (Web application)
3. Add to **Authorized redirect URIs**: `http://localhost:8000/api/v1/auth/google/callback`
4. Add to **Authorized JavaScript origins**: `http://localhost:8000`
5. Copy Client ID and Secret to `backend/.env`

---

## AI Configuration

Archon supports any AI provider. Go to **Credentials** in the app to add yours:

| Provider | Key prefix | Notes |
|---|---|---|
| Anthropic (Claude) | `sk-ant-` | Auto-detected from key |
| OpenAI (ChatGPT) | `sk-` | Auto-detected from key |
| Google (Gemini) | `AIza` | Auto-detected from key |
| Groq | `gsk_` | Auto-detected from key |
| Mistral | — | |
| Ollama | — | Requires base URL, no key needed |
| Custom | — | Any OpenAI-compatible API |

Models are fetched live from each provider's API when you enter your key. The **active** credential is used for the AI audit review and AI Chat. Without an active credential, audits run rule-based only and the chat is disabled.

---

## API Reference

Interactive docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Main endpoints

```
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/google
GET  /api/v1/auth/google/callback

GET  /api/v1/projects
POST /api/v1/projects
GET  /api/v1/projects/{id}

POST /api/v1/connections
POST /api/v1/audits/run/{project_id}/stream   # SSE stream
GET  /api/v1/audits/findings/{project_id}

POST /api/v1/chat/stream                      # SSE stream

GET  /api/v1/credentials
POST /api/v1/credentials
POST /api/v1/credentials/{id}/activate
POST /api/v1/credentials/models               # fetch live models from provider
```

---

## Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Mark existing tables as migrated (first run on existing DB)
alembic stamp 001
alembic upgrade head
```

---

## Full Docker Stack

```bash
docker-compose up --build
```

| Service | Port |
|---|---|
| PostgreSQL 16 + pgvector | 5433 |
| Redis 7 | 6379 |
| FastAPI backend | 8000 |
| Celery worker | — |

---

## License

MIT
