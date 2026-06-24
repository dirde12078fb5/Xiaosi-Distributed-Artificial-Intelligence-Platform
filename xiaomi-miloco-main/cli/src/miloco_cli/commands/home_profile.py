"""home-profile 命令组：家庭档案 CRUD + commit + 迁移。

复杂结构（ops/mappings）走 ``--ops``/``--mappings`` JSON 字符串或 ``--ops-file``/
``--mappings-file``；含中文/换行/引号的 payload 一律用文件形式，避免 shell 转义出错。
"""

import json
import sys
from pathlib import Path

import click

from miloco_cli.output import print_result


def _load_json_arg(inline: str | None, file_path: str | None, label: str):
    if file_path:
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    if inline:
        return json.loads(inline)
    print(json.dumps({"error": f"missing {label}: pass --{label} or --{label}-file"}), file=sys.stderr)
    sys.exit(1)


@click.group("home-profile")
def home_profile_group():
    """家庭档案：列表 / 写入 / 提交渲染 / 主体归并 / 迁移。"""


@home_profile_group.command("list")
@click.option("--target", type=click.Choice(["profile", "candidates", "both"]), default="both")
@click.option("--pretty", is_flag=True)
def hp_list(target, pretty):
    """列条目（含 evidence_log，供去重）+ ready_to_promote。"""
    from miloco_cli.client import api_get

    data = api_get("/api/home-profile/entries", params={"target": target})
    print_result(data, pretty)


@home_profile_group.command("candidate-write")
@click.option("--ops", default=None, help="候选操作 JSON 数组")
@click.option("--ops-file", default=None, type=click.Path(exists=True), help="候选操作 JSON 文件")
@click.option("--pretty", is_flag=True)
def hp_candidate_write(ops, ops_file, pretty):
    """批量候选操作 add/merge。"""
    from miloco_cli.client import api_post

    ops_data = _load_json_arg(ops, ops_file, "ops")
    data = api_post("/api/home-profile/candidates:write", {"ops": ops_data})
    print_result(data, pretty)


@home_profile_group.command("profile-write")
@click.option("--ops", default=None, help="档案操作 JSON 数组")
@click.option("--ops-file", default=None, type=click.Path(exists=True), help="档案操作 JSON 文件")
@click.option("--user-edit", is_flag=True, help="用户直接编辑（source=user_told, confidence=1.0）")
@click.option("--pretty", is_flag=True)
def hp_profile_write(ops, ops_file, user_edit, pretty):
    """批量档案操作 add/merge/replace/delete。"""
    from miloco_cli.client import api_post

    ops_data = _load_json_arg(ops, ops_file, "ops")
    data = api_post("/api/home-profile/profile:write", {"ops": ops_data, "user_edit": user_edit})
    print_result(data, pretty)


@home_profile_group.command("commit")
@click.option("--pretty", is_flag=True)
def hp_commit(pretty):
    """完整 commit：维护（过期/归档/token 截断）+ 重渲染 canonical profile.md。"""
    from miloco_cli.client import api_post

    data = api_post("/api/home-profile/commit")
    print_result(data, pretty)


@home_profile_group.command("reassign")
@click.option("--mappings", default=None, help="主体归并映射 JSON 数组")
@click.option("--mappings-file", default=None, type=click.Path(exists=True), help="映射 JSON 文件")
@click.option("--pretty", is_flag=True)
def hp_reassign(mappings, mappings_file, pretty):
    """主体归并：把若干 subject_id/subject_name 重指到统一目标主体。
    
    既用于成员的不同称呼 → 同一 person_id 绑定，也用于统一空间/设备等非成员的
    subject_name（此时 to_subject_id 留空，仅收敛名称）。
    """
    from miloco_cli.client import api_post

    maps = _load_json_arg(mappings, mappings_file, "mappings")
    data = api_post("/api/home-profile/subject:reassign", {"mappings": maps})
    print_result(data, pretty)


@home_profile_group.command("show")
def hp_show():
    """stdout 输出 canonical profile.md（纯读、不重渲染）。"""
    from miloco_cli.client import api_get

    data = api_get("/api/home-profile/rendered")
    md = (data.get("data") or {}).get("markdown", "")
    print(md)


@home_profile_group.command("migrate")
@click.option("--profile-file", default=None, type=click.Path(exists=True), help="旧 .home-memory/profile.json")
@click.option("--candidates-file", default=None, type=click.Path(exists=True), help="旧 .home-memory/candidates.json")
@click.option("--pretty", is_flag=True)
def hp_migrate(profile_file, candidates_file, pretty):
    """一次性迁移旧 .home-memory 数据：subject→subject_name，保留 id/时间戳/evidence。"""
    from miloco_cli.client import api_post

    body = {
        "profile": _migrate_entries(profile_file),
        "candidates": _migrate_entries(candidates_file),
    }
    data = api_post("/api/home-profile/import", body)
    print_result(data, pretty)


def _migrate_entries(file_path: str | None) -> list[dict]:
    """读旧索引文件，把每条的 ``subject`` 映射成 ``subject_name``（id 留空）。

    特殊值 shared/general 原样保留为 subject_name。保留 id/confidence/
    evidence_count/first_seen/last_seen/source/evidence_log/archived。
    """
    if not file_path:
        return []
    raw = json.loads(Path(file_path).read_text(encoding="utf-8"))
    out = []
    for e in raw.get("entries", []):
        item = dict(e)
        if "subject" in item:
            item["subject_name"] = item.pop("subject")
        item.setdefault("subject_id", None)
        out.append(item)
    return out
