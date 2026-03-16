"""AI Team OS CLI — Rich格式化输出工具."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aiteam.types import Agent, Task, Team, TeamStatusSummary

console = Console()


# ============================================================
# 状态消息
# ============================================================


def print_success(msg: str) -> None:
    """打印成功消息."""
    console.print(f"[bold green][OK][/bold green] {msg}")


def print_error(msg: str) -> None:
    """打印错误消息."""
    console.print(f"[bold red][ERROR][/bold red] {msg}")


def print_warning(msg: str) -> None:
    """打印警告消息."""
    console.print(f"[bold yellow][WARN][/bold yellow] {msg}")


# ============================================================
# 团队显示
# ============================================================


def print_team(team: Team) -> None:
    """用Rich Panel显示团队详情."""
    content = (
        f"[bold]名称:[/bold] {team.name}\n"
        f"[bold]编排模式:[/bold] {team.mode.value}\n"
        f"[bold]ID:[/bold] {team.id}\n"
        f"[bold]创建时间:[/bold] {team.created_at:%Y-%m-%d %H:%M:%S}\n"
        f"[bold]更新时间:[/bold] {team.updated_at:%Y-%m-%d %H:%M:%S}"
    )
    if team.config:
        content += f"\n[bold]配置:[/bold] {team.config}"

    panel = Panel(content, title=f"[bold blue]团队: {team.name}[/bold blue]", border_style="blue")
    console.print(panel)


def print_teams_table(teams: list[Team]) -> None:
    """用Rich Table列出团队."""
    if not teams:
        print_warning("暂无团队")
        return

    table = Table(title="团队列表")
    table.add_column("名称", style="bold cyan")
    table.add_column("编排模式", style="green")
    table.add_column("ID", style="dim")
    table.add_column("创建时间")

    for team in teams:
        table.add_row(
            team.name,
            team.mode.value,
            team.id[:8] + "...",
            team.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


# ============================================================
# Agent显示
# ============================================================


def print_agents_table(agents: list[Agent]) -> None:
    """用Rich Table列出Agent."""
    if not agents:
        print_warning("暂无Agent")
        return

    table = Table(title="Agent列表")
    table.add_column("名称", style="bold cyan")
    table.add_column("角色", style="green")
    table.add_column("模型", style="yellow")
    table.add_column("状态", style="magenta")
    table.add_column("ID", style="dim")

    for agent in agents:
        status_color = {
            "busy": "green",
            "waiting": "blue",
            "offline": "dim",
        }.get(agent.status.value, "white")

        table.add_row(
            agent.name,
            agent.role,
            agent.model,
            f"[{status_color}]{agent.status.value}[/{status_color}]",
            agent.id[:8] + "...",
        )

    console.print(table)


# ============================================================
# 任务显示
# ============================================================


def print_tasks_table(tasks: list[Task]) -> None:
    """用Rich Table列出任务."""
    if not tasks:
        print_warning("暂无任务")
        return

    table = Table(title="任务列表")
    table.add_column("ID", style="dim")
    table.add_column("标题", style="bold cyan")
    table.add_column("状态", style="magenta")
    table.add_column("分配给")
    table.add_column("创建时间")

    for task in tasks:
        status_color = {
            "pending": "yellow",
            "running": "blue",
            "completed": "green",
            "failed": "red",
        }.get(task.status.value, "white")

        table.add_row(
            task.id[:8] + "...",
            task.title,
            f"[{status_color}]{task.status.value}[/{status_color}]",
            task.assigned_to or "-",
            task.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


# ============================================================
# 状态面板
# ============================================================


def print_status(status: TeamStatusSummary) -> None:
    """综合状态面板."""
    # 团队信息
    team = status.team
    content = (
        f"[bold]团队名称:[/bold] {team.name}\n"
        f"[bold]编排模式:[/bold] {team.mode.value}\n"
        f"[bold]Agent数量:[/bold] {len(status.agents)}\n"
        f"[bold]活跃任务:[/bold] {len(status.active_tasks)}\n"
        f"[bold]已完成任务:[/bold] {status.completed_tasks}\n"
        f"[bold]总任务数:[/bold] {status.total_tasks}"
    )

    panel = Panel(
        content,
        title=f"[bold blue]状态: {team.name}[/bold blue]",
        border_style="blue",
    )
    console.print(panel)

    # Agent列表
    if status.agents:
        print_agents_table(status.agents)

    # 活跃任务
    if status.active_tasks:
        print_tasks_table(status.active_tasks)
