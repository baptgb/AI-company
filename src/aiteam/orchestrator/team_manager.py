"""AI Team OS — TeamManager 团队管理器.

所有团队操作的统一入口，CLI和API都通过此接口操作。
负责团队CRUD、Agent管理、任务执行和状态查询。
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from aiteam.orchestrator.graph_compiler import compile_graph
from aiteam.storage.repository import StorageRepository
from aiteam.types import (
    Agent,
    OrchestrationMode,
    Task,
    TaskResult,
    TaskStatus,
    Team,
    TeamStatus,
)


class TeamManager:
    """团队管理器 — 所有团队操作的统一入口."""

    def __init__(
        self,
        repository: StorageRepository,
        memory: Any | None = None,
    ) -> None:
        """初始化TeamManager.

        Args:
            repository: 数据持久化仓库。
            memory: 可选的MemoryStore实例（开发中，可为None）。
        """
        self._repo = repository
        self._memory = memory

    # ================================================================
    # 团队管理
    # ================================================================

    async def create_team(
        self,
        name: str,
        mode: str = "coordinate",
        config: dict | None = None,
    ) -> Team:
        """创建团队.

        Args:
            name: 团队名称。
            mode: 编排模式，默认coordinate。
            config: 可选的团队配置。

        Returns:
            创建的Team对象。
        """
        # 验证模式合法性
        OrchestrationMode(mode)
        return await self._repo.create_team(name=name, mode=mode, config=config)

    async def get_team(self, name_or_id: str) -> Team:
        """根据名称或ID获取团队.

        Args:
            name_or_id: 团队名称或ID。

        Returns:
            Team对象。

        Raises:
            ValueError: 团队不存在时。
        """
        # 先按名称查找
        team = await self._repo.get_team_by_name(name_or_id)
        if team is not None:
            return team
        # 再按ID查找
        team = await self._repo.get_team(name_or_id)
        if team is not None:
            return team
        msg = f"团队 '{name_or_id}' 不存在"
        raise ValueError(msg)

    async def list_teams(self) -> list[Team]:
        """列出所有团队."""
        return await self._repo.list_teams()

    async def delete_team(self, name_or_id: str) -> bool:
        """删除团队.

        Args:
            name_or_id: 团队名称或ID。

        Returns:
            是否成功删除。
        """
        team = await self.get_team(name_or_id)
        return await self._repo.delete_team(team.id)

    async def set_mode(self, name_or_id: str, mode: str) -> Team:
        """设置团队编排模式.

        Args:
            name_or_id: 团队名称或ID。
            mode: 新的编排模式。

        Returns:
            更新后的Team对象。
        """
        team = await self.get_team(name_or_id)
        OrchestrationMode(mode)
        return await self._repo.update_team(team.id, mode=mode)

    # ================================================================
    # Agent管理
    # ================================================================

    async def add_agent(
        self,
        team_name: str,
        name: str,
        role: str,
        system_prompt: str = "",
        model: str = "claude-opus-4-6",
    ) -> Agent:
        """向团队添加Agent.

        Args:
            team_name: 团队名称。
            name: Agent名称。
            role: Agent角色。
            system_prompt: 系统提示词。
            model: 使用的模型ID。

        Returns:
            创建的Agent对象。
        """
        team = await self.get_team(team_name)
        return await self._repo.create_agent(
            team_id=team.id,
            name=name,
            role=role,
            system_prompt=system_prompt,
            model=model,
        )

    async def remove_agent(self, team_name: str, agent_name: str) -> bool:
        """从团队移除Agent.

        Args:
            team_name: 团队名称。
            agent_name: Agent名称。

        Returns:
            是否成功移除。
        """
        team = await self.get_team(team_name)
        agents = await self._repo.list_agents(team.id)
        for agent in agents:
            if agent.name == agent_name:
                return await self._repo.delete_agent(agent.id)
        msg = f"Agent '{agent_name}' 在团队 '{team_name}' 中不存在"
        raise ValueError(msg)

    async def list_agents(self, team_name: str) -> list[Agent]:
        """列出团队中的所有Agent.

        Args:
            team_name: 团队名称。

        Returns:
            Agent列表。
        """
        team = await self.get_team(team_name)
        return await self._repo.list_agents(team.id)

    # ================================================================
    # 任务执行
    # ================================================================

    async def run_task(
        self,
        team_name: str,
        task_description: str,
        **kwargs: Any,
    ) -> TaskResult:
        """执行任务（核心方法）.

        流程:
        1. 创建Task记录（pending）
        2. 获取team的agents
        3. 编译对应模式的StateGraph
        4. 执行graph（ainvoke），传入task描述
        5. 更新Task记录（completed/failed）
        6. 返回TaskResult

        Args:
            team_name: 团队名称。
            task_description: 任务描述。
            **kwargs: 额外参数。

        Returns:
            TaskResult 任务执行结果。
        """
        team = await self.get_team(team_name)
        agents = await self._repo.list_agents(team.id)

        # 1. 创建Task记录
        title = kwargs.get("title", task_description[:50])
        task = await self._repo.create_task(
            team_id=team.id,
            title=title,
            description=task_description,
        )

        # 2. 更新任务状态为running
        await self._repo.update_task(
            task.id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(),
        )

        start_time = time.time()

        try:
            # 3. 确定LLM模型
            llm_model = kwargs.get("model", "claude-opus-4-6")
            if agents:
                # 使用第一个Agent的模型作为默认
                llm_model = agents[0].model or llm_model

            # 4. 编译StateGraph
            compiled_graph = compile_graph(
                team=team,
                agents=agents,
                memory_store=self._memory,
                llm_model=llm_model,
            )

            # 5. 执行graph
            initial_state = {
                "team_id": team.id,
                "current_task": task_description,
                "messages": [],
                "agent_outputs": {},
                "leader_plan": None,
                "final_result": None,
            }

            result_state = await compiled_graph.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "agents": agents,
                        "llm_model": llm_model,
                    }
                },
            )

            duration = time.time() - start_time
            final_result = result_state.get("final_result", "")
            agent_outputs = result_state.get("agent_outputs", {})

            # 6. 更新Task为completed
            await self._repo.update_task(
                task.id,
                status=TaskStatus.COMPLETED,
                result=final_result,
                completed_at=datetime.now(),
            )

            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                result=final_result or "",
                agent_outputs=agent_outputs,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"任务执行失败: {e}"

            # 更新Task为failed
            await self._repo.update_task(
                task.id,
                status=TaskStatus.FAILED,
                result=error_msg,
                completed_at=datetime.now(),
            )

            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                result=error_msg,
                agent_outputs={},
                duration_seconds=duration,
            )

    # ================================================================
    # 状态查询
    # ================================================================

    async def get_task_status(self, task_id: str) -> Task:
        """查询任务状态.

        Args:
            task_id: 任务ID。

        Returns:
            Task对象。

        Raises:
            ValueError: 任务不存在时。
        """
        task = await self._repo.get_task(task_id)
        if task is None:
            msg = f"任务 '{task_id}' 不存在"
            raise ValueError(msg)
        return task

    async def list_tasks(self, team_name: str) -> list[Task]:
        """列出团队的所有任务.

        Args:
            team_name: 团队名称。

        Returns:
            Task列表。
        """
        team = await self.get_team(team_name)
        return await self._repo.list_tasks(team.id)

    async def get_status(self, team_name: str | None = None) -> TeamStatus:
        """获取团队状态摘要.

        Args:
            team_name: 团队名称。如果为None，返回第一个团队的状态。

        Returns:
            TeamStatus 团队状态摘要。

        Raises:
            ValueError: 团队不存在时。
        """
        if team_name is None:
            teams = await self._repo.list_teams()
            if not teams:
                msg = "没有可用的团队"
                raise ValueError(msg)
            team = teams[0]
        else:
            team = await self.get_team(team_name)

        agents = await self._repo.list_agents(team.id)
        all_tasks = await self._repo.list_tasks(team.id)
        active_tasks = [
            t for t in all_tasks
            if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
        ]
        completed_count = sum(
            1 for t in all_tasks if t.status == TaskStatus.COMPLETED
        )

        return TeamStatus(
            team=team,
            agents=agents,
            active_tasks=active_tasks,
            completed_tasks=completed_count,
            total_tasks=len(all_tasks),
        )
