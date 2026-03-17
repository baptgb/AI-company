#!/usr/bin/env python3
"""AI Team OS — Claude Code Hook事件发送器

CC hook触发时执行此脚本，将事件转发到OS API。
用法: python send_event.py <EventType> (从stdin读取JSON)

注意: 此脚本只使用Python标准库，不依赖任何第三方包，
因为它可能在任何Python环境中被CC直接调用。
"""

import glob
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = os.environ.get("AITEAM_API_URL", "http://localhost:8000")

# 大字段截断限制（防止SubagentStop等事件payload过大导致超时）
MAX_FIELD_LEN = 500
MAX_PAYLOAD_BYTES = 32_768  # 整体payload上限32KB，超过则丢弃非必要字段
LARGE_FIELDS = {"last_assistant_message", "agent_transcript_path", "transcript_path"}
# 必须保留的字段（即使payload超限也不丢弃）
ESSENTIAL_FIELDS = {"hook_event_name", "session_id", "tool_name", "tool_input", "cc_team_name"}


def _trim_payload(payload: dict) -> dict:
    """截断过大的字段，防止HTTP超时。

    两级保护:
    1. 已知大字段截断到 MAX_FIELD_LEN (500字符)
    2. 整体超过50KB时，所有字符串字段截断到200字符
    """
    trimmed = {}
    for k, v in payload.items():
        if k in LARGE_FIELDS:
            if isinstance(v, str) and len(v) > MAX_FIELD_LEN:
                trimmed[k] = v[:MAX_FIELD_LEN] + "...(truncated)"
            elif isinstance(v, dict):
                trimmed[k] = str(v)[:MAX_FIELD_LEN] + "...(truncated)"
            else:
                trimmed[k] = v
        elif k == "tool_response" and isinstance(v, dict):
            # 截断工具输出但保留结构
            tr = {}
            for rk, rv in v.items():
                if isinstance(rv, str) and len(rv) > MAX_FIELD_LEN:
                    tr[rk] = rv[:MAX_FIELD_LEN] + "...(truncated)"
                else:
                    tr[rk] = rv
            trimmed[k] = tr
        else:
            trimmed[k] = v

    # 整体大小检查：超过50KB则递归截断所有字符串字段
    payload_str = json.dumps(trimmed)
    if len(payload_str) > 50_000:
        for k, v in trimmed.items():
            if isinstance(v, str) and len(v) > 200:
                trimmed[k] = v[:200] + "...(truncated)"

    return trimmed


def _resolve_cc_team_name(session_id: str, agent_name: str = "") -> str | None:
    """通过agent_name在CC团队配置中查找所属团队名称。

    策略1: 按members.name精确匹配（不依赖sessionId，跨session可靠）
    策略2: fallback按leadSessionId匹配
    只使用标准库，静默处理所有异常。
    """
    teams_dir = os.path.join(os.path.expanduser("~"), ".claude", "teams")
    try:
        config_files = glob.glob(os.path.join(teams_dir, "*", "config.json"))
    except OSError:
        return None

    # 策略1：按agent_name在members列表中查找（跨session可靠）
    if agent_name:
        for config_path in config_files:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                for m in config.get("members", []):
                    if m.get("name", "") == agent_name:
                        return config.get("name")
            except (json.JSONDecodeError, OSError, KeyError):
                continue

    # 策略2：fallback按leadSessionId
    if session_id:
        for config_path in config_files:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                if config.get("leadSessionId") == session_id:
                    return config.get("name")
            except (json.JSONDecodeError, OSError, KeyError):
                continue

    return None



def main() -> None:
    try:
        # Windows下stdin默认用GBK解码，CC发送的是UTF-8，强制用buffer读取
        raw = sys.stdin.buffer.read().decode("utf-8")
        if not raw.strip():
            return

        payload = json.loads(raw)

        # CC hook payload不自带事件类型名，通过命令行参数注入
        if len(sys.argv) > 1 and "hook_event_name" not in payload:
            payload["hook_event_name"] = sys.argv[1]

        # SubagentStart/SubagentStop: 注入CC团队名称
        event_name = payload.get("hook_event_name", "")
        if event_name in ("SubagentStart", "SubagentStop") and "cc_team_name" not in payload:
            session_id = payload.get("session_id", "")
            agent_name = payload.get("agent_type", "")
            cc_team = _resolve_cc_team_name(session_id, agent_name)
            if cc_team:
                payload["cc_team_name"] = cc_team

        # 截断大字段
        payload = _trim_payload(payload)

        # 整体payload大小检查：超过上限则只保留必要字段
        data = json.dumps(payload).encode("utf-8")
        if len(data) > MAX_PAYLOAD_BYTES:
            stripped = {k: v for k, v in payload.items() if k in ESSENTIAL_FIELDS}
            stripped["_stripped"] = True
            stripped["_original_size"] = len(data)
            event_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"
            sys.stderr.write(
                f"[aiteam-hook] {event_name}: payload too large "
                f"({len(data)} bytes > {MAX_PAYLOAD_BYTES}), stripped to essentials\n"
            )
            data = json.dumps(stripped).encode("utf-8")
        req = urllib.request.Request(
            f"{API_URL}/api/hooks/event",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=1.5) as resp:
            result = json.loads(resp.read().decode())
            # 返回决策给CC（对于PreToolUse等需要决策的hook）
            if "decision" in result:
                print(json.dumps(result))

    except urllib.error.URLError as e:
        # OS服务未启动，输出到stderr方便调试（不阻塞CC）
        event_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"
        sys.stderr.write(f"[aiteam-hook] {event_name}: API unreachable - {e}\n")
    except Exception as e:
        # 其他错误也记录到stderr
        event_name = sys.argv[1] if len(sys.argv) > 1 else "unknown"
        sys.stderr.write(f"[aiteam-hook] {event_name}: error - {e}\n")


if __name__ == "__main__":
    main()
