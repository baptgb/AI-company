"""AI Team OS CLI — TeamManager 工厂函数.

提供延迟初始化的 TeamManager 实例，供所有CLI命令使用。
"""

from __future__ import annotations

import asyncio
from typing import Any

_manager_instance: Any = None


def run_async(coro: Any) -> Any:
    """在同步CLI环境中运行异步协程."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # 已有事件循环运行中（如Jupyter），使用nest_asyncio或新线程
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def get_manager() -> Any:
    """获取 TeamManager 实例（延迟初始化）.

    内部创建 StorageRepository + MemoryStore + TeamManager。
    由于这些模块可能尚未实现，用 try/except 包裹。

    Returns:
        TeamManager 实例

    Raises:
        RuntimeError: 如果依赖模块尚未实现
    """
    global _manager_instance  # noqa: PLW0603

    if _manager_instance is not None:
        return _manager_instance

    try:
        from aiteam.memory.store import MemoryStore
        from aiteam.orchestrator.team_manager import TeamManager
        from aiteam.storage.repository import StorageRepository

        repo = StorageRepository()
        run_async(repo.init_db())
        memory = MemoryStore(repository=repo)
        _manager_instance = TeamManager(repository=repo, memory=memory)
        return _manager_instance

    except ImportError as e:
        raise RuntimeError(
            f"依赖模块尚未实现: {e}。"
            "请确保 storage、memory、orchestrator 模块已正确安装。"
        ) from e
