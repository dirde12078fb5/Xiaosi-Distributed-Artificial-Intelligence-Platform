"""notify 命令组：米家 App 推送。"""

import click

from miloco_cli.output import print_result


@click.group("notify")
def notify_group():
    """米家 App 通知：发送推送消息到绑定 miloco 的管理员手机（v1 临时方案）。"""


@notify_group.command("push")
@click.option("--text", required=True, help="推送文案")
@click.option("--pretty", is_flag=True)
def notify_push(text, pretty):
    """发送米家 App 推送（调用 /api/miot/send_notify）。"""
    from miloco_cli.client import api_post

    data = api_post("/api/miot/send_notify", {"notify": text})
    print_result(data, pretty)
