"""AI Team OS — 数据分析统计路由."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from aiteam.api.deps import get_repository
from aiteam.storage.repository import StorageRepository

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/tool-usage")
async def get_tool_usage(
    team_id: str | None = Query(None),
    repo: StorageRepository = Depends(get_repository),
) -> dict[str, Any]:
    """工具使用分布统计."""
    data = await repo.count_activities_by_tool(team_id=team_id)
    return {"success": True, "data": data}


@router.get("/agent-productivity")
async def get_agent_productivity(
    team_id: str | None = Query(None),
    repo: StorageRepository = Depends(get_repository),
) -> dict[str, Any]:
    """Agent产能指标."""
    data = await repo.get_agent_productivity(team_id=team_id)
    return {"success": True, "data": data}


@router.get("/timeline")
async def get_activity_timeline(
    team_id: str | None = Query(None),
    hours: int = Query(24, ge=1, le=168),
    repo: StorageRepository = Depends(get_repository),
) -> dict[str, Any]:
    """活动时间线（按小时聚合）."""
    data = await repo.get_activity_timeline(team_id=team_id, hours=hours)
    return {"success": True, "data": data}


@router.get("/team-overview")
async def get_team_overview(
    team_id: str = Query(...),
    repo: StorageRepository = Depends(get_repository),
) -> dict[str, Any]:
    """团队整体统计概览."""
    # 工具分布
    tool_dist = await repo.count_activities_by_tool(team_id=team_id)

    # Agent产能
    productivity = await repo.get_agent_productivity(team_id=team_id)

    # 活跃Agent数
    agents = await repo.list_agents(team_id)
    active_agents = [a for a in agents if a.status.value == "busy"]

    # 总活动数
    total_activities = sum(p["activity_count"] for p in productivity)

    return {
        "success": True,
        "data": {
            "total_activities": total_activities,
            "total_agents": len(agents),
            "active_agents": len(active_agents),
            "tool_distribution": tool_dist,
            "agent_productivity": productivity,
        },
    }
