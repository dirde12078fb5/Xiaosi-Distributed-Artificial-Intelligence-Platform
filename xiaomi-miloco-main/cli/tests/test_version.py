"""miloco-cli 版本运行时解析与 version 命令测试.

覆盖:
- 已安装 → 读包元数据
- 未安装 + 无 git → 0.0.0+unknown（不抛）
- version 命令输出走 _VERSION（包元数据），不再是写死的 0.1.0
"""

from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from click.testing import CliRunner

from miloco_cli import main as main_mod


def test_reads_package_metadata():
    main_mod._resolve_version.cache_clear()
    with patch("importlib.metadata.version", return_value="2026.6.17"):
        assert main_mod._resolve_version() == "2026.6.17"


def test_fallback_unknown_when_no_git():
    main_mod._resolve_version.cache_clear()
    with (
        patch("importlib.metadata.version", side_effect=PackageNotFoundError),
        patch("subprocess.run", side_effect=FileNotFoundError),
    ):
        assert main_mod._resolve_version() == "0.0.0+unknown"


def test_version_command_outputs_resolved_version():
    result = CliRunner().invoke(main_mod.cli, ["version"])
    assert result.exit_code == 0
    assert main_mod._VERSION in result.output
