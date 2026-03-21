"""AI Team OS — Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check() -> dict:
    """Simple health check — returns status and version."""
    return {"status": "ok", "version": "1.0.0"}
