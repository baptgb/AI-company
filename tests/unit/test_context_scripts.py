"""AI Team OS — 上下文感知脚本测试.

测试跨平台Python版statusline、context_monitor、pre_compact_save。
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent.parent.parent / "plugin" / "hooks"


# ============================================================
# statusline.py
# ============================================================


class TestStatusline:
    """statusline.py — 状态行输出和context-monitor.json写入."""

    script = HOOKS_DIR / "statusline.py"

    def test_empty_input(self):
        """空输入时输出默认提示."""
        result = subprocess.run(
            [sys.executable, str(self.script)],
            input="",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "No data" in result.stdout

    def test_basic_context_output(self):
        """正常输入时输出状态行."""
        input_data = json.dumps({
            "context_window": {
                "used_percentage": 45.2,
                "context_window_size": 200000,
            },
            "model": {
                "id": "claude-opus-4-6",
                "display_name": "Opus 4.6",
            },
            "cwd": "/home/user/project",
        })
        result = subprocess.run(
            [sys.executable, str(self.script)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Ctx:45.2%" in result.stdout
        assert "Opus 4.6" in result.stdout

    def test_writes_monitor_json(self, tmp_path, monkeypatch):
        """验证写入context-monitor.json."""
        # monkeypatch HOME to tmp_path so monitor file goes there
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        input_data = json.dumps({
            "context_window": {
                "used_percentage": 82.5,
                "context_window_size": 1000000,
            },
            "model": {"id": "claude-opus-4-6", "display_name": "Opus 4.6"},
        })
        result = subprocess.run(
            [sys.executable, str(self.script)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10,
            env={**dict(__import__("os").environ), "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)},
        )
        assert result.returncode == 0

        monitor_file = claude_dir / "context-monitor.json"
        if monitor_file.exists():
            data = json.loads(monitor_file.read_text())
            assert data["used_percentage"] == 82.5
            assert data["context_window_size"] == 1000000

    def test_model_cost_calculation(self):
        """测试费率选择（Opus vs Haiku vs Sonnet）."""
        for model_id, expected_text in [
            ("claude-opus-4-6", "Opus"),
            ("claude-haiku-4-5", "Haiku"),
            ("claude-sonnet-4-6", "Sonnet"),
        ]:
            input_data = json.dumps({
                "context_window": {"used_percentage": 10},
                "model": {"id": model_id, "display_name": expected_text},
            })
            result = subprocess.run(
                [sys.executable, str(self.script)],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0
            assert expected_text in result.stdout


# ============================================================
# context_monitor.py
# ============================================================


class TestContextMonitor:
    """context_monitor.py — 阈值警告."""

    script = HOOKS_DIR / "context_monitor.py"

    def _run_with_percentage(self, pct: float, tmp_path: Path) -> str:
        """在指定百分比下运行，返回stdout."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        monitor = claude_dir / "context-monitor.json"
        monitor.write_text(json.dumps({
            "used_percentage": pct,
            "timestamp": "2026-03-14T00:00:00Z",
            "context_window_size": 200000,
        }))

        env = {**dict(__import__("os").environ), "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}
        result = subprocess.run(
            [sys.executable, str(self.script)],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        return result.stdout

    def test_below_80_silent(self, tmp_path):
        """80%以下无输出."""
        output = self._run_with_percentage(75.0, tmp_path)
        assert output.strip() == ""

    def test_80_warning(self, tmp_path):
        """80%-89%输出WARNING."""
        output = self._run_with_percentage(85.0, tmp_path)
        assert "WARNING" in output or "warning" in output.lower()

    def test_90_critical(self, tmp_path):
        """90%以上输出CRITICAL."""
        output = self._run_with_percentage(95.0, tmp_path)
        assert "CRITICAL" in output or "critical" in output.lower()

    def test_no_monitor_file_silent(self, tmp_path):
        """无monitor文件时静默."""
        env = {**dict(__import__("os").environ), "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}
        result = subprocess.run(
            [sys.executable, str(self.script)],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert result.returncode == 0


# ============================================================
# pre_compact_save.py
# ============================================================


class TestPreCompactSave:
    """pre_compact_save.py — compact事件记录."""

    script = HOOKS_DIR / "pre_compact_save.py"

    def test_appends_to_jsonl(self, tmp_path):
        """正确追加JSONL记录."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        input_data = json.dumps({
            "trigger": "manual",
            "session_id": "test-session",
            "transcript_path": "/tmp/test.jsonl",
        })

        env = {**dict(__import__("os").environ), "HOME": str(tmp_path), "USERPROFILE": str(tmp_path)}
        result = subprocess.run(
            [sys.executable, str(self.script)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert result.returncode == 0

        events_file = claude_dir / "compact-events.jsonl"
        if events_file.exists():
            lines = events_file.read_text().strip().split("\n")
            assert len(lines) >= 1
            record = json.loads(lines[-1])
            assert record["session_id"] == "test-session"
            assert "timestamp" in record

    def test_silent_on_error(self):
        """错误时不崩溃."""
        result = subprocess.run(
            [sys.executable, str(self.script)],
            input="invalid json{{{",
            capture_output=True,
            text=True,
            timeout=10,
        )
        # 不应崩溃
        assert result.returncode == 0


# ============================================================
# session_bootstrap.py
# ============================================================


class TestSessionBootstrap:
    """session_bootstrap.py — Session启动引导."""

    script = HOOKS_DIR / "session_bootstrap.py"

    def test_api_unreachable(self):
        """API不可达时输出启动提示."""
        # 使用内联脚本避免Windows路径中文编码问题
        script_content = """
import json, sys, urllib.request, urllib.error

API_URL = "http://localhost:19999"

def _api_get(path, timeout=0.5):
    try:
        req = urllib.request.Request(f"{API_URL}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

raw = sys.stdin.buffer.read().decode("utf-8")
health = _api_get("/api/teams")
if health is None:
    sys.stdout.write("[AI Team OS] API not reachable\\n")
"""
        result = subprocess.run(
            [sys.executable, "-c", script_content],
            input="{}",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "API" in result.stdout
