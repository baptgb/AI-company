# AI Team OS

## Overview
AI Team OS is a "self-driving AI company" operating system designed to enhance Claude Code with a structured, persistent, and autonomous multi-agent environment. It enables a hierarchy of AI agents (CEO, Tech Lead, Developers, etc.) to collaborate on projects, manage a task wall, hold structured meetings, and learn from failures.

## Architecture

### Backend (FastAPI + Python)
- **Framework:** FastAPI with uvicorn ASGI server
- **Package Manager:** pip (installed with `pip install -e ".[full]"`)
- **Database:** SQLite (default, via aiosqlite) or PostgreSQL (optional via asyncpg)
- **Orchestration:** LangGraph StateGraph for agent workflows
- **MCP Protocol:** fastmcp for Claude Code integration
- **Port:** 8000 (console workflow)

### Frontend (React + Vite)
- **Framework:** React 19 + TypeScript
- **Build Tool:** Vite 7
- **UI:** Shadcn UI + Tailwind CSS 4
- **State:** Zustand + TanStack Query
- **Real-time:** WebSockets
- **Port:** 5000 (webview workflow)

## Project Structure
- `src/aiteam/` — Core Python package
  - `api/` — FastAPI app, routes, WebSocket manager
  - `mcp/` — MCP server (60+ tools for Claude Code)
  - `loop/` — Autonomous engine (watchdog, auto-assignment)
  - `orchestrator/` — Team management, LangGraph workflows
  - `memory/` — RAG/memory backends
  - `storage/` — SQLAlchemy models and repositories
  - `config/` — Settings (loads from `aiteam.yaml`)
  - `cli/` — Typer CLI (`aiteam` command)
- `dashboard/` — React frontend SPA
- `plugin/` — Claude Code agent templates, meeting configs
- `hooks/` — Claude Code hook scripts (PreToolUse, SessionStart, etc.)
- `migrations/` — Alembic DB migrations

## Workflows
- **Start application** — `cd dashboard && npm run dev` on port 5000 (webview)
- **Backend API** — `uvicorn aiteam.api.app:create_app --factory --host 0.0.0.0 --port 8000` (console)

## Vite Proxy
The Vite dev server proxies `/api` and `/ws` paths to the backend at `http://localhost:8000`, so the frontend uses relative URLs for API calls.

## Key Configuration
- `aiteam.yaml` — Project config file (searched upward from CWD)
- `.env` — Environment variables (copy from `.env.example`)
- Default storage: SQLite at `.aiteam/aiteam.db`
- Default model: `claude-opus-4-6`

## Deployment
- Target: VM (always-running, needed for WebSockets)
- Build: `cd dashboard && npm run build`
- Run: `uvicorn aiteam.api.app:create_app --factory --host 0.0.0.0 --port 5000`
- The backend serves the built frontend static files in production
