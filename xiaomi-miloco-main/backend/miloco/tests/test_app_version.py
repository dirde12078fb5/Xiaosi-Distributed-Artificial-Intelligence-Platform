# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""AppSettings 版本运行时解析 (_resolve_version) 的兜底链测试.

覆盖:
- 已安装 → 读包元数据
- 未安装 + git describe 成功 → 用 git 描述
- 未安装 + git 失败 → 0.0.0+unknown（导入期绝不抛）
- AppSettings.version 字段非空
"""

from importlib.metadata import PackageNotFoundError
from unittest.mock import MagicMock, patch

from miloco.config import settings as settings_mod


def test_reads_package_metadata():
    settings_mod._resolve_version.cache_clear()
    with patch("importlib.metadata.version", return_value="2026.6.17"):
        assert settings_mod._resolve_version() == "2026.6.17"


def test_fallback_git_describe_when_not_installed():
    settings_mod._resolve_version.cache_clear()
    with (
        patch("importlib.metadata.version", side_effect=PackageNotFoundError),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="v2026.6.17-3-gabc123\n")
        assert settings_mod._resolve_version() == "v2026.6.17-3-gabc123"


def test_fallback_unknown_when_no_git():
    settings_mod._resolve_version.cache_clear()
    with (
        patch("importlib.metadata.version", side_effect=PackageNotFoundError),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        assert settings_mod._resolve_version() == "0.0.0+unknown"


def test_app_settings_version_non_empty():
    settings_mod._resolve_version.cache_clear()
    assert settings_mod.AppSettings().version
