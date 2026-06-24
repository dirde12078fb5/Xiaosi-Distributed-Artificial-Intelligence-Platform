# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""task / task_link 双表数据访问层。

事务原子性陷阱:SQLiteConnector 默认 ``isolation_level=None``(autocommit),
每条 execute 自动提交。必须显式 ``cursor.execute("BEGIN")`` + 末尾
``conn.commit()`` 才能让 create_task 的多条 INSERT 构成原子事务。

跨 task ref 唯一性靠 DB 层 ``UNIQUE INDEX idx_task_link_ref_unique``
``(link_kind, link_ref)`` 强制,service 层不做 SELECT 预检——撞库走
IntegrityError 异常路径。
"""

import logging
import sqlite3
from typing import Any

from miloco.database.connector import get_db_connector
from miloco.utils.time_utils import ms_to_iso_local, now_ms

logger = logging.getLogger(__name__)


class TaskLinkConflict(Exception):
    """task PK 撞库 / 跨 task ref 撞库 / FK 引用不存在的 task。"""


class TaskRepo:
    def __init__(self):
        self.db = get_db_connector()

    def create_task(self, task_id: str, description: str) -> None:
        """方案 P 阶段 D'：仅 INSERT task 行（占位），不写 task_link。

        rule / cron 关联挂载由后续 endpoint 完成：rule create 内部一笔事务
        INSERT rule + INSERT task_link；cron 走 ``POST /tasks/{id}/link``。
        record 不进 task_link，由 ``POST /tasks/{id}/record`` 经 FK 直连 task。
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO task (task_id, description, status, created_at) "
                    "VALUES (?, ?, 'active', ?)",
                    (task_id, description, now_ms()),
                )
                conn.commit()
                logger.info("Task created (placeholder): task_id=%s", task_id)
            except sqlite3.IntegrityError as e:
                conn.rollback()
                msg = str(e)
                if "task.task_id" in msg or "UNIQUE" in msg:
                    raise TaskLinkConflict(f"task_id {task_id!r} 已存在") from e
                raise

    def add_link(self, task_id: str, kind: str, ref: str) -> None:
        """追加单条 task_link 行。``kind`` 仅接受 ``rule`` / ``cron``。"""
        if kind not in ("rule", "cron"):
            raise TaskLinkConflict(
                f"link_kind {kind!r} 不合法，方案 P 仅支持 rule / cron"
            )
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO task_link "
                    "(task_id, link_kind, link_ref) VALUES (?, ?, ?)",
                    (task_id, kind, ref),
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                msg = str(e)
                if "FOREIGN KEY" in msg:
                    raise TaskLinkConflict(
                        f"task {task_id!r} 不存在,先调 task create"
                    ) from e
                raise TaskLinkConflict(
                    f"{kind} ref {ref!r} 撞库（已挂在其它 task 或重复添加）"
                ) from e

    def task_exists(self, task_id: str) -> bool:
        """task 表是否含此 task_id（rule create 前置校验用）。"""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM task WHERE task_id = ?", (task_id,)
            ).fetchone()
            return row is not None

    def get_full_view(self, task_id: str) -> dict[str, Any] | None:
        """单 task 视图:task 元信息 + 所有 task_link 行。"""
        with self.db.get_connection() as conn:
            task_row = conn.execute(
                "SELECT task_id, description, status, paused_at, created_at "
                "FROM task WHERE task_id=?",
                (task_id,),
            ).fetchone()
            if task_row is None:
                return None
            links = conn.execute(
                "SELECT link_kind AS kind, link_ref AS ref FROM task_link "
                "WHERE task_id=?",
                (task_id,),
            ).fetchall()
            return {
                "task_id": task_row["task_id"],
                "description": task_row["description"],
                "status": task_row["status"],
                "paused_at": ms_to_iso_local(task_row["paused_at"]),
                "created_at": ms_to_iso_local(task_row["created_at"]),
                "links": [{"kind": link["kind"], "ref": link["ref"]} for link in links],
            }

    def list_all(self) -> list[dict[str, Any]]:
        """所有 task 的聚合视图(service 层接管 rule_briefs JOIN)。

        实现:1 次 SELECT task + 1 次 SELECT task_link 全表,Python 内 join。
        简单可读,task 量级(< 1000)下性能足够。
        """
        with self.db.get_connection() as conn:
            tasks = conn.execute(
                "SELECT task_id, description, status, paused_at, created_at "
                "FROM task ORDER BY created_at DESC"
            ).fetchall()
            all_links = conn.execute(
                "SELECT task_id, link_kind AS kind, link_ref AS ref FROM task_link"
            ).fetchall()
            links_by_task: dict[str, list[dict]] = {}
            for link in all_links:
                links_by_task.setdefault(link["task_id"], []).append(
                    {"kind": link["kind"], "ref": link["ref"]}
                )
            return [
                {
                    "task_id": t["task_id"],
                    "description": t["description"],
                    "status": t["status"],
                    "paused_at": ms_to_iso_local(t["paused_at"]),
                    "created_at": ms_to_iso_local(t["created_at"]),
                    "links": links_by_task.get(t["task_id"], []),
                }
                for t in tasks
            ]

    def set_status(self, task_id: str, status: str) -> str:
        """改 task.status。返回 'ok' | 'noop' | 'not_found'。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            current = cursor.execute(
                "SELECT status FROM task WHERE task_id=?", (task_id,)
            ).fetchone()
            if current is None:
                return "not_found"
            if current["status"] == status:
                return "noop"
            paused_at = now_ms() if status == "paused" else None
            cursor.execute(
                "UPDATE task SET status=?, paused_at=? WHERE task_id=?",
                (status, paused_at, task_id),
            )
            conn.commit()
            return "ok"

    def update_description(self, task_id: str, description: str) -> bool:
        """改 task.description。返回 affected>0。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE task SET description=? WHERE task_id=?",
                (description, task_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_task(self, task_id: str) -> int:
        """删 task 行(FK CASCADE 自动清 task_link)。返回 task 表 affected rows。"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM task WHERE task_id=?", (task_id,))
            conn.commit()
            return cursor.rowcount

    @staticmethod
    def delete_task_in_tx(cursor, task_id: str) -> int:
        """外层事务版本：用 caller 提供的 cursor 删 task，不 own connection。"""
        cursor.execute("DELETE FROM task WHERE task_id=?", (task_id,))
        return cursor.rowcount

    def get_rule_refs(self, task_id: str) -> list[str]:
        """拿该 task 的 rule_id 列表(service 层 disable/delete 联动用)。"""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT link_ref FROM task_link "
                "WHERE task_id=? AND link_kind='rule'",
                (task_id,),
            ).fetchall()
            return [r["link_ref"] for r in rows]

    def delete_link_by_ref(self, kind: str, ref: str) -> int:
        """删 task_link 行(kind, ref)。返回 affected rows。

        UNIQUE(link_kind, link_ref) 保证最多影响 1 行。底层 ref 被先删
        (rule delete / cron 删除) 时调用,清理 task_link 中的 dangling 行。
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM task_link WHERE link_kind=? AND link_ref=?",
                (kind, ref),
            )
            conn.commit()
            return cursor.rowcount
