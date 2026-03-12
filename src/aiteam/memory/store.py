"""AI Team OS — 三温度记忆管理.

实现 Hot（内存缓存）/ Warm（SQLite）/ Cold（JSON归档）三层记忆架构。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from aiteam.memory.retriever import build_context_string, keyword_search
from aiteam.types import Memory, MemoryScope

if TYPE_CHECKING:
    from aiteam.storage.repository import StorageRepository


class MemoryStore:
    """三温度记忆管理.

    - Hot层: Python dict 内存缓存，按 scope:scope_id 索引
    - Warm层: 通过 StorageRepository 操作 SQLite
    - Cold层: JSON文件归档
    """

    def __init__(
        self,
        repository: StorageRepository,
        archive_dir: Path | None = None,
    ) -> None:
        self._repo = repository
        self._archive_dir = archive_dir or Path(".aiteam/archive")
        # Hot层缓存: key = "scope:scope_id", value = Memory列表
        self._hot_cache: dict[str, list[Memory]] = {}

    def _cache_key(self, scope: str, scope_id: str) -> str:
        """生成缓存键."""
        return f"{scope}:{scope_id}"

    def _add_to_hot(self, memory: Memory) -> None:
        """将记忆添加到Hot层缓存."""
        key = self._cache_key(memory.scope.value, memory.scope_id)
        if key not in self._hot_cache:
            self._hot_cache[key] = []
        self._hot_cache[key].append(memory)

    def _remove_from_hot(self, memory_id: str) -> bool:
        """从Hot层缓存删除记忆."""
        for key, memories in self._hot_cache.items():
            for i, mem in enumerate(memories):
                if mem.id == memory_id:
                    memories.pop(i)
                    return True
        return False

    async def store(
        self,
        scope: str,
        scope_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> str:
        """存储记忆到Hot层和Warm层，返回memory_id.

        Args:
            scope: 记忆作用域（global/team/agent/user）。
            scope_id: 作用域ID。
            content: 记忆内容。
            metadata: 可选元数据。

        Returns:
            新创建的记忆ID。
        """
        # Warm层: 持久化到SQLite
        memory = await self._repo.create_memory(scope, scope_id, content, metadata)
        # Hot层: 添加到内存缓存
        self._add_to_hot(memory)
        return memory.id

    async def retrieve(
        self,
        scope: str,
        scope_id: str,
        query: str,
        limit: int = 5,
    ) -> list[Memory]:
        """检索相关记忆.

        优先从Hot层检索，不足时回退到Warm层。
        M1阶段使用关键词匹配。

        Args:
            scope: 记忆作用域。
            scope_id: 作用域ID。
            query: 搜索查询。
            limit: 最大返回数量。

        Returns:
            相关记忆列表。
        """
        key = self._cache_key(scope, scope_id)

        # 先查Hot层
        hot_memories = self._hot_cache.get(key, [])
        if hot_memories:
            results = keyword_search(hot_memories, query)
            if len(results) >= limit:
                return results[:limit]

        # Hot层不够，查Warm层
        warm_results = await self._repo.search_memories(scope, scope_id, query, limit)

        # 合并去重（以memory_id去重）
        seen_ids: set[str] = set()
        merged: list[Memory] = []

        # Hot层结果优先
        if hot_memories:
            for mem in keyword_search(hot_memories, query):
                if mem.id not in seen_ids:
                    seen_ids.add(mem.id)
                    merged.append(mem)

        # 补充Warm层结果
        for mem in warm_results:
            if mem.id not in seen_ids:
                seen_ids.add(mem.id)
                merged.append(mem)

        return merged[:limit]

    async def get_context(self, agent_id: str, task: str) -> str:
        """为Agent构建上下文字符串.

        检索agent记忆 + team记忆 + global记忆，拼接为上下文字符串。

        Args:
            agent_id: Agent的ID。
            task: 当前任务描述（用作检索查询）。

        Returns:
            格式化后的上下文字符串。
        """
        all_memories: list[Memory] = []

        # 检索agent级别记忆
        agent_memories = await self.retrieve(
            MemoryScope.AGENT.value, agent_id, task, limit=5
        )
        all_memories.extend(agent_memories)

        # 检索global级别记忆
        global_memories = await self.retrieve(
            MemoryScope.GLOBAL.value, "system", task, limit=3
        )
        all_memories.extend(global_memories)

        return build_context_string(all_memories)

    async def list_all(self, scope: str, scope_id: str) -> list[Memory]:
        """列出指定作用域的所有记忆.

        Args:
            scope: 记忆作用域。
            scope_id: 作用域ID。

        Returns:
            该作用域下的所有记忆列表。
        """
        return await self._repo.list_memories(scope, scope_id)

    async def delete(self, memory_id: str) -> bool:
        """从Hot层和Warm层删除记忆.

        Args:
            memory_id: 要删除的记忆ID。

        Returns:
            是否删除成功。
        """
        # 从Hot层删除
        self._remove_from_hot(memory_id)
        # 从Warm层删除
        return await self._repo.delete_memory(memory_id)

    async def archive(self, scope: str, scope_id: str) -> Path:
        """将Warm层记忆导出为JSON文件存到Cold层.

        Args:
            scope: 记忆作用域。
            scope_id: 作用域ID。

        Returns:
            归档文件路径。
        """
        # 获取Warm层所有记忆
        memories = await self._repo.list_memories(scope, scope_id)

        # 构建归档目录
        archive_path = self._archive_dir / scope / scope_id
        archive_path.mkdir(parents=True, exist_ok=True)

        # 生成归档文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = archive_path / f"{timestamp}.json"

        data = [
            {
                "id": mem.id,
                "scope": mem.scope.value,
                "scope_id": mem.scope_id,
                "content": mem.content,
                "metadata": mem.metadata,
                "created_at": mem.created_at.isoformat(),
                "accessed_at": mem.accessed_at.isoformat(),
            }
            for mem in memories
        ]

        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return file_path
