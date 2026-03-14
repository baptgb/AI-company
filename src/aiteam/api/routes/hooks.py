"""AI Team OS — Hooks桥接API路由.

接收Claude Code Hook事件，通过HookTranslator转化为OS系统操作。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from aiteam.api.deps import get_hook_translator
from aiteam.api.hook_translator import HookTranslator

router = APIRouter(prefix="/api/hooks", tags=["hooks"])


@router.post("/event")
async def receive_hook_event(
    payload: dict,
    translator: HookTranslator = Depends(get_hook_translator),
) -> dict:
    """统一接收Claude Code hook事件.

    接收CC的各类hook事件payload，自动同步到OS系统：
    - SubagentStart/Stop: Agent状态同步
    - PreToolUse/PostToolUse: 工具使用追踪
    - SessionStart/End: 会话生命周期管理与对账
    """
    return await translator.handle_event(payload)
