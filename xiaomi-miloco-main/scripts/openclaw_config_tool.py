#!/usr/bin/env python3
"""openclaw config 通用包装：get / set / unset / append / remove / merge。

  ./scripts/openclaw_config_tool.py get    tools.alsoAllow
  ./scripts/openclaw_config_tool.py set    tools.profile coding
  ./scripts/openclaw_config_tool.py set    gateway.port 19001
  ./scripts/openclaw_config_tool.py set    tools.allow '["read","write"]'
  ./scripts/openclaw_config_tool.py append tools.alsoAllow foo bar
  ./scripts/openclaw_config_tool.py remove tools.alsoAllow foo
  ./scripts/openclaw_config_tool.py merge  agents.defaults.models '{"openai/gpt-5.4":{}}'
  ./scripts/openclaw_config_tool.py unset  plugins.entries.brave.config.webSearch.apiKey

任何子命令都可加 --dry-run，只走 openclaw schema 校验不写盘。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys


def run_openclaw(args: list[str]) -> str:
    result = subprocess.run(["openclaw", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    return result.stdout


def get_value(path: str, missing_ok: bool = False):
    result = subprocess.run(
        ["openclaw", "config", "get", path, "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        if missing_ok and "Config path not found" in result.stderr:
            return None
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    raw = result.stdout.strip()
    if not raw or raw == "null":
        return None
    return json.loads(raw)


def parse_value(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def with_dry_run(args: list[str], dry_run: bool) -> list[str]:
    return args + (["--dry-run"] if dry_run else [])


def cmd_get(args: argparse.Namespace) -> None:
    value = get_value(args.path)
    print(json.dumps(value, ensure_ascii=False, indent=2))


def cmd_set(args: argparse.Namespace) -> None:
    parsed = parse_value(args.value)
    serialized = json.dumps(parsed, ensure_ascii=False)
    cli = ["config", "set", args.path, serialized, "--strict-json"]
    sys.stdout.write(run_openclaw(with_dry_run(cli, args.dry_run)))


def cmd_unset(args: argparse.Namespace) -> None:
    cli = ["config", "unset", args.path]
    sys.stdout.write(run_openclaw(with_dry_run(cli, args.dry_run)))


def cmd_append(args: argparse.Namespace) -> None:
    current = get_value(args.path, missing_ok=True)
    if current is None:
        current = []
    elif not isinstance(current, list):
        sys.exit(f"路径 {args.path} 不是数组（当前值类型：{type(current).__name__}），append 不适用")
    added = [item for item in args.items if item not in current]
    if not added:
        print("没有新条目需要追加，全部已存在")
        return
    new_value = current + added
    print(f"追加 {added} → {args.path}（共 {len(new_value)} 项）")
    cli = ["config", "set", args.path, json.dumps(new_value, ensure_ascii=False), "--strict-json"]
    sys.stdout.write(run_openclaw(with_dry_run(cli, args.dry_run)))


def cmd_remove(args: argparse.Namespace) -> None:
    current = get_value(args.path, missing_ok=True)
    if current is None:
        print(f"路径 {args.path} 不存在或为空，无需移除")
        return
    if not isinstance(current, list):
        sys.exit(f"路径 {args.path} 不是数组（当前值类型：{type(current).__name__}），remove 不适用")
    to_remove = set(args.items)
    new_value = [item for item in current if item not in to_remove]
    removed = [item for item in args.items if item in current]
    if not removed:
        print("没有匹配条目可移除")
        return
    print(f"移除 {removed} ← {args.path}（剩 {len(new_value)} 项）")
    cli = ["config", "set", args.path, json.dumps(new_value, ensure_ascii=False), "--strict-json"]
    sys.stdout.write(run_openclaw(with_dry_run(cli, args.dry_run)))


def cmd_merge(args: argparse.Namespace) -> None:
    try:
        parsed = json.loads(args.value)
    except json.JSONDecodeError as e:
        sys.exit(f"merge 要求 value 是合法 JSON 对象：{e}")
    if not isinstance(parsed, dict):
        sys.exit("merge 要求 value 是 JSON 对象（dict），数组请用 append/set")
    cli = ["config", "set", args.path, json.dumps(parsed, ensure_ascii=False), "--strict-json", "--merge"]
    sys.stdout.write(run_openclaw(with_dry_run(cli, args.dry_run)))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="只走 schema 校验不写盘")
    sub = parser.add_subparsers(dest="cmd", metavar="子命令")

    g = sub.add_parser("get", help="读取并输出 JSON")
    g.add_argument("path")
    g.set_defaults(func=cmd_get)

    s = sub.add_parser("set", help="整体写入（标量/数组/对象都走替换；值按 JSON 解析失败则当字符串）")
    s.add_argument("path")
    s.add_argument("value")
    s.set_defaults(func=cmd_set)

    u = sub.add_parser("unset", help="删除指定路径")
    u.add_argument("path")
    u.set_defaults(func=cmd_unset)

    a = sub.add_parser("append", help="数组追加（自动去重）")
    a.add_argument("path")
    a.add_argument("items", nargs="+")
    a.set_defaults(func=cmd_append)

    r = sub.add_parser("remove", help="数组按值移除")
    r.add_argument("path")
    r.add_argument("items", nargs="+")
    r.set_defaults(func=cmd_remove)

    m = sub.add_parser("merge", help="对象浅合并（透传 openclaw --merge）")
    m.add_argument("path")
    m.add_argument("value", help="JSON 对象字符串")
    m.set_defaults(func=cmd_merge)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return
    if shutil.which("openclaw") is None:
        sys.exit("未找到 openclaw CLI，请确认已安装并在 PATH 中")
    args.func(args)


if __name__ == "__main__":
    main()
