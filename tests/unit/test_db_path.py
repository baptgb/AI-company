"""测试数据库路径固化 — 验证默认路径指向 ~/.claude/data/ai-team-os/aiteam.db."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from aiteam.storage.connection import _default_db_url


class TestDefaultDbUrl:
    """验证 _default_db_url() 返回正确的固定路径."""

    def test_url_contains_expected_path(self) -> None:
        """返回的URL应包含 .claude/data/ai-team-os/aiteam.db."""
        url = _default_db_url()
        assert "sqlite+aiosqlite:///" in url
        assert ".claude" in url
        assert "data" in url
        assert "ai-team-os" in url
        assert "aiteam.db" in url

    def test_directory_auto_created(self, tmp_path: Path) -> None:
        """使用mock的home目录验证目录自动创建."""
        fake_home = tmp_path / "fakehome"
        # 不预先创建目录，验证函数会自动创建
        with patch.object(Path, "home", return_value=fake_home):
            url = _default_db_url()

        expected_dir = fake_home / ".claude" / "data" / "ai-team-os"
        assert expected_dir.is_dir()
        assert url == f"sqlite+aiosqlite:///{expected_dir / 'aiteam.db'}"

    def test_idempotent_on_existing_directory(self, tmp_path: Path) -> None:
        """目录已存在时不应报错."""
        fake_home = tmp_path / "fakehome"
        data_dir = fake_home / ".claude" / "data" / "ai-team-os"
        data_dir.mkdir(parents=True)

        with patch.object(Path, "home", return_value=fake_home):
            url = _default_db_url()

        assert "aiteam.db" in url
        assert data_dir.is_dir()
