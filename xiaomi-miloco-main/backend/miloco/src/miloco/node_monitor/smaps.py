from __future__ import annotations

import logging
import os
import re
import time
from typing import Final

from miloco.node_monitor.mem_snapshot import TOP_N, CategoryStats, MemSnapshot

logger = logging.getLogger(__name__)

_HEADER_RE = re.compile(r"^[0-9a-f]+-[0-9a-f]+\s+[rwxps-]{4}\s")
_RSS_FIELD_RE = re.compile(r"^Rss:\s+(\d+)\s+kB")

# .so 与紧跟的匿名 region 之间允许的最大 gap；典型场景 gap=0（紧贴），
# 留 64 KB 容差给 guard page / 对齐
_NEIGHBOR_SO_GAP_MAX: Final[int] = 64 * 1024


def _normalize_name(raw: str) -> str:
    """smaps mapping name → 分类 key。"""
    if not raw:
        return "[anon]"
    if raw.startswith("[anon:"):
        return "[anon]"
    if raw.startswith("["):
        return raw
    return raw.rsplit("/", 1)[-1]


def _load_thread_stacks(task_dir: str) -> dict[int, str]:
    """读 /proc/<pid>/task/*/{stat,comm}，返回 {startstack 地址 → 线程名}。

    stat 第 28 字段是用户态栈顶；comm 单行就是线程名。任意一项读取失败，
    该线程静默跳过——监控代码不能因为线程瞬时退出而炸。
    """
    result: dict[int, str] = {}
    try:
        entries = os.listdir(task_dir)
    except OSError:
        return result
    for tid_name in entries:
        try:
            stat_text = open(os.path.join(task_dir, tid_name, "stat")).read()
            comm_text = open(os.path.join(task_dir, tid_name, "comm")).read()
        except OSError:
            continue
        # comm 在括号里可能含空格,只取最后一个 ')' 之后的部分
        close = stat_text.rfind(")")
        if close < 0:
            continue
        fields = stat_text[close + 2 :].split()
        if len(fields) < 26:
            continue
        try:
            startstack = int(fields[25])
        except ValueError:
            continue
        result[startstack] = comm_text.strip()
    return result


def _classify(
    raw: str,
    start: int,
    end: int,
    prev_raw: str,
    prev_end: int,
    thread_stacks: dict[int, str],
) -> str:
    """region → 分类 key。raw 非空走原 _normalize_name;raw 空时两维识别。

    优先级:线程栈反查 > 邻居 .so > [anon]。
    """
    if raw:
        return _normalize_name(raw)
    for sp, comm in thread_stacks.items():
        if start <= sp < end:
            return f"detect:[anon:{comm}]"
    if (
        prev_raw
        and _is_so_path(prev_raw)
        and 0 <= start - prev_end <= _NEIGHBOR_SO_GAP_MAX
    ):
        return f"detect:[anon:{prev_raw.rsplit('/', 1)[-1]}]"
    return "[anon]"


def _is_so_path(raw: str) -> bool:
    return raw.endswith(".so") or ".so." in raw


def parse_smaps(
    path: str = "/proc/self/smaps",
    task_dir: str | None = None,
) -> MemSnapshot:
    """解析 /proc/<pid>/smaps,按 mapping basename 归并,取 top-N by RSS。

    task_dir 提供时(如 "/proc/self/task"),对无名匿名 region 做两维归属识别:
    ① startstack 落在该 region → detect:[anon:线程名]
    ② 上一条映射是 .so 且 gap ≤ 64KB → detect:[anon:libfoo.so]
    两维都命中时线程栈优先。识别只作用于 raw 为空的匿名 region;内核已打的
    [anon:libc_malloc] 等保持原有折叠行为(归 [anon])。
    """
    ts = time.time()
    raw_rss: dict[str, int] = {}
    raw_count: dict[str, int] = {}
    current_name: str | None = None
    prev_raw: str = ""
    prev_end: int = 0
    thread_stacks = _load_thread_stacks(task_dir) if task_dir else {}

    with open(path) as f:
        for line in f:
            if _HEADER_RE.match(line):
                parts = line.rstrip("\n").split(None, 5)
                addr_range = parts[0]
                raw = parts[5] if len(parts) >= 6 else ""
                start_hex, end_hex = addr_range.split("-")
                start = int(start_hex, 16)
                end = int(end_hex, 16)
                current_name = _classify(
                    raw, start, end, prev_raw, prev_end, thread_stacks
                )
                raw_count[current_name] = raw_count.get(current_name, 0) + 1
                prev_raw, prev_end = raw, end
                continue
            if current_name is None:
                continue
            m = _RSS_FIELD_RE.match(line)
            if m is None:
                continue
            raw_rss[current_name] = raw_rss.get(current_name, 0) + int(m.group(1))

    names_sorted = sorted(raw_rss.keys(), key=lambda n: raw_rss[n], reverse=True)
    top = names_sorted[:TOP_N]
    other = names_sorted[TOP_N:]

    categories = [
        CategoryStats(
            name=n,
            rss_kb=raw_rss.get(n, 0),
            count=raw_count.get(n, 0),
        )
        for n in top
    ]
    other_rss = sum(raw_rss.get(n, 0) for n in other)
    other_count = sum(raw_count.get(n, 0) for n in other)
    total_rss = sum(raw_rss.values())

    return MemSnapshot(
        ts=ts,
        total_rss_kb=total_rss,
        categories=categories,
        other_rss_kb=other_rss,
        other_count=other_count,
    )
