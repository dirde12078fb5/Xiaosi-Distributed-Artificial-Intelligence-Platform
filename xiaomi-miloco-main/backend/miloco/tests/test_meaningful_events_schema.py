# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""meaningful_events 表 schema 验证:列定义 + 默认值 + 索引 + 缺表兜底建。"""

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


@pytest.fixture
def partial_db(tmp_path, monkeypatch):
    """部分 DB:手动建 kv 表后启动,触发缺表兜底建 meaningful_events 的路径。

    模拟运行时 db 文件意外损坏 / 缺表场景(墨菲定律 — schema 健壮性兜底)。
    """
    db_file = tmp_path / "partial.db"

    conn = sqlite3.connect(str(db_file))
    conn.execute("""
        CREATE TABLE kv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    monkeypatch.setenv("MILOCO_DATABASE__PATH", str(db_file))

    from miloco.config import reset_settings

    reset_settings()
    import miloco.database.connector as connector_module

    monkeypatch.setattr(connector_module, "db_connector", None)
    connector_module.init_database()
    yield db_file
    reset_settings()


def _table_exists(db_file, name: str) -> bool:
    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def _index_exists(db_file, name: str) -> bool:
    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?", (name,)
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def _column_info(db_file, table: str) -> dict[str, dict]:
    """返回 {column_name: {type, notnull, dflt_value, pk}} 用于 schema 断言."""
    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return {
            row[1]: {"type": row[2], "notnull": row[3], "dflt": row[4], "pk": row[5]}
            for row in cursor.fetchall()
        }
    finally:
        conn.close()


class TestMeaningfulEventsTable:
    def test_table_created_on_fresh_db(self, fresh_db):
        assert _table_exists(fresh_db, "meaningful_events")

    def test_indices_created_on_fresh_db(self, fresh_db):
        assert _index_exists(fresh_db, "idx_meaningful_events_created_at")
        assert _index_exists(fresh_db, "idx_meaningful_events_timestamp")

    def test_table_created_on_partial_db(self, partial_db):
        """缺 meaningful_events 表的 db → 启动时被补建(缺表兜底)。"""
        assert _table_exists(partial_db, "meaningful_events")
        assert _index_exists(partial_db, "idx_meaningful_events_created_at")
        assert _index_exists(partial_db, "idx_meaningful_events_timestamp")

    def test_schema_columns(self, fresh_db):
        """全部字段都存在且类型/NOTNULL/默认值正确."""
        cols = _column_info(fresh_db, "meaningful_events")
        # 必填字段
        assert cols["id"]["type"] == "TEXT" and cols["id"]["pk"] == 1
        assert cols["timestamp"]["type"] == "INTEGER" and cols["timestamp"]["notnull"] == 1
        assert cols["text"]["type"] == "TEXT" and cols["text"]["notnull"] == 1
        assert cols["payload_json"]["type"] == "TEXT" and cols["payload_json"]["notnull"] == 1
        # 行级 schema_version 字段(DAO 兼容字段,与 DB user_version 是两个机制)
        assert cols["schema_version"]["type"] == "INTEGER"
        assert cols["schema_version"]["notnull"] == 1
        assert cols["schema_version"]["dflt"] == "1"
        # has_* 默认 0
        assert cols["has_rule_hit"]["dflt"] == "0"
        assert cols["has_suggestion"]["dflt"] == "0"
        assert cols["has_asr"]["dflt"] == "0"
        # device_ids 默认空 JSON 数组
        assert cols["device_ids"]["type"] == "TEXT"
        assert cols["device_ids"]["notnull"] == 1
        assert cols["device_ids"]["dflt"] == "'[]'"
        # snapshot_count 默认 0
        assert cols["snapshot_count"]["dflt"] == "0"
        # home_id 可空(预留多家庭)
        assert cols["home_id"]["notnull"] == 0

    def test_schema_version_default_on_insert(self, fresh_db):
        """INSERT 不显式指定 schema_version 时,默认值 1 生效。"""
        conn = sqlite3.connect(str(fresh_db))
        try:
            conn.execute(
                "INSERT INTO meaningful_events "
                "(id, timestamp, text, payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                ("test-id-1", 1717286400000, "test text", "{}", 1717286400000),
            )
            conn.commit()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT schema_version, device_ids FROM meaningful_events WHERE id=?",
                ("test-id-1",),
            )
            row = cursor.fetchone()
            assert row[0] == 1
            assert row[1] == "[]"
        finally:
            conn.close()
