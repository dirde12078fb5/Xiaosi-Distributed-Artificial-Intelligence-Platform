"""scene 命令组：list / trigger / create。"""

import json
import sys

import click

from miloco_cli.output import print_result


@click.group("scene")
def scene_group():
    """场景操作：列表 / 触发 / 创建。"""


@scene_group.command("list")
@click.option("--pretty", is_flag=True)
def scene_list(pretty):
    """列出所有场景（从 home_info 缓存读取）。"""
    from miloco_cli.home_info import list_scenes
    scenes = list_scenes()
    print_result({"scenes": scenes}, pretty)


@scene_group.command("trigger")
@click.argument("scene_id")
@click.option("--pretty", is_flag=True)
def scene_trigger(scene_id, pretty):
    """触发指定场景。"""
    from miloco_cli.client import api_post

    data = api_post(f"/api/miot/scenes/{scene_id}/trigger", None)
    print_result(data, pretty)


@scene_group.command("create")
@click.option("--name", required=True, help="场景名称")
@click.option(
    "--action",
    "actions",
    multiple=True,
    required=True,
    help="场景动作 JSON，可重复多次。例：--action '{\"did\":\"xxx\",\"iid\":\"prop.2.1\",\"value\":true}'",
)
@click.option("--pretty", is_flag=True)
def scene_create(name, actions, pretty):
    """创建自动化场景。"""
    from miloco_cli.client import api_post

    parsed_actions = []
    for raw in actions:
        try:
            parsed_actions.append(json.loads(raw))
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"invalid action JSON: {e}"}), file=sys.stderr)
            sys.exit(1)

    data = api_post("/api/miot/scenes", {"name": name, "actions": parsed_actions})
    print_result(data, pretty)
