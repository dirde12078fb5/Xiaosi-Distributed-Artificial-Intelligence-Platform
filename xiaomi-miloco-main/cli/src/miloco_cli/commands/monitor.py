"""monitor 命令组：查看运行时监控状态。"""

from __future__ import annotations

import click

from miloco_cli.output import print_result


@click.group("monitor")
def monitor_group():
    """节点监控：查看运行时节点状态。"""


@monitor_group.command("status")
@click.option("--pretty", is_flag=True, help="表格格式输出")
@click.option("--name", default=None, help="查看单个节点")
def monitor_status(pretty, name):
    """查询节点运行状态。"""
    from miloco_cli.client import api_get

    if name:
        data = api_get(f"/api/monitor/nodes/{name}")
    else:
        data = api_get("/api/monitor/nodes")

    if pretty and not name:
        _print_table(data)
    else:
        print_result(data, pretty)


@monitor_group.command("resources")
@click.option("--pretty", is_flag=True, help="JSON 格式化输出")
def monitor_resources(pretty):
    """查询系统资源使用情况（CPU / 内存 / 磁盘等）。"""
    from miloco_cli.client import api_get

    data = api_get("/api/monitor/resources")
    print_result(data, pretty)


def _print_table(data: dict) -> None:
    """Tabular output: NAME / LIFE / FPS / RTF / LAT_P95 / IDLE / LAST_ERR"""
    nodes = data.get("nodes", [])
    if not nodes:
        print("No nodes registered.")
        return

    hdr = f"{'NAME':<24} {'LIFE':<12} {'FPS':>8} {'RTF':>8} {'LAT_P95':>10} {'IDLE':>8} LAST_ERR"
    print(hdr)
    print("-" * len(hdr))

    for n in nodes:
        name = n.get("name", "?")
        life = n.get("lifecycle", "?")
        kind = n.get("kind", "")

        fps = _fmt_float(n.get("fps_60s"), 2) if kind != "service" else "-"
        rtf = _fmt_float(n.get("rtf_60s"), 3) if kind == "window" else "-"
        lat = _fmt_float(n.get("p95_latency_ms"), 1) if kind == "window" else "-"
        idle = _fmt_idle(n.get("idle_s"))
        err = (n.get("last_error") or "")[:40]

        print(f"{name:<24} {life:<12} {fps:>8} {rtf:>8} {lat:>10} {idle:>8} {err}")


def _fmt_float(val, decimals: int) -> str:
    if val is None:
        return "-"
    return f"{val:.{decimals}f}"


def _fmt_idle(val) -> str:
    if val is None:
        return "-"
    val = float(val)
    if val < 60:
        return f"{val:.0f}s"
    if val < 3600:
        return f"{val / 60:.0f}m"
    return f"{val / 3600:.1f}h"
