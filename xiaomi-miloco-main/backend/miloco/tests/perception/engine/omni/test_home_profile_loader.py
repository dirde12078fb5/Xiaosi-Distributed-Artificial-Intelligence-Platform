"""Tests for home_profile_loader — reading canonical profile.md via profile_md_path()."""

from __future__ import annotations

from pathlib import Path

import pytest
from miloco.perception.engine.omni.home_profile_loader import (
    get_home_profile_prefix,
)


@pytest.fixture()
def patch_profile_path(monkeypatch: pytest.MonkeyPatch):
    """Return a helper that patches profile_md_path to return a given path.

    loader 通过 ``from miloco.home_profile.store import profile_md_path`` 绑定，
    所以 patch 必须打在 loader 模块命名空间里的 ``profile_md_path``。
    """

    def _patch(path: str | Path) -> None:
        monkeypatch.setattr(
            "miloco.perception.engine.omni.home_profile_loader.profile_md_path",
            lambda: Path(path),
        )

    return _patch


class TestGetHomeProfilePrefix:
    def test_returns_empty_when_profile_file_not_found(self, patch_profile_path):
        patch_profile_path("/nonexistent/path/profile.md")
        assert get_home_profile_prefix() == ""

    def test_passes_through_and_strips_content(
        self, tmp_path: Path, patch_profile_path
    ):
        # 档案已由 render 产出完整层级（# 家庭档案 / ## 分类 / ### 分组），
        # loader 仅 strip 首尾空白后原样透传，不做任何标题改写。
        profile = tmp_path / "profile.md"
        profile.write_text(
            "  # 家庭档案\n\n## 家庭成员\n\n### 爸爸\n  ", encoding="utf-8"
        )
        patch_profile_path(profile)
        result = get_home_profile_prefix()
        assert result == "# 家庭档案\n\n## 家庭成员\n\n### 爸爸"

    def test_returns_cjk_content(self, tmp_path: Path, patch_profile_path):
        profile = tmp_path / "profile.md"
        content = "# 家庭档案\n\n## 家庭成员\n\n### 爸爸\n- 06:30 起床\n- 空调 24 度\n"
        profile.write_text(content, encoding="utf-8")
        patch_profile_path(profile)
        result = get_home_profile_prefix()
        assert "爸爸" in result
        assert "06:30 起床" in result

    def test_returns_empty_on_unreadable_file(
        self, tmp_path: Path, patch_profile_path
    ):
        profile = tmp_path / "profile.md"
        profile.mkdir()  ## directory, not file — read will raise
        patch_profile_path(profile)
        assert get_home_profile_prefix() == ""

    def test_path_resolved_from_store(self, tmp_path: Path, patch_profile_path):
        profile = tmp_path / "sub" / "profile.md"
        profile.parent.mkdir()
        profile.write_text("# 家庭档案\n\n## 家庭成员", encoding="utf-8")
        patch_profile_path(profile)
        assert get_home_profile_prefix() == "# 家庭档案\n\n## 家庭成员"

    def test_empty_file_returns_empty(self, tmp_path: Path, patch_profile_path):
        profile = tmp_path / "empty.md"
        profile.write_text("", encoding="utf-8")
        patch_profile_path(profile)
        assert get_home_profile_prefix() == ""

    def test_whitespace_only_file_returns_empty(
        self, tmp_path: Path, patch_profile_path
    ):
        profile = tmp_path / "blank.md"
        profile.write_text("  \n\n  ", encoding="utf-8")
        patch_profile_path(profile)
        assert get_home_profile_prefix() == ""

    def test_preserves_internal_whitespace(
        self, tmp_path: Path, patch_profile_path
    ):
        profile = tmp_path / "profile.md"
        profile.write_text(
            "## Title\n\n### Section\n\nContent here\n", encoding="utf-8"
        )
        patch_profile_path(profile)
        result = get_home_profile_prefix()
        assert result == "## Title\n\n### Section\n\nContent here"
