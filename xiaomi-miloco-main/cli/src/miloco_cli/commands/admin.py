"""admin 命令组：status / home-info / cost"""

import json
import sys

import click

from miloco_cli.output import print_result


@click.group("admin")
def admin_group():
    """系统管理：状态 / 缓存 / 模型管理 / 成本。"""


@admin_group.command("status")
@click.option("--pretty", is_flag=True)
def admin_status(pretty):
    """系统状态（MiOT 连接、SQLite、感知模型、规则引擎）。"""
    from miloco_cli.client import api_get

    data = api_get("/api/admin/status")
    print_result(data, pretty)


@admin_group.command("home-info")
@click.option("--pretty", is_flag=True)
def admin_home_info(pretty):
    """从后端拉取 home_info 并展示摘要。"""
    from miloco_cli.home_info import get_home_info

    info = get_home_info()
    print_result({
        "devices": len(info.get("devices", [])),
        "areas": len(info.get("areas", [])),
        "scenes": len(info.get("scenes", [])),
        "persons": len(info.get("persons", [])),
    }, pretty)


@admin_group.command("cost")
@click.option(
    "--period",
    type=click.Choice(["today", "month"]),
    default="today",
    show_default=True,
    help="统计周期",
)
@click.option("--pretty", is_flag=True)
def admin_cost(period, pretty):
    """感知 LLM 调用成本统计。"""
    print(json.dumps({"code": 501, "message": "cost statistics not yet supported"}), file=sys.stderr)
    sys.exit(1)

