"""doctor 命令测试：mock 系统调用，验证各平台检测逻辑。"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from miloco_cli.commands.doctor import (
    _NOT_FOUND,
    CmdResult,
    Status,
    check_firewall,
    check_wsl,
)
from miloco_cli.main import cli


def _ok(stdout: str) -> CmdResult:
    return CmdResult(found=True, rc=0, stdout=stdout, stderr="")


def _fail(rc: int = 1, stderr: str = "") -> CmdResult:
    return CmdResult(found=True, rc=rc, stdout="", stderr=stderr)


@pytest.fixture
def runner():
    return CliRunner()


# ─── 防火墙检测 ───────────────────────────────────────────────────────────────


class TestCheckFirewall:
    def test_macos_pass(self):
        with patch("miloco_cli.commands.doctor._detect_platform", return_value="macos"):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert "macOS" in results[0].name

    def test_no_firewall_tools(self):
        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", return_value=_NOT_FOUND),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert "未检测到" in results[0].message

    def test_iptables_drop_udp(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _NOT_FOUND
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _ok(
                    "Chain INPUT (policy ACCEPT)\n"
                    "target     prot opt source               destination\n"
                    "DROP       udp  --  0.0.0.0/0            0.0.0.0/0\n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.FAIL
        assert "iptables" in results[0].name

    def test_iptables_no_udp_block(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _NOT_FOUND
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _ok(
                    "Chain INPUT (policy ACCEPT)\n"
                    "target     prot opt source               destination\n"
                    "ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0\n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert "iptables" in results[0].name

    def test_iptables_policy_drop_no_udp_accept(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _NOT_FOUND
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _ok(
                    "Chain INPUT (policy DROP)\n"
                    "target     prot opt source               destination\n"
                    "ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:22\n"
                    "ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED\n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.FAIL
        assert "默认策略" in results[0].message

    def test_iptables_policy_drop_with_udp_accept(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _NOT_FOUND
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _ok(
                    "Chain INPUT (policy DROP)\n"
                    "target     prot opt source               destination\n"
                    "ACCEPT     udp  --  192.168.0.0/16       0.0.0.0/0\n"
                    "ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:22\n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS

    def test_ufw_unrecognized_output(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _ok("Estado: activo\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert "无法识别" in results[0].message

    def test_ufw_inactive(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _ok("Status: inactive\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert "未激活" in results[0].message

    def test_ufw_deny_incoming(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _ok("Status: active\n")
            if cmd == ["ufw", "status", "verbose"]:
                return _ok("Default: deny (incoming), allow (outgoing)\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.FAIL
        assert results[0].fix_hint is not None
        assert "ufw allow" in results[0].fix_hint

    def test_ufw_allow_incoming(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _ok("Status: active\n")
            if cmd == ["ufw", "status", "verbose"]:
                return _ok("Default: allow (incoming), allow (outgoing)\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS

    def test_firewalld_get_zone_fails(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _ok("running\n")
            if cmd == ["firewall-cmd", "--get-default-zone"]:
                return _fail(1)
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert "无法获取" in results[0].message

    def test_firewalld_drop(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _ok("running\n")
            if cmd == ["firewall-cmd", "--get-default-zone"]:
                return _ok("public\n")
            if cmd == ["firewall-cmd", "--zone=public", "--list-all"]:
                return _ok("public\n  target: DROP\n  services: ssh\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.FAIL
        assert "firewalld" in results[0].name

    def test_firewalld_target_default_warn(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _ok("running\n")
            if cmd == ["firewall-cmd", "--get-default-zone"]:
                return _ok("public\n")
            if cmd == ["firewall-cmd", "--zone=public", "--list-all"]:
                return _ok("public\n  target: default\n  services: ssh\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert "default" in results[0].message

    def test_firewalld_protocols_udp_pass(self):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _ok("running\n")
            if cmd == ["firewall-cmd", "--get-default-zone"]:
                return _ok("public\n")
            if cmd == ["firewall-cmd", "--zone=public", "--list-all"]:
                return _ok(
                    "public\n  target: default\n  services: ssh\n"
                    "  protocols: udp\n  ports: \n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS

    def test_firewalld_port_udp_only_warn(self):
        """仅有特定端口 UDP 规则（如 53/udp）应 WARN 而非 PASS"""
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _ok("running\n")
            if cmd == ["firewall-cmd", "--get-default-zone"]:
                return _ok("public\n")
            if cmd == ["firewall-cmd", "--zone=public", "--list-all"]:
                return _ok(
                    "public\n  target: default\n  services: ssh dhcpv6-client\n"
                    "  ports: 53/udp 80/tcp\n  protocols: \n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert "特定端口" in results[0].message

    def test_ufw_permission_denied(self):
        """ufw 已安装但无 sudo 权限时应 WARN 而非 fall-through 到 PASS"""
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _fail(1, stderr="ERROR: You need to be root to run this script\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert "权限不足" in results[0].message

    def test_iptables_permission_denied(self):
        """iptables 已安装但无 sudo 权限时应 WARN 而非 fall-through 到 PASS"""
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _NOT_FOUND
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _fail(4, stderr="iptables v1.8.7: Permission denied\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert "权限不足" in results[0].message

    def test_firewalld_permission_denied(self):
        """firewalld 已安装但无权限时应 WARN 而非 fall-through"""
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _fail(1, stderr="Authorization failed\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert "权限不足" in results[0].message

    def test_firewalld_not_running_falls_through_to_iptables(self):
        """firewalld 未运行时应 fall-through 到 iptables 检测"""
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return CmdResult(found=True, rc=252, stdout="not running\n", stderr="")
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _ok(
                    "Chain INPUT (policy ACCEPT)\n"
                    "target     prot opt source               destination\n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert "iptables" in results[0].name

    def test_firewalld_not_running_old_version_stderr(self):
        """旧版 firewalld stdout 为空、stderr 含 not running 时应 fall-through"""
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return CmdResult(found=True, rc=252, stdout="", stderr="FirewallD is not running\n")
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _ok(
                    "Chain INPUT (policy ACCEPT)\n"
                    "target     prot opt source               destination\n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS
        assert "iptables" in results[0].name

    def test_iptables_port_limited_udp_accept_warn(self):
        """iptables policy DROP + 仅端口限定 UDP ACCEPT 应 WARN"""
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _NOT_FOUND
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _ok(
                    "Chain INPUT (policy DROP)\n"
                    "target     prot opt source               destination\n"
                    "ACCEPT     udp  --  0.0.0.0/0            0.0.0.0/0            udp dpt:53\n"
                    "ACCEPT     tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:22\n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert "特定端口" in results[0].message

    def test_iptables_accept_and_drop_udp_warn(self):
        """iptables 同时存在 UDP ACCEPT 与 DROP 规则应 WARN（非 FAIL）"""
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _NOT_FOUND
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _ok(
                    "Chain INPUT (policy DROP)\n"
                    "target     prot opt source               destination\n"
                    "ACCEPT     udp  --  192.168.0.0/16       0.0.0.0/0\n"
                    "ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED\n"
                    "DROP       udp  --  0.0.0.0/0            0.0.0.0/0\n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.WARN
        assert "人工核对" in results[0].message

    def test_iptables_accept_all_covers_udp(self):
        """ACCEPT all 全协议放行应被识别为 UDP 放行，不误报 FAIL"""
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _NOT_FOUND
            if cmd == ["firewall-cmd", "--state"]:
                return _NOT_FOUND
            if cmd == ["iptables", "-L", "INPUT", "-n"]:
                return _ok(
                    "Chain INPUT (policy DROP)\n"
                    "target     prot opt source               destination\n"
                    "ACCEPT     all  --  192.168.0.0/16       0.0.0.0/0\n"
                    "ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0            state RELATED,ESTABLISHED\n"
                )
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_firewall()
        assert len(results) == 1
        assert results[0].status == Status.PASS


# ─── WSL 检测 ─────────────────────────────────────────────────────────────────


class TestCheckWsl:
    def test_not_wsl_empty(self):
        with patch("miloco_cli.commands.doctor._is_wsl", return_value=False):
            results = check_wsl()
        assert results == []

    def test_wsl_mirrored_and_hyperv_ok(self, tmp_path):
        wslconfig = tmp_path / ".wslconfig"
        wslconfig.write_text("[wsl2]\nnetworkingMode=mirrored\n")

        def fake_run(cmd, timeout=5):
            if "powershell.exe" in cmd and "Get-NetFirewallHyperVVMSetting" in " ".join(cmd):
                return _ok("Allow\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._is_wsl", return_value=True),
            patch(
                "miloco_cli.commands.doctor._get_wslconfig_path", return_value=wslconfig
            ),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_wsl()
        assert len(results) == 2
        assert results[0].status == Status.PASS
        assert "镜像网络" in results[0].message
        assert results[1].status == Status.PASS

    def test_wsl_no_mirrored(self, tmp_path):
        wslconfig = tmp_path / ".wslconfig"
        wslconfig.write_text("[wsl2]\n")

        def fake_run(cmd, timeout=5):
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._is_wsl", return_value=True),
            patch(
                "miloco_cli.commands.doctor._get_wslconfig_path", return_value=wslconfig
            ),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_wsl()
        assert results[0].status == Status.FAIL
        assert results[1].status == Status.WARN

    def test_wsl_commented_mirrored_fail(self, tmp_path):
        wslconfig = tmp_path / ".wslconfig"
        wslconfig.write_text("[wsl2]\n# networkingMode=mirrored\n")

        def fake_run(cmd, timeout=5):
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._is_wsl", return_value=True),
            patch(
                "miloco_cli.commands.doctor._get_wslconfig_path", return_value=wslconfig
            ),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_wsl()
        assert results[0].status == Status.FAIL
        assert "未启用" in results[0].message

    def test_wsl_config_not_exists(self, tmp_path):
        wslconfig = tmp_path / ".wslconfig"  # does not exist

        def fake_run(cmd, timeout=5):
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._is_wsl", return_value=True),
            patch(
                "miloco_cli.commands.doctor._get_wslconfig_path", return_value=wslconfig
            ),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            results = check_wsl()
        assert results[0].status == Status.FAIL
        assert ".wslconfig 不存在" in results[0].message


# ─── CLI 集成 ─────────────────────────────────────────────────────────────────


class TestDoctorCommand:
    def test_exit_code_0_on_pass(self, runner):
        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="macos"),
            patch("miloco_cli.commands.doctor._is_wsl", return_value=False),
        ):
            result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0
        assert "Miloco 环境诊断" in result.output

    def test_exit_code_1_on_fail(self, runner):
        def fake_run(cmd, timeout=5):
            if cmd == ["ufw", "status"]:
                return _ok("Status: active\n")
            if cmd == ["ufw", "status", "verbose"]:
                return _ok("Default: deny (incoming), allow (outgoing)\n")
            return _NOT_FOUND

        with (
            patch("miloco_cli.commands.doctor._detect_platform", return_value="linux"),
            patch("miloco_cli.commands.doctor._is_wsl", return_value=False),
            patch("miloco_cli.commands.doctor._run_cmd", side_effect=fake_run),
        ):
            result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 1
        assert "❌" in result.output
