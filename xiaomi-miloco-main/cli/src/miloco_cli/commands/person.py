"""person 命令组：list / add / update / delete。

v2 变更(2026-05-18):移除 ``person biometric add/delete`` 子命令。
v1 那条路径已被 ``identity register`` 系列取代(body ReID 而非 face,见
[plugins/skills/miloco-miot-identity-register](miloco-miot-identity-register));
miloco-cli 不再保留废弃命令以免误导。
"""

import json
import sys

import click

from miloco_cli.output import print_result


@click.group("person")
def person_group():
    """家庭成员档案 CRUD：列表 / 添加 / 更新 / 删除。

    样本注册(给某人录身形)请用 ``miloco-cli identity register ...``。
    """


@person_group.command("list")
@click.option("--pretty", is_flag=True)
def person_list(pretty):
    """列出所有家庭成员。"""
    from miloco_cli.client import api_get

    data = api_get("/api/identity/persons")
    print_result(data, pretty)


@person_group.command("add")
@click.option("--name", required=True, help="真名")
@click.option("--role", default=None, help="家庭角色，如爸爸、妈妈")
@click.option("--pretty", is_flag=True)
def person_add(name, role, pretty):
    """添加家庭成员档案(只建 DB 行，不录样本)。"""
    from miloco_cli.client import api_post

    payload: dict = {"name": name}
    if role:
        payload["role"] = role

    data = api_post("/api/identity/persons", payload)
    print_result(data, pretty)


@person_group.command("update")
@click.argument("person_id")
@click.option("--name", default=None, help="新真名")
@click.option("--role", default=None, help='新家庭角色（传空串 "" 清空已设角色）')
@click.option("--pretty", is_flag=True)
def person_update(person_id, name, role, pretty):
    """更新家庭成员信息（部分更新）。"""
    from miloco_cli.client import api_put

    payload: dict = {}
    if name:
        payload["name"] = name
    # role is None = 未传 --role(本次不改)；传了(含空串→清空) → 入 body,后端按是否带 role 区分
    if role is not None:
        payload["role"] = role

    if not payload:
        print(json.dumps({"error": "no fields to update"}), file=sys.stderr)
        sys.exit(1)

    data = api_put(f"/api/identity/persons/{person_id}", payload)
    print_result(data, pretty)


@person_group.command("delete")
@click.argument("person_id")
@click.option("--pretty", is_flag=True)
def person_delete(person_id, pretty):
    """删除家庭成员(级联清除其所有样本 + identity_lib/persons/<id> 目录)。"""
    from miloco_cli.client import api_delete

    data = api_delete(f"/api/identity/persons/{person_id}")
    print_result(data, pretty)
