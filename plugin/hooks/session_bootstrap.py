#!/usr/bin/env python3
"""AI Team OS — Session启动引导脚本

SessionStart hook触发时执行：
1. 检测OS API是否可达
2. 如可达，输出Leader简报（任务墙Top3、团队状态、规则提醒）
3. 如不可达，提示启动服务

stdout输出会被注入到Claude的系统提示中，用于指引Leader行为。
只使用Python标准库。
"""

import json
import sys
import urllib.error
import urllib.request

API_URL = "http://localhost:8000"


def _api_get(path: str, timeout: float = 2.0):
    """GET请求API，返回JSON或None."""
    try:
        req = urllib.request.Request(f"{API_URL}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _build_briefing() -> str:
    """构建Leader简报."""
    lines = []
    lines.append("[AI Team OS] Session启动 — Leader简报")
    lines.append("")

    # 1. 团队状态
    teams_data = _api_get("/api/teams")
    if teams_data and teams_data.get("data"):
        teams = teams_data["data"]
        active = [t for t in teams if t.get("status") == "active"]
        completed = [t for t in teams if t.get("status") == "completed"]
        lines.append(f"团队: {len(active)}个活跃, {len(completed)}个已完成")
        for t in active:
            lines.append(f"  - {t['name']} (active)")
    else:
        lines.append("团队: 暂无")

    lines.append("")

    # 2. 任务墙Top任务（从项目级task-wall获取）
    # 尝试获取第一个项目的task-wall
    projects_data = _api_get("/api/projects")
    if projects_data and projects_data.get("data"):
        project_id = projects_data["data"][0].get("id", "")
        if project_id:
            wall_data = _api_get(f"/api/projects/{project_id}/task-wall")
            if wall_data and wall_data.get("wall"):
                wall = wall_data["wall"]
                pending = []
                for horizon in ["short", "mid", "long"]:
                    for task in wall.get(horizon, []):
                        pending.append(task)
                # 按score排序取前5
                pending.sort(key=lambda t: t.get("score", 0), reverse=True)
                if pending:
                    lines.append("任务墙Top5:")
                    for t in pending[:5]:
                        priority = t.get("priority", "medium")
                        horizon = t.get("horizon", "mid")
                        score = t.get("score", 0)
                        lines.append(
                            f"  [{priority}/{horizon}] {t['title']} (score:{score:.1f})"
                        )
                else:
                    lines.append("任务墙: 无待办任务")
                lines.append("")

                stats = wall_data.get("stats", {})
                if stats:
                    lines.append(
                        f"统计: 总{stats.get('total',0)}任务, "
                        f"已完成{stats.get('completed_count',0)}, "
                        f"待办{stats.get('by_status',{}).get('pending',0)}"
                    )
                    lines.append("")

    # 3. 规则提醒
    lines.append("=== Leader行为规则 ===")
    lines.append("1. 添加成员必须用 Agent(team_name=...) 创建CC团队成员，不用local agent")
    lines.append("2. 只用CC Agent(team_name)创建成员，不要用MCP agent_register预注册")
    lines.append("3. 常驻QA+bug-fixer不Kill，临时开发/研究完成后Kill")
    lines.append("4. 不空等——等结果时继续从任务墙领取任务（最多3个并行）")
    lines.append("5. 任务拆分基于Leader判断，不用模板")
    lines.append("6. 每个任务完成需编写测试验证")
    lines.append("7. [CONTEXT WARNING 80%]时完成当前任务后保存记忆")
    lines.append("8. 完整规则: GET /api/system/rules (31条)")
    lines.append("9. 阅读CLAUDE.md获取项目规则和约束")
    lines.append("")
    lines.append("请先阅读CLAUDE.md中的规则段落，然后查看任务墙决定下一步工作。")

    return "\n".join(lines)


def main() -> None:
    # 读取stdin中的session信息
    try:
        raw = sys.stdin.buffer.read().decode("utf-8")
        session_info = json.loads(raw) if raw.strip() else {}
    except Exception:
        session_info = {}

    # 检测API是否可达
    health = _api_get("/api/teams")

    if health is not None:
        # API可达 → 输出简报到stdout（注入Claude上下文）
        briefing = _build_briefing()
        sys.stdout.write(briefing)

        # stderr记录（不影响stdout注入）
        sys.stderr.write(
            f"[aiteam-bootstrap] AI Team OS API reachable at {API_URL}\n"
            f"[aiteam-bootstrap] session_id={session_info.get('session_id', 'unknown')}\n"
            f"[aiteam-bootstrap] briefing injected ({len(briefing)} chars)\n"
        )
    else:
        # API不可达
        sys.stdout.write(
            "[AI Team OS] API未启动。请运行以下命令启动服务:\n"
            "cd ai-team-os && python -m uvicorn aiteam.api.app:create_app "
            "--factory --host 0.0.0.0 --port 8000 --reload\n"
        )
        sys.stderr.write(
            f"[aiteam-bootstrap] AI Team OS API not reachable at {API_URL}\n"
        )


if __name__ == "__main__":
    main()
