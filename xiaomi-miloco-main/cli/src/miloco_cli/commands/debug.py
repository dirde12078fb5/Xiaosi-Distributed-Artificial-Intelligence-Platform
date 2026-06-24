"""debug 命令组:omni log debug 开关 + 打包排查数据。

子命令均走 backend HTTP。on/off 同步创建/删除 .debug_observability 文件,
重启后从文件 flag 恢复状态。
"""

import click

from miloco_cli.output import print_result


@click.group("debug")
def debug_group():
    """Omni log debug 开关 + 打包排查数据。"""


@debug_group.command("status")
@click.option("--pretty", is_flag=True)
def debug_status(pretty):
    """查询 debug 开关状态:enabled / source / runtime_override / file_flag_present。"""
    from miloco_cli.client import api_get

    data = api_get("/api/admin/debug")
    print_result(data, pretty)


@debug_group.command("on")
@click.option("--pretty", is_flag=True)
def debug_on(pretty):
    """开启 debug 并创建 .debug_observability(持久,重启后仍生效)。"""
    from miloco_cli.client import api_post

    data = api_post("/api/admin/debug", {"enabled": True})
    print_result(data, pretty)


@debug_group.command("off")
@click.option("--pretty", is_flag=True)
def debug_off(pretty):
    """关闭 debug 并删除 .debug_observability(持久,重启后仍关闭)。"""
    from miloco_cli.client import api_post

    data = api_post("/api/admin/debug", {"enabled": False})
    print_result(data, pretty)


@debug_group.command("log-pack")
@click.option("--pretty", is_flag=True)
def debug_log_pack(pretty):
    """打包 trace db / jsonl / log 到 $MILOCO_HOME/packs/。

    LRU 保留最新 2 个;体量 > 500MB 报错并打印各组件 size。
    """
    from miloco_cli.client import api_post

    data = api_post("/api/admin/debug/log-pack")
    print_result(data, pretty)
