# AI Team OS — Quickstart Guide

Two ways to run the project locally:

- **Option A — Simple (SQLite, no Docker):** fastest way to get started, no database setup needed
- **Option B — Full Stack (Docker, PostgreSQL + Redis):** production-grade, all services in containers

---

## Prerequisites

| Tool | Minimum Version | Notes |
|------|-----------------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 20+ | `node --version` |
| npm | 9+ | bundled with Node.js |
| Docker + Compose | v2 | Option B only |

---

## Option A — Simple Local Setup (SQLite)

This uses SQLite as the database (auto-created on first run). No Docker required.

### 1. Clone and enter the repo

```bash
git clone <your-repo-url>
cd ai-team-os
```

### 2. Copy and edit environment variables

```bash
cp .env.example .env
```

Open `.env` and set your Anthropic API key:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

> The DATABASE_URL and REDIS_URL lines can be left as-is — SQLite is used by default when PostgreSQL is not available.

### 3. Install Python dependencies

```bash
pip install -e ".[full]"
```

### 4. Install frontend dependencies

```bash
cd dashboard
npm install
cd ..
```

### 5. Start the backend API

In one terminal:

```bash
uvicorn aiteam.api.app:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.
API docs (Swagger): `http://localhost:8000/docs`

### 6. Start the frontend dashboard

In a second terminal:

```bash
cd dashboard
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

> The Vite dev server proxies `/api` and `/ws` requests to the backend at port 8000, so there are no CORS issues.

---

## Option B — Full Docker Setup (PostgreSQL + Redis)

Runs everything in containers — the API, dashboard (served by the API), PostgreSQL, and Redis.

### 1. Clone and enter the repo

```bash
git clone <your-repo-url>
cd ai-team-os
```

### 2. Copy and edit environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here

POSTGRES_USER=aiteam
POSTGRES_PASSWORD=aiteam_dev
POSTGRES_DB=aiteam
DATABASE_URL=postgresql+asyncpg://aiteam:aiteam_dev@localhost:5432/aiteam

REDIS_URL=redis://localhost:6379/0
```

### 3. Build and start all services

```bash
docker compose -f docker-compose.full.yml up --build
```

Or run in the background:

```bash
docker compose -f docker-compose.full.yml up --build -d
```

Once running:

| Service | URL |
|---------|-----|
| Dashboard + API | `http://localhost:8000` |
| API Docs (Swagger) | `http://localhost:8000/docs` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

### 4. Stopping and cleanup

```bash
# Stop services
docker compose -f docker-compose.full.yml down

# Stop and remove all data volumes
docker compose -f docker-compose.full.yml down -v
```

---

## Option C — Infrastructure Only (Docker for DB + Redis, local app)

Use this if you want PostgreSQL + Redis in Docker but run the Python/Node processes locally (good for development with hot reload).

### 1. Start only the infrastructure

```bash
docker compose up -d
```

This starts just PostgreSQL and Redis (the original `docker-compose.yml`).

### 2. Follow Option A steps 3–6

Make sure your `.env` points to the containerized database:

```env
DATABASE_URL=postgresql+asyncpg://aiteam:aiteam_dev@localhost:5432/aiteam
REDIS_URL=redis://localhost:6379/0
```

---

## Configuration

The app looks for an `aiteam.yaml` file in the current directory (or any parent directory). Create one to configure your project:

```yaml
# aiteam.yaml
project:
  name: "my-project"
  description: "My AI team project"
  language: "en"   # or "zh"

defaults:
  model: "claude-opus-4-6"
  max_context_ratio: 0.8

infrastructure:
  storage_backend: "sqlite"      # "sqlite" or "postgresql"
  memory_backend: "file"         # "file" or "mem0"
  cache_backend: "memory"        # "memory" or "redis"
  api_port: 8000
```

---

## Claude Code Integration (MCP)

AI Team OS is designed to work as an MCP server inside Claude Code. After the API is running, add it to your Claude Code config (`~/.claude/claude_desktop_config.json` or `.mcp.json`):

```json
{
  "mcpServers": {
    "aiteam": {
      "command": "ai-team-os-serve",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-your-key-here"
      }
    }
  }
}
```

See `README.md` and the `plugin/` directory for full agent configuration templates.

---

## Troubleshooting

**Port already in use**
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9
```

**Python version issues**
```bash
# Use pyenv or conda to switch to Python 3.11+
python3.11 -m pip install -e ".[full]"
python3.11 -m uvicorn aiteam.api.app:create_app --factory --host 0.0.0.0 --port 8000
```

**Database migration errors (PostgreSQL)**
```bash
# Run migrations manually after starting the database
alembic upgrade head
```

**Frontend can't reach the backend**

Make sure the backend is running on port 8000 before starting the frontend. The Vite dev server proxies API calls automatically — no environment variable changes needed for local development.
