"""AI Team OS — Hooks桥接API路由.

接收Claude Code Hook事件，通过HookTranslator转化为OS系统操作。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from aiteam.api.deps import get_hook_translator
from aiteam.api.hook_translator import HookTranslator

router = APIRouter(prefix="/api/hooks", tags=["hooks"])


class HookEventPayload(BaseModel):
    """Claude Code Hook事件payload schema."""

    hook_event_name: str = Field(default="", max_length=50)
    session_id: str = Field(default="", max_length=200)
    agent_id: str = Field(default="", max_length=200)
    agent_type: str = Field(default="", max_length=200)
    tool_name: str = Field(default="", max_length=100)
    tool_input: dict = Field(default_factory=dict)
    tool_output: dict = Field(default_factory=dict)
    cwd: str = Field(default="", max_length=500)
    cc_team_name: str = Field(default="", max_length=200)

    model_config = ConfigDict(extra="allow")


@router.post("/event")
async def receive_hook_event(
    payload: HookEventPayload,
    translator: HookTranslator = Depends(get_hook_translator),
) -> dict:
    """统一接收Claude Code hook事件.

    接收CC的各类hook事件payload，自动同步到OS系统：
    - SubagentStart/Stop: Agent状态同步
    - PreToolUse/PostToolUse: 工具使用追踪
    - SessionStart/End: 会话生命周期管理与对账
    """
    return await translator.handle_event(payload.model_dump())
