"""doctor 命令：环境诊断，检测防火墙和 WSL 网络配置。"""

from __future__ import annotations

import platform
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import click


class Status(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    name: str
    status: Status
    message: str
    fix_hint: str | None = None


# ─── 平台检测 ────────────────────────────────────────────────────────────────


def _is_wsl() -> bool:
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except (FileNotFoundError, PermissionError):
        return False


def _detect_platform() -> str:
    if platform.system() == "Darwin":
        return "macos"
    if _is_wsl():
        return "wsl"
    if platform.system() == "Linux":
        return "linux"
    return "unknown"


# ─── 命令执行 ────────────────────────────────────────────────────────────────


@dataclass
class CmdResult:
    found: bool
    rc: int
    stdout: str
    stderr: str


_NOT_FOUND = CmdResult(found=False, rc=-1, stdout="", stderr="")


def _run_cmd(cmd: list[str], timeout: int = 5) -> CmdResult:
    if not shutil.which(cmd[0]):
        return _NOT_FOUND
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout)
        return CmdResult(found=True, rc=r.returncode, stdout=r.stdout, stderr=r.stderr)
    except (subprocess.TimeoutExpired, OSError):
        return CmdResult(found=True, rc=-1, stdout="", stderr="")


# ─── 防火墙检测 ───────────────────────────────────────────────────────────────


def check_firewall() -> list[CheckResult]:
    plat = _detect_platform()
    results: list[CheckResult] = []

    if plat == "macos":
        results.append(CheckResult(
            name="防火墙 (macOS)",
            status=Status.PASS,
            message="macOS 默认不阻断 UDP 入站回包，通常无需配置",
        ))
        return results

    # Linux / WSL: 检测 ufw
    ufw_result = _run_cmd(["ufw", "status"])
    if not ufw_result.found:
        pass  # ufw 未安装，继续检测下一个防火墙
    elif ufw_result.rc != 0:
        results.append(CheckResult(
            name="ufw 状态",
            status=Status.WARN,
            message="ufw 已安装但无法读取状态（权限不足），请用 sudo 重试",
            fix_hint="sudo ufw status verbose",
        ))
        return results
    elif ufw_result.rc == 0:
        out = ufw_result.stdout
        if "inactive" in out.lower():
            results.append(CheckResult(
                name="ufw 状态",
                status=Status.PASS,
                message="ufw 未激活，不阻断流量",
            ))
        elif "status: active" in out.lower():
            verbose = _run_cmd(["ufw", "status", "verbose"])
            out2 = verbose.stdout if verbose.found and verbose.rc == 0 else ""
            if "deny (incoming)" in out2.lower() or "reject (incoming)" in out2.lower():
                results.append(CheckResult(
                    name="ufw UDP 入站",
                    status=Status.FAIL,
                    message="ufw 默认拒绝入站流量，PPCS UDP 包会被丢弃",
                    fix_hint=(
                        "允许局域网 UDP 入站（推荐，限定子网）:\n"
                        "  sudo ufw allow from 192.168.0.0/16 proto udp\n"
                        "\n"
                        "或允许所有 UDP 入站（宽松）:\n"
                        "  sudo ufw allow proto udp from any"
                    ),
                ))
            else:
                results.append(CheckResult(
                    name="ufw UDP 入站",
                    status=Status.PASS,
                    message="ufw 默认允许入站流量",
                ))
        else:
            results.append(CheckResult(
                name="ufw 状态",
                status=Status.WARN,
                message="ufw 输出格式无法识别，请手动检查: sudo ufw status verbose",
            ))
        return results

    # Linux: 检测 firewalld
    fwd_result = _run_cmd(["firewall-cmd", "--state"])
    if not fwd_result.found:
        pass  # firewalld 未安装，继续检测下一个
    elif fwd_result.rc != 0 and "not running" in (fwd_result.stdout + fwd_result.stderr).lower():
        pass  # firewalld 已安装但未运行，继续检测 iptables
    elif fwd_result.rc != 0:
        results.append(CheckResult(
            name="firewalld 状态",
            status=Status.WARN,
            message="firewalld 已安装但无法读取状态（权限不足），请用 sudo 重试",
            fix_hint="sudo firewall-cmd --state",
        ))
        return results
    elif fwd_result.rc == 0 and "running" in fwd_result.stdout.lower():
        zone_result = _run_cmd(["firewall-cmd", "--get-default-zone"])
        zone = zone_result.stdout.strip()
        if zone_result.rc != 0 or not zone:
            results.append(CheckResult(
                name="firewalld UDP 入站",
                status=Status.WARN,
                message="无法获取 firewalld 默认 zone（权限不足或命令异常），请手动检查",
                fix_hint="sudo firewall-cmd --get-default-zone\nsudo firewall-cmd --list-all",
            ))
            return results
        info_result = _run_cmd(["firewall-cmd", f"--zone={zone}", "--list-all"])
        info = info_result.stdout
        info_lower = info.lower()
        lines = info_lower.splitlines()
        target_line = next((ln for ln in lines if "target:" in ln), "")
        target_accept = "accept" in target_line
        protocols_line = next((ln for ln in lines if ln.strip().startswith("protocols:")), "")
        has_protocol_udp = "udp" in protocols_line
        ports_line = next((ln for ln in lines if ln.strip().startswith("ports:")), "")
        has_port_udp = "udp" in ports_line
        if "drop" in target_line or "reject" in target_line:
            results.append(CheckResult(
                name="firewalld UDP 入站",
                status=Status.FAIL,
                message=f"firewalld zone '{zone}' 目标为 DROP/REJECT，UDP 入站被丢弃",
                fix_hint=(
                    f"允许局域网 UDP（推荐）:\n"
                    f"  sudo firewall-cmd --zone={zone} --add-rich-rule="
                    f"'rule family=ipv4 source address=192.168.0.0/16 protocol value=udp accept' --permanent\n"
                    f"  sudo firewall-cmd --reload"
                ),
            ))
        elif target_accept or has_protocol_udp:
            results.append(CheckResult(
                name="firewalld UDP 入站",
                status=Status.PASS,
                message=f"firewalld zone '{zone}' 允许 UDP 流量",
            ))
        elif has_port_udp:
            results.append(CheckResult(
                name="firewalld UDP 入站",
                status=Status.WARN,
                message=(
                    f"firewalld zone '{zone}' 仅放行特定端口的 UDP，"
                    f"PPCS 使用随机高位端口可能被阻断"
                ),
                fix_hint=(
                    f"确认 UDP 是否放行:\n"
                    f"  sudo firewall-cmd --zone={zone} --list-all\n\n"
                    f"若需放行局域网 UDP:\n"
                    f"  sudo firewall-cmd --zone={zone} --add-rich-rule="
                    f"'rule family=ipv4 source address=192.168.0.0/16 protocol value=udp accept' --permanent\n"
                    f"  sudo firewall-cmd --reload"
                ),
            ))
        else:
            results.append(CheckResult(
                name="firewalld UDP 入站",
                status=Status.WARN,
                message=f"firewalld zone '{zone}' target 为 default，未找到显式 UDP 放行规则，可能阻断 PPCS UDP",
                fix_hint=(
                    f"确认 UDP 是否放行:\n"
                    f"  sudo firewall-cmd --zone={zone} --list-all\n\n"
                    f"若需放行局域网 UDP:\n"
                    f"  sudo firewall-cmd --zone={zone} --add-rich-rule="
                    f"'rule family=ipv4 source address=192.168.0.0/16 protocol value=udp accept' --permanent\n"
                    f"  sudo firewall-cmd --reload"
                ),
            ))
        return results

    # Linux: 检测原生 iptables
    ipt_result = _run_cmd(["iptables", "-L", "INPUT", "-n"])
    if not ipt_result.found:
        pass  # iptables 未安装
    elif ipt_result.rc != 0:
        results.append(CheckResult(
            name="iptables 状态",
            status=Status.WARN,
            message="iptables 已安装但无法读取规则（权限不足），请用 sudo 重试",
            fix_hint="sudo iptables -L INPUT -n",
        ))
        return results
    elif ipt_result.rc == 0:
        out = ipt_result.stdout
        lines = out.splitlines()
        policy_drop = bool(
            lines and ("policy drop" in lines[0].lower() or "policy reject" in lines[0].lower())
        )
        has_udp_block = any(
            "udp" in line.lower() and ("drop" in line.lower() or "reject" in line.lower())
            for line in lines
        )
        udp_accept_lines = [
            line for line in lines
            if "udp" in line.lower() and "accept" in line.lower()
        ]
        has_blanket_accept = any(
            "accept" in line.lower()
            and "all" in line.lower().split()
            and "established" not in line.lower()
            for line in lines[1:]
        )
        has_udp_accept = bool(udp_accept_lines) or has_blanket_accept
        udp_accept_all_port_limited = (
            bool(udp_accept_lines)
            and not has_blanket_accept
            and all(
                "dpt:" in line.lower() or "dpts:" in line.lower()
                for line in udp_accept_lines
            )
        )
        if has_udp_block and has_udp_accept:
            results.append(CheckResult(
                name="iptables UDP 入站",
                status=Status.WARN,
                message=(
                    "iptables INPUT 链同时存在 UDP ACCEPT 与 UDP DROP/REJECT 规则，"
                    "实际行为取决于规则顺序，请人工核对"
                ),
                fix_hint=(
                    "查看带行号的完整规则:\n"
                    "  sudo iptables -L INPUT -nv --line-numbers"
                ),
            ))
        elif has_udp_block or (policy_drop and not has_udp_accept):
            msg = (
                "iptables INPUT 链默认策略为 DROP 且无 UDP ACCEPT 规则" if policy_drop and not has_udp_block
                else "iptables INPUT 链存在 DROP/REJECT UDP 规则"
            )
            results.append(CheckResult(
                name="iptables UDP 入站",
                status=Status.FAIL,
                message=f"{msg}，PPCS UDP 包会被丢弃",
                fix_hint=(
                    "允许局域网 UDP 入站:\n"
                    "  sudo iptables -I INPUT -p udp -s 192.168.0.0/16 -j ACCEPT\n"
                    "\n"
                    "持久化（Ubuntu/Debian）:\n"
                    "  sudo apt install iptables-persistent && sudo netfilter-persistent save"
                ),
            ))
        elif policy_drop and udp_accept_all_port_limited:
            results.append(CheckResult(
                name="iptables UDP 入站",
                status=Status.WARN,
                message="iptables 仅放行特定端口的 UDP，PPCS 使用随机高位端口可能被阻断",
                fix_hint=(
                    "允许局域网 UDP 入站:\n"
                    "  sudo iptables -I INPUT -p udp -s 192.168.0.0/16 -j ACCEPT\n"
                    "\n"
                    "持久化（Ubuntu/Debian）:\n"
                    "  sudo apt install iptables-persistent && sudo netfilter-persistent save"
                ),
            ))
        else:
            results.append(CheckResult(
                name="iptables UDP 入站",
                status=Status.PASS,
                message="iptables INPUT 链未阻断 UDP 入站",
            ))
        return results

    results.append(CheckResult(
        name="防火墙",
        status=Status.PASS,
        message="未检测到 ufw、firewalld 或 iptables，UDP 入站不受防火墙限制",
    ))
    return results


# ─── WSL 检测 ─────────────────────────────────────────────────────────────────


def check_wsl() -> list[CheckResult]:
    if not _is_wsl():
        return []

    results: list[CheckResult] = []

    # 检测镜像网络模式
    wslconfig = _get_wslconfig_path()
    if wslconfig and wslconfig.exists():
        content = wslconfig.read_text(errors="ignore")
        mirrored = False
        in_wsl2 = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("["):
                in_wsl2 = stripped.lower() == "[wsl2]"
                continue
            if stripped.startswith("#") or stripped.startswith(";"):
                continue
            if in_wsl2 and "networkingmode" in stripped.replace(" ", "").lower():
                if "=mirrored" in stripped.replace(" ", "").lower():
                    mirrored = True
                    break
        if mirrored:
            results.append(CheckResult(
                name="WSL 网络模式",
                status=Status.PASS,
                message="已启用镜像网络模式 (networkingMode=mirrored)",
            ))
        else:
            results.append(CheckResult(
                name="WSL 网络模式",
                status=Status.FAIL,
                message="未启用镜像网络模式，WSL 无法接收宿主机局域网 UDP 包",
                fix_hint=(
                    "在 Windows 侧编辑 %USERPROFILE%\\.wslconfig:\n"
                    "  [wsl2]\n"
                    "  networkingMode=mirrored\n"
                    "\n"
                    "保存后执行: wsl --shutdown && wsl"
                ),
            ))
    elif wslconfig:
        results.append(CheckResult(
            name="WSL 网络模式",
            status=Status.FAIL,
            message=f".wslconfig 不存在 ({wslconfig})，默认 NAT 模式无法接收局域网 UDP",
            fix_hint=(
                "创建 %USERPROFILE%\\.wslconfig:\n"
                "  [wsl2]\n"
                "  networkingMode=mirrored\n"
                "\n"
                "保存后执行: wsl --shutdown && wsl"
            ),
        ))
    else:
        results.append(CheckResult(
            name="WSL 网络模式",
            status=Status.WARN,
            message="无法定位 .wslconfig（Windows 用户目录检测失败）",
            fix_hint=(
                "请手动确认 %USERPROFILE%\\.wslconfig 中有:\n"
                "  [wsl2]\n"
                "  networkingMode=mirrored"
            ),
        ))

    # 检测 Hyper-V 防火墙默认入站策略
    hv_result = _run_cmd([
        "powershell.exe", "-NoProfile", "-Command",
        "(Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore "
        "-Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}').DefaultInboundAction",
    ], timeout=15)
    if hv_result.found and hv_result.rc == 0:
        action = hv_result.stdout.strip().lower()
        if action == "allow":
            results.append(CheckResult(
                name="Hyper-V 防火墙",
                status=Status.PASS,
                message="Hyper-V 防火墙 DefaultInboundAction=Allow，UDP 入站已放行",
            ))
        else:
            results.append(CheckResult(
                name="Hyper-V 防火墙",
                status=Status.FAIL,
                message=f"Hyper-V 防火墙 DefaultInboundAction={action or 'Block'}，UDP 入站被阻断",
                fix_hint=(
                    "在 Windows PowerShell (管理员) 执行:\n"
                    "  Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' "
                    "-DefaultInboundAction Allow"
                ),
            ))
    else:
        results.append(CheckResult(
            name="Hyper-V 防火墙",
            status=Status.WARN,
            message="无法检测 Hyper-V 防火墙（powershell.exe 不可用、无权限或启动超时）",
            fix_hint=(
                "如首次运行较慢可重试。\n"
                "或在 Windows PowerShell (管理员) 手动检查:\n"
                "  Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore "
                "-Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}'\n"
                "确认 DefaultInboundAction 为 Allow"
            ),
        ))

    return results


def _get_wslconfig_path() -> Path | None:
    ps_result = _run_cmd(
        [
            "powershell.exe", "-NoProfile", "-Command",
            "[Console]::OutputEncoding=[Text.Encoding]::UTF8; $env:USERPROFILE",
        ],
        timeout=15,
    )
    if ps_result.found and ps_result.rc == 0:
        profile = ps_result.stdout.strip().lstrip("\ufeff")
        if profile:
            wsl_result = _run_cmd(["wslpath", "-u", profile])
            if wsl_result.found and wsl_result.rc == 0 and wsl_result.stdout.strip():
                return Path(wsl_result.stdout.strip()) / ".wslconfig"

    # fallback: 扫描 /mnt/c/Users/
    users_dir = Path("/mnt/c/Users")
    skip = {"Public", "Default", "Default User", "All Users"}
    try:
        if not users_dir.exists():
            return None

        def _safe_mtime(p: Path) -> float:
            try:
                return p.stat().st_mtime
            except OSError:
                return 0

        dirs = sorted(
            (d for d in users_dir.iterdir() if d.is_dir() and d.name not in skip),
            key=_safe_mtime,
            reverse=True,
        )
        for d in dirs:
            p = d / ".wslconfig"
            if p.exists():
                return p
        if dirs:
            return dirs[0] / ".wslconfig"
    except OSError:
        pass
    return None


# ─── 输出渲染 ─────────────────────────────────────────────────────────────────

_STATUS_ICON = {
    Status.PASS: "✅",
    Status.WARN: "⚠️ ",
    Status.FAIL: "❌",
}


def _render_result(r: CheckResult) -> None:
    icon = _STATUS_ICON[r.status]
    click.echo(f"  {icon} {r.name}")
    click.echo(f"     {r.message}")
    if r.fix_hint:
        click.echo()
        click.echo("     \U0001f4a1 修复建议:")
        for line in r.fix_hint.split("\n"):
            click.echo(f"        {line}")
    click.echo()


def _render_summary(results: list[CheckResult]) -> None:
    click.echo("─" * 50)
    counts = {s: 0 for s in Status}
    for r in results:
        counts[r.status] += 1
    parts = []
    if counts[Status.PASS]:
        parts.append(f"✅ {counts[Status.PASS]} pass")
    if counts[Status.WARN]:
        parts.append(f"⚠️  {counts[Status.WARN]} warn")
    if counts[Status.FAIL]:
        parts.append(f"❌ {counts[Status.FAIL]} fail")
    click.echo(f"  {' / '.join(parts)}")
    click.echo()


# ─── 命令定义 ─────────────────────────────────────────────────────────────────


@click.command("doctor")
def doctor_cmd():
    """环境诊断：检测防火墙、WSL 网络等影响摄像头连接的配置。"""
    click.echo()
    click.echo("\U0001fa7a Miloco 环境诊断")
    click.echo("─" * 50)

    all_results: list[CheckResult] = []

    for r in check_firewall():
        _render_result(r)
        all_results.append(r)

    for r in check_wsl():
        _render_result(r)
        all_results.append(r)

    _render_summary(all_results)

    if any(r.status == Status.FAIL for r in all_results):
        raise SystemExit(1)
