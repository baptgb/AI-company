"""AI Team OS — Coordinate编排模式 StateGraph.

Coordinate模式流程:
  START → leader_plan → agent_execute(逐个) → leader_synthesize → END

Leader分析任务并制定计划，各Agent按顺序执行子任务，最后Leader综合结果。
"""

from typing import Annotated, Any, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from aiteam.orchestrator.nodes.agent_node import create_agent_node
from aiteam.orchestrator.nodes.leader_node import (
    leader_plan_node,
    leader_synthesize_node,
)
from aiteam.types import Agent


class CoordinateState(TypedDict):
    """Coordinate模式的状态定义."""

    team_id: str
    current_task: str
    messages: Annotated[list[BaseMessage], add_messages]
    agent_outputs: dict[str, str]
    leader_plan: Optional[str]
    final_result: Optional[str]


def build_coordinate_graph(
    agents: list[Agent],
    memory_store: Any | None = None,
    llm_model: str = "claude-opus-4-6",
) -> StateGraph:
    """构建Coordinate模式的StateGraph.

    流程: START → leader_plan → [agent_1 → agent_2 → ...] → leader_synthesize → END

    Args:
        agents: 团队中的Agent列表。
        memory_store: 可选的MemoryStore实例。
        llm_model: 默认LLM模型名。

    Returns:
        已编译的StateGraph可执行对象。
    """
    graph = StateGraph(CoordinateState)

    # 添加Leader规划节点
    graph.add_node("leader_plan", leader_plan_node)

    # 为每个Agent添加执行节点
    agent_node_names = []
    for agent in agents:
        node_name = f"agent_{agent.name}"
        agent_node_fn = create_agent_node(agent, memory_store=memory_store)
        graph.add_node(node_name, agent_node_fn)
        agent_node_names.append(node_name)

    # 添加Leader综合节点
    graph.add_node("leader_synthesize", leader_synthesize_node)

    # 构建边: START → leader_plan
    graph.add_edge(START, "leader_plan")

    if agent_node_names:
        # leader_plan → 第一个Agent
        graph.add_edge("leader_plan", agent_node_names[0])

        # Agent之间顺序链接
        for i in range(len(agent_node_names) - 1):
            graph.add_edge(agent_node_names[i], agent_node_names[i + 1])

        # 最后一个Agent → leader_synthesize
        graph.add_edge(agent_node_names[-1], "leader_synthesize")
    else:
        # 没有Agent时，Leader直接综合（基于自身计划）
        graph.add_edge("leader_plan", "leader_synthesize")

    # leader_synthesize → END
    graph.add_edge("leader_synthesize", END)

    return graph
