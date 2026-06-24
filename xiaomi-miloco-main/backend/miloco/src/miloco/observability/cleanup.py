"""SQLite 表 + jsonl 目录的过期清理。

`cleanup_omni_log` 在 Phase 2.5 omni_log 模块就绪后补。
"""
from __future__ import annotations

import logging
import re
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def _cutoff_ms(retention_days: int) -> int:
    return int(time.time() * 1000) - retention_days * 86400 * 1000


def cleanup_traces_table(conn: sqlite3.Connection, retention_days: int) -> int:
    cur = conn.execute(
        "DELETE FROM traces WHERE timestamp < ?", (_cutoff_ms(retention_days),)
    )
    return cur.rowcount


def cleanup_traces_device_table(conn: sqlite3.Connection, retention_days: int) -> int:
    cur = conn.execute(
        "DELETE FROM traces_device WHERE timestamp < ?",
        (_cutoff_ms(retention_days),),
    )
    return cur.rowcount


def cleanup_events_table(conn: sqlite3.Connection, retention_days: int) -> int:
    cur = conn.execute(
        "DELETE FROM events WHERE timestamp < ?", (_cutoff_ms(retention_days),)
    )
    return cur.rowcount


def cleanup_agent_runs_table(conn: sqlite3.Connection, retention_days: int) -> int:
    cur = conn.execute(
        "DELETE FROM agent_runs WHERE timestamp < ?",
        (_cutoff_ms(retention_days),),
    )
    return cur.rowcount


_DIR_RE = re.compile(r"^\d{8}$")
# omni_log size rotate 出来的 YYYYMMDD.1.jsonl.gz / YYYYMMDD.2.jsonl.gz 也按日期清。
_OMNI_FILE_RE = re.compile(r"^(\d{8})(?:\.\d+)?\.jsonl\.gz$")


def cleanup_trace_jsonl(root: Path, retention_days: int) -> int:
    if not root.exists():
        return 0
    deleted = 0
    cutoff_ord = datetime.now().toordinal() - retention_days
    for entry in root.iterdir():
        if not entry.is_dir() or not _DIR_RE.match(entry.name):
            continue
        try:
            ord_day = datetime.strptime(entry.name, "%Y%m%d").toordinal()
        except ValueError:
            continue
        if ord_day < cutoff_ord:
            shutil.rmtree(entry, ignore_errors=True)
            deleted += 1
    return deleted


def cleanup_omni_log(root: Path, retention_days: int) -> int:
    """删除 ``root/YYYYMMDD.jsonl.gz`` 中比 retention 早的文件。"""
    if not root.exists():
        return 0
    deleted = 0
    cutoff_ord = datetime.now().toordinal() - retention_days
    for entry in root.iterdir():
        if not entry.is_file():
            continue
        m = _OMNI_FILE_RE.match(entry.name)
        if not m:
            continue
        try:
            day_ord = datetime.strptime(m.group(1), "%Y%m%d").toordinal()
        except ValueError:
            continue
        if day_ord < cutoff_ord:
            entry.unlink(missing_ok=True)
            deleted += 1
    return deleted
