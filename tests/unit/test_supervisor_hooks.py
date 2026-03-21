"""Tests for supervisor hook checks in workflow_reminder.py.

Tests _check_leader_doing_too_much and _check_team_has_permanent_members.
"""

from __future__ import annotations

import sys
from pathlib import Path

# 将hooks目录加入sys.path以便直接导入workflow_reminder
_hooks_dir = str(Path(__file__).resolve().parents[2] / "plugin" / "hooks")
if _hooks_dir not in sys.path:
    sys.path.insert(0, _hooks_dir)

from workflow_reminder import (  # noqa: E402
    _LEADER_CONSECUTIVE_THRESHOLD,
    _TEAM_WITHOUT_MEMBERS_THRESHOLD,
    _check_leader_doing_too_much,
    _check_team_has_permanent_members,
)


class TestLeaderDoingTooMuch:
    """Tests for _check_leader_doing_too_much."""

    def test_leader_consecutive_calls_warning(self):
        """超过阈值次连续非委派调用时应产生warning。"""
        state: dict = {}
        event = {"tool_name": "Bash", "hook_event_name": "PreToolUse"}

        # 前threshold次不应warning
        for i in range(1, _LEADER_CONSECUTIVE_THRESHOLD + 1):
            result = _check_leader_doing_too_much(event, state)
            assert result is None, f"Unexpected warning at call {i}"

        # 第threshold+1次应warning
        result = _check_leader_doing_too_much(event, state)
        assert result is not None
        assert "B0.9" in result
        assert str(_LEADER_CONSECUTIVE_THRESHOLD + 1) in result

    def test_agent_call_resets_counter(self):
        """Agent调用应重置计数器。"""
        state: dict = {}
        bash_event = {"tool_name": "Edit", "hook_event_name": "PreToolUse"}
        agent_event = {"tool_name": "Agent", "hook_event_name": "PreToolUse"}

        # 积累一些调用
        for _ in range(7):
            _check_leader_doing_too_much(bash_event, state)

        # Agent调用重置计数器
        result = _check_leader_doing_too_much(agent_event, state)
        assert result is None
        assert state.get("leader_consecutive_calls", 0) == 0

        # 重新积累不应立即warning
        result = _check_leader_doing_too_much(bash_event, state)
        assert result is None

    def test_team_create_resets_counter(self):
        """TeamCreate调用也应重置计数器。"""
        state: dict = {}
        bash_event = {"tool_name": "Read", "hook_event_name": "PreToolUse"}
        create_event = {"tool_name": "TeamCreate", "hook_event_name": "PreToolUse"}

        for _ in range(7):
            _check_leader_doing_too_much(bash_event, state)

        result = _check_leader_doing_too_much(create_event, state)
        assert result is None
        assert state.get("leader_consecutive_calls", 0) == 0

    def test_send_message_resets_counter(self):
        """SendMessage调用也应重置计数器。"""
        state: dict = {}
        bash_event = {"tool_name": "Write", "hook_event_name": "PreToolUse"}
        msg_event = {"tool_name": "SendMessage", "hook_event_name": "PreToolUse"}

        for _ in range(7):
            _check_leader_doing_too_much(bash_event, state)

        result = _check_leader_doing_too_much(msg_event, state)
        assert result is None
        assert state.get("leader_consecutive_calls", 0) == 0

    def test_empty_tool_name_no_warning(self):
        """空tool_name时不应处理。"""
        state: dict = {}
        event = {"tool_name": "", "hook_event_name": "PreToolUse"}
        result = _check_leader_doing_too_much(event, state)
        assert result is None

    def test_counter_persists_in_state(self):
        """计数器应在state字典中持久化。"""
        state: dict = {}
        event = {"tool_name": "Bash", "hook_event_name": "PreToolUse"}

        _check_leader_doing_too_much(event, state)
        _check_leader_doing_too_much(event, state)
        _check_leader_doing_too_much(event, state)

        assert state["leader_consecutive_calls"] == 3


class TestTeamHasPermanentMembers:
    """Tests for _check_team_has_permanent_members."""

    def test_team_without_members_warning(self):
        """TeamCreate后未添加成员时应在达到阈值后warning。"""
        state: dict = {}
        # PostToolUse: TeamCreate完成
        post_event = {
            "tool_name": "TeamCreate",
            "hook_event_name": "PostToolUse",
        }
        result = _check_team_has_permanent_members(post_event, state)
        assert result is None  # 设置标记，不warning

        # 后续PreToolUse中连续非Agent调用
        pre_event = {
            "tool_name": "Bash",
            "hook_event_name": "PreToolUse",
        }
        for i in range(1, _TEAM_WITHOUT_MEMBERS_THRESHOLD):
            result = _check_team_has_permanent_members(pre_event, state)
            assert result is None, f"Unexpected warning at call {i}"

        # 达到阈值时应warning
        result = _check_team_has_permanent_members(pre_event, state)
        assert result is not None
        assert "B0.10" in result
        assert "常驻成员" in result

    def test_agent_call_after_team_create_no_warning(self):
        """TeamCreate后立即调用Agent时不应warning。"""
        state: dict = {}
        # TeamCreate完成
        post_event = {
            "tool_name": "TeamCreate",
            "hook_event_name": "PostToolUse",
        }
        _check_team_has_permanent_members(post_event, state)

        # 立即创建Agent成员
        agent_event = {
            "tool_name": "Agent",
            "hook_event_name": "PreToolUse",
        }
        result = _check_team_has_permanent_members(agent_event, state)
        assert result is None

        # 监控应已关闭
        assert state.get("team_created_waiting", False) is False

    def test_no_team_create_no_warning(self):
        """没有TeamCreate时任何工具调用都不应触发此检查。"""
        state: dict = {}
        pre_event = {
            "tool_name": "Bash",
            "hook_event_name": "PreToolUse",
        }
        for _ in range(10):
            result = _check_team_has_permanent_members(pre_event, state)
            assert result is None

    def test_warning_only_fires_once(self):
        """warning触发后应重置状态，不反复提醒。"""
        state: dict = {}
        # TeamCreate
        post_event = {
            "tool_name": "TeamCreate",
            "hook_event_name": "PostToolUse",
        }
        _check_team_has_permanent_members(post_event, state)

        pre_event = {
            "tool_name": "Bash",
            "hook_event_name": "PreToolUse",
        }
        # 触发warning
        for _ in range(_TEAM_WITHOUT_MEMBERS_THRESHOLD):
            _check_team_has_permanent_members(pre_event, state)

        # 之后不应再warning（已重置）
        result = _check_team_has_permanent_members(pre_event, state)
        assert result is None

    def test_post_tool_use_non_team_create_ignored(self):
        """PostToolUse非TeamCreate工具不应设置标记。"""
        state: dict = {}
        post_event = {
            "tool_name": "Bash",
            "hook_event_name": "PostToolUse",
        }
        result = _check_team_has_permanent_members(post_event, state)
        assert result is None
        assert state.get("team_created_waiting", False) is False


class TestNormalFlowNoWarning:
    """Tests that normal (well-behaved) flows produce no warnings."""

    def test_normal_flow_no_warning(self):
        """正常流程（混合委派和直接操作）不应产生warning。"""
        state: dict = {}
        # Leader做几步操作
        for tool in ["Read", "Bash", "Read"]:
            event = {"tool_name": tool, "hook_event_name": "PreToolUse"}
            r1 = _check_leader_doing_too_much(event, state)
            r2 = _check_team_has_permanent_members(event, state)
            assert r1 is None
            assert r2 is None

        # 然后委派
        event = {"tool_name": "Agent", "hook_event_name": "PreToolUse"}
        r1 = _check_leader_doing_too_much(event, state)
        r2 = _check_team_has_permanent_members(event, state)
        assert r1 is None
        assert r2 is None

        # 再做几步
        for tool in ["Edit", "Bash"]:
            event = {"tool_name": tool, "hook_event_name": "PreToolUse"}
            r1 = _check_leader_doing_too_much(event, state)
            r2 = _check_team_has_permanent_members(event, state)
            assert r1 is None
            assert r2 is None

    def test_team_create_then_agent_no_warning(self):
        """TeamCreate后立即用Agent添加成员 -- 完全正常的流程。"""
        state: dict = {}
        # TeamCreate (PostToolUse)
        post_event = {
            "tool_name": "TeamCreate",
            "hook_event_name": "PostToolUse",
        }
        r = _check_team_has_permanent_members(post_event, state)
        assert r is None

        # 立即添加Agent成员 (PreToolUse)
        agent_event = {
            "tool_name": "Agent",
            "hook_event_name": "PreToolUse",
        }
        r = _check_team_has_permanent_members(agent_event, state)
        assert r is None

        # 之后继续其他操作不受影响
        bash_event = {
            "tool_name": "Bash",
            "hook_event_name": "PreToolUse",
        }
        for _ in range(5):
            r = _check_team_has_permanent_members(bash_event, state)
            assert r is None
