# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""task_link 表的 schema 约束验证:FK ON DELETE CASCADE + 全局 UNIQUE(link_kind, link_ref)。"""

import sqlite3

import pytest


@pytest.fixture
def fresh_db(tmp_path, monkeypatch):
    """新建 DB,走 _create_tables 路径建齐全表。"""
    db_file = tmp_path / "fresh.db"
    monkeypatch.setenv("MILOCO_DATABASE__PATH", str(db_file))

    from miloco.config import reset_settings

    reset_settings()
    import miloco.database.connector as connector_module

    monkeypatch.setattr(connector_module, "db_connector", None)
    connector_module.init_database()
    yield db_file
    reset_settings()


def test_task_link_fk_rejects_orphan(fresh_db):
    """task_link.task_id FK 必须真正生效,引用不存在的 task 应被拒绝。"""
    conn = sqlite3.connect(str(fresh_db))
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO task_link (task_id, link_kind, link_ref) "
                "VALUES ('ghost', 'rule', 'r1')"
            )
    finally:
        conn.close()


def test_task_link_unique_ref_across_tasks(fresh_db):
    """全局 UNIQUE(link_kind, link_ref) 必须真正生效:同一 ref 不能挂在两个 task 上。"""
    from miloco.utils.time_utils import now_ms

    conn = sqlite3.connect(str(fresh_db))
    conn.execute("PRAGMA foreign_keys = ON")
    ts = now_ms()
    try:
        conn.execute(
            "INSERT INTO task (task_id, description, created_at) VALUES ('t1', 'd1', ?)",
            (ts,),
        )
        conn.execute(
            "INSERT INTO task (task_id, description, created_at) VALUES ('t2', 'd2', ?)",
            (ts,),
        )
        conn.execute(
            "INSERT INTO task_link (task_id, link_kind, link_ref) "
            "VALUES ('t1', 'rule', 'rule_X')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO task_link (task_id, link_kind, link_ref) "
                "VALUES ('t2', 'rule', 'rule_X')"
            )
        conn.commit()
    finally:
        conn.close()
