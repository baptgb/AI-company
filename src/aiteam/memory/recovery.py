"""AI Team OS — 上下文恢复管理.

提供检查点创建、恢复和清理功能，用于Agent上下文耗尽时的状态恢复。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class ContextRecovery:
    """上下文耗尽时的恢复机制.

    通过JSON文件保存Agent状态快照，支持断点恢复。
    """

    def __init__(self, checkpoint_dir: Path | None = None) -> None:
        self._checkpoint_dir = checkpoint_dir or Path(".aiteam/checkpoints")

    async def create_checkpoint(self, agent_id: str, state: dict) -> str:
        """创建检查点，保存状态快照为JSON文件.

        Args:
            agent_id: Agent的ID。
            state: 要保存的状态字典。

        Returns:
            checkpoint_id。
        """
        checkpoint_id = str(uuid4())
        timestamp = datetime.now().isoformat()

        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "agent_id": agent_id,
            "state": state,
            "timestamp": timestamp,
        }

        # 确保目录存在
        agent_dir = self._checkpoint_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        file_path = agent_dir / f"{checkpoint_id}.json"
        file_path.write_text(
            json.dumps(checkpoint_data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        return checkpoint_id

    async def restore_checkpoint(self, checkpoint_id: str) -> dict:
        """从JSON文件恢复检查点状态.

        Args:
            checkpoint_id: 要恢复的检查点ID。

        Returns:
            恢复的状态字典。

        Raises:
            FileNotFoundError: 检查点文件不存在。
        """
        # 遍历所有agent目录查找checkpoint文件
        if not self._checkpoint_dir.exists():
            msg = f"检查点 {checkpoint_id} 不存在"
            raise FileNotFoundError(msg)

        for agent_dir in self._checkpoint_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            file_path = agent_dir / f"{checkpoint_id}.json"
            if file_path.exists():
                data = json.loads(file_path.read_text(encoding="utf-8"))
                return data

        msg = f"检查点 {checkpoint_id} 不存在"
        raise FileNotFoundError(msg)

    async def list_checkpoints(self, agent_id: str) -> list[dict]:
        """列出Agent的所有检查点（按时间排序）.

        Args:
            agent_id: Agent的ID。

        Returns:
            检查点信息列表，按时间升序排列。
        """
        agent_dir = self._checkpoint_dir / agent_id
        if not agent_dir.exists():
            return []

        checkpoints: list[dict] = []
        for file_path in agent_dir.glob("*.json"):
            data = json.loads(file_path.read_text(encoding="utf-8"))
            checkpoints.append({
                "checkpoint_id": data["checkpoint_id"],
                "agent_id": data["agent_id"],
                "timestamp": data["timestamp"],
            })

        # 按时间升序排列
        checkpoints.sort(key=lambda x: x["timestamp"])
        return checkpoints

    async def cleanup_old_checkpoints(
        self, agent_id: str, keep_latest: int = 5
    ) -> int:
        """只保留最新N个检查点，删除旧的.

        Args:
            agent_id: Agent的ID。
            keep_latest: 保留最新的检查点数量。

        Returns:
            删除的检查点数量。
        """
        agent_dir = self._checkpoint_dir / agent_id
        if not agent_dir.exists():
            return 0

        # 读取所有检查点并按时间排序
        files_with_time: list[tuple[str, Path]] = []
        for file_path in agent_dir.glob("*.json"):
            data = json.loads(file_path.read_text(encoding="utf-8"))
            files_with_time.append((data.get("timestamp", ""), file_path))

        # 按时间降序排列（最新的在前）
        files_with_time.sort(key=lambda x: x[0], reverse=True)

        # 删除超出保留数量的旧检查点
        deleted = 0
        for _, file_path in files_with_time[keep_latest:]:
            file_path.unlink()
            deleted += 1

        return deleted
