# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""task_record repo 层单测：CRUD + partial unique index + FK CASCADE。

侧重 SQL 层正确性（建表 / 索引 / 约束）；业务规则与跨表事务在
test_task_record_service.py 覆盖。
"""

from __future__ import annotations

import sqlite3

import pytest


@pytest.fixture
def real_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_task_record.db"
    monkeypatch.setenv("MILOCO_DATABASE__PATH", str(db_file))

    from miloco.config import reset_settings

    reset_settings()
    import miloco.database.connector as connector_module

    monkeypatch.setattr(connector_module, "db_connector", None)
    connector_module.init_database()
    yield db_file
    reset_settings()


@pytest.fixture
def db_conn(real_db):
    from miloco.database.connector import get_db_connector

    db = get_db_connector()
    with db.get_connection() as conn:
        yield conn


def _insert_task(conn: sqlite3.Connection, task_id: str, description: str = "test task"):
    from miloco.utils.time_utils import now_iso

    conn.execute(
        "INSERT INTO task (task_id, description, status, created_at) "
        "VALUES (?, ?, 'active', ?)",
        (task_id, description, now_iso()),
    )
    conn.commit()


class TestSchemaCreation:
    def test_six_new_tables_exist(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {r["name"] for r in rows}
        for tbl in (
            "task_record_progress",
            "task_record_duration",
            "task_record_duration_session",
            "task_record_event",
            "task_record_event_entry",
            "task_terminate_log",
        ):
            assert tbl in names, f"missing table {tbl}"

    def test_user_version_bumped_to_latest(self, db_conn):
        from miloco.database.connector import _DB_SCHEMA_VERSION

        row = db_conn.execute("PRAGMA user_version").fetchone()
        assert row[0] == _DB_SCHEMA_VERSION

    def test_partial_unique_index_progress(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name='uniq_progress_active'"
        ).fetchall()
        assert len(rows) == 1

    def test_partial_unique_index_duration(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='index' AND name='uniq_duration_active'"
        ).fetchall()
        assert len(rows) == 1


class TestProgressRepo:
    def test_insert_and_get(self, db_conn):
        from miloco.task_record.repo import ProgressRepo

        _insert_task(db_conn, "p1")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        ProgressRepo.insert_active(
            cursor,
            task_id="p1",
            target=8,
            unit="杯",
            window="day",
            recurring_pattern={"day": "*"},
            expires_at=None,
            now="2026-06-10T09:00:00",
        )
        db_conn.commit()

        row = ProgressRepo.get_active(db_conn.cursor(), "p1")
        assert row is not None
        assert row["target"] == 8
        assert row["current"] == 0
        assert row["unit"] == "杯"
        assert row["recurring_pattern"] is not None
        assert row["status"] == "active"

    def test_partial_unique_active_blocks_duplicate(self, db_conn):
        from miloco.task_record.repo import ProgressRepo

        _insert_task(db_conn, "p1")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        ProgressRepo.insert_active(
            cursor,
            task_id="p1",
            target=8,
            unit="杯",
            window="day",
            recurring_pattern=None,
            expires_at=None,
            now="2026-06-10T09:00:00",
        )
        db_conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            cursor2 = db_conn.cursor()
            cursor2.execute("BEGIN")
            ProgressRepo.insert_active(
                cursor2,
                task_id="p1",
                target=10,
                unit="杯",
                window="day",
                recurring_pattern=None,
                expires_at=None,
                now="2026-06-10T10:00:00",
            )

    def test_archive_then_insert_new_active(self, db_conn):
        from miloco.task_record.repo import ProgressRepo

        _insert_task(db_conn, "p1")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        ProgressRepo.insert_active(
            cursor,
            task_id="p1",
            target=8,
            unit="杯",
            window="day",
            recurring_pattern={"day": "*"},
            expires_at=None,
            now="2026-06-10T09:00:00",
        )
        db_conn.commit()

        # rollover：archive 旧活跃 + 新活跃
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        ProgressRepo.archive_active(
            cursor, task_id="p1", archived_at="2026-06-11T00:05:00"
        )
        ProgressRepo.insert_active(
            cursor,
            task_id="p1",
            target=8,
            unit="杯",
            window="day",
            recurring_pattern={"day": "*"},
            expires_at=None,
            now="2026-06-11T00:05:00",
        )
        db_conn.commit()

        all_rows = list(
            db_conn.execute(
                "SELECT id, current, archived_at FROM task_record_progress "
                "WHERE task_id = 'p1' ORDER BY id"
            )
        )
        assert len(all_rows) == 2
        # v10 起 archived_at 是 INTEGER ms
        from miloco.utils.time_utils import iso_to_ms

        assert all_rows[0]["archived_at"] == iso_to_ms("2026-06-11T00:05:00")
        assert all_rows[1]["archived_at"] is None
        assert all_rows[1]["current"] == 0


class TestDurationRepo:
    def test_insert_main_and_session(self, db_conn):
        from miloco.task_record.repo import DurationRepo

        _insert_task(db_conn, "d1")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        DurationRepo.insert_active(
            cursor,
            task_id="d1",
            target_minutes=60,
            active_session_start_at=None,
            recurring_pattern=None,
            expires_at=None,
            now="2026-06-10T09:00:00",
        )
        DurationRepo.insert_session(
            cursor,
            task_id="d1",
            start_at="2026-06-10T09:00:00",
            end_at="2026-06-10T09:25:00",
            duration_seconds=25 * 60,
        )
        db_conn.commit()

        sessions = DurationRepo.list_active_sessions(db_conn.cursor(), task_id="d1")
        assert len(sessions) == 1
        assert sessions[0]["duration_seconds"] == 25 * 60

    def test_sum_seconds_active_period(self, db_conn):
        from miloco.task_record.repo import DurationRepo

        _insert_task(db_conn, "d1")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        DurationRepo.insert_active(
            cursor,
            task_id="d1",
            target_minutes=60,
            active_session_start_at=None,
            recurring_pattern=None,
            expires_at=None,
            now="2026-06-10T09:00:00",
        )
        for start, end, dur_min in [
            ("2026-06-10T09:00:00", "2026-06-10T09:25:00", 25),
            ("2026-06-10T10:00:00", "2026-06-10T10:15:00", 15),
        ]:
            DurationRepo.insert_session(
                cursor,
                task_id="d1",
                start_at=start,
                end_at=end,
                duration_seconds=dur_min * 60,
            )
        db_conn.commit()

        total = DurationRepo.sum_seconds_active_period(
            db_conn.cursor(), task_id="d1"
        )
        assert total == 40 * 60


class TestEventRepo:
    def test_insert_event_and_entries(self, db_conn):
        from miloco.task_record.repo import EventRepo

        _insert_task(db_conn, "e1")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        EventRepo.insert_active(
            cursor,
            task_id="e1",
            recurring_pattern=None,
            expires_at=None,
            now="2026-06-10T09:00:00",
        )
        EventRepo.insert_entry(
            cursor,
            task_id="e1",
            description="第一次",
            at="2026-06-10T09:15:00",
        )
        EventRepo.insert_entry(
            cursor,
            task_id="e1",
            description="第二次",
            at="2026-06-10T11:30:00",
        )
        db_conn.commit()

        cursor = db_conn.cursor()
        assert EventRepo.count_entries(cursor, task_id="e1") == 2
        assert (
            EventRepo.count_entries_with_prefix(
                cursor, task_id="e1", at_prefix="2026-06-10"
            )
            == 2
        )
        # v10 起 EventRepo.last_entry_at 出口转部署时区带偏移 ISO (DB 内 ms,跨时区无歧义)
        from miloco.utils.time_utils import iso_to_ms, ms_to_iso_local

        expected = ms_to_iso_local(iso_to_ms("2026-06-10T11:30:00"))
        assert EventRepo.last_entry_at(cursor, task_id="e1") == expected

    def test_unique_task_id_blocks_duplicate(self, db_conn):
        from miloco.task_record.repo import EventRepo

        _insert_task(db_conn, "e1")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        EventRepo.insert_active(
            cursor,
            task_id="e1",
            recurring_pattern=None,
            expires_at=None,
            now="2026-06-10T09:00:00",
        )
        db_conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            cursor = db_conn.cursor()
            cursor.execute("BEGIN")
            EventRepo.insert_active(
                cursor,
                task_id="e1",
                recurring_pattern=None,
                expires_at=None,
                now="2026-06-10T10:00:00",
            )


class TestFKCascade:
    def test_delete_task_cascades_record_tables(self, db_conn):
        from miloco.task_record.repo import (
            ProgressRepo,
        )

        _insert_task(db_conn, "t_cascade")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        ProgressRepo.insert_active(
            cursor,
            task_id="t_cascade",
            target=5,
            unit="次",
            window="day",
            recurring_pattern=None,
            expires_at=None,
            now="2026-06-10T09:00:00",
        )
        db_conn.commit()

        # 单 task 一次只能挂一种 record 类型，独立测每个 kind 的 cascade
        # 这里 progress 已挂上；删 task 后 progress 行应消失
        db_conn.execute("DELETE FROM task WHERE task_id = ?", ("t_cascade",))
        db_conn.commit()

        rows = db_conn.execute(
            "SELECT * FROM task_record_progress WHERE task_id = ?",
            ("t_cascade",),
        ).fetchall()
        assert rows == []

    def test_delete_task_cascades_duration_with_sessions(self, db_conn):
        from miloco.task_record.repo import DurationRepo

        _insert_task(db_conn, "t_dur")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        DurationRepo.insert_active(
            cursor,
            task_id="t_dur",
            target_minutes=60,
            active_session_start_at=None,
            recurring_pattern=None,
            expires_at=None,
            now="2026-06-10T09:00:00",
        )
        DurationRepo.insert_session(
            cursor,
            task_id="t_dur",
            start_at="2026-06-10T09:00:00",
            end_at="2026-06-10T09:30:00",
            duration_seconds=30 * 60,
        )
        db_conn.commit()

        db_conn.execute("DELETE FROM task WHERE task_id = ?", ("t_dur",))
        db_conn.commit()

        main_rows = db_conn.execute(
            "SELECT * FROM task_record_duration WHERE task_id = ?",
            ("t_dur",),
        ).fetchall()
        session_rows = db_conn.execute(
            "SELECT * FROM task_record_duration_session WHERE task_id = ?",
            ("t_dur",),
        ).fetchall()
        assert main_rows == []
        assert session_rows == []


class TestTerminateLogRepo:
    def test_insert_count_prune(self, db_conn):
        from miloco.task_record.repo import TerminateLogRepo
        from miloco.task_record.schema import RecordKind

        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        for at in (
            "2026-04-01T09:00:00",  # 应被 30 天前 prune（相对 2026-06-10）
            "2026-06-09T09:00:00",  # 留下
        ):
            TerminateLogRepo.insert(
                cursor,
                task_id="t1",
                kind=RecordKind.PROGRESS,
                reason="completed",
                description="x",
                final_snapshot={"target": 8, "current": 8},
                terminated_at=at,
            )
        db_conn.commit()

        cursor = db_conn.cursor()
        assert TerminateLogRepo.count(cursor) == 2

        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        deleted = TerminateLogRepo.prune_older_than(
            cursor, cutoff="2026-05-11T00:00:00"
        )
        db_conn.commit()
        assert deleted == 1
        cursor = db_conn.cursor()
        assert TerminateLogRepo.count(cursor) == 1


class TestDurationPrecisionRegression:
    """memory project_task_record_duration_floor_precision 复现。

    9 段 session 实际秒数和 = 651s = 10.85min；
    旧实现：每段 floor 入 duration_minutes，SUM = 5min（损失 54%）
    新实现：存 duration_seconds，SUM 出 651，输出层 // 60 = 10min
    """

    def test_sum_seconds_active_period_preserves_651_total(self, db_conn):
        """9 段 0-200s 不等的 session，SUM 应等于 651s 而非 5min*60。"""
        from datetime import datetime, timedelta, timezone

        from miloco.task_record.repo import DurationRepo

        _insert_task(db_conn, "phone_usage_test")
        cursor = db_conn.cursor()
        cursor.execute("BEGIN")
        DurationRepo.insert_active(
            cursor,
            task_id="phone_usage_test",
            target_minutes=None,
            active_session_start_at=None,
            recurring_pattern=None,
            expires_at=None,
            now="2026-06-13T10:00:00+08:00",
        )
        segments = [60, 73, 65, 80, 70, 78, 67, 75, 83]  # sum=651
        base = datetime(
            2026, 6, 13, 10, 0, 0, tzinfo=timezone(timedelta(hours=8))
        )
        t = base
        for sec in segments:
            end_t = t + timedelta(seconds=sec)
            DurationRepo.insert_session(
                cursor,
                task_id="phone_usage_test",
                start_at=t.isoformat(timespec="seconds"),
                end_at=end_t.isoformat(timespec="seconds"),
                duration_seconds=sec,
            )
            t = end_t
        db_conn.commit()

        total = DurationRepo.sum_seconds_active_period(
            db_conn.cursor(), task_id="phone_usage_test"
        )
        assert total == 651, f"expected 651s, got {total}"
