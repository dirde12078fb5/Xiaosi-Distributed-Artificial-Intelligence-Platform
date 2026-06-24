# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""rollover_daily_job + 边界判断单测（spec §6.3, §11.1）。

覆盖：
- 单 task 跨日（progress）current 重置为 0
- 单 task 跨日（duration）active session 切两段（旧 session end=0:05 +
  新 period active_session_start_at=0:05）
- self-heal：上次 archive 在当前 period 起点之前 → 触发 rollover
- 同一 period 内重启不重复 rollover（idempotent）
- 多 task 并发：单 task 失败不影响其他
- event kind 不进 rollover job
- _should_rollover：day / week / month / longterm 边界判断
- seconds_until_next_run 算下次 0:05
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest


@pytest.fixture
def real_db(tmp_path, monkeypatch):
    db_file = tmp_path / "rollover_test.db"
    monkeypatch.setenv("MILOCO_DATABASE__PATH", str(db_file))

    from miloco.config import reset_settings

    reset_settings()
    import miloco.database.connector as connector_module

    monkeypatch.setattr(connector_module, "db_connector", None)
    connector_module.init_database()
    yield db_file
    reset_settings()


@pytest.fixture
def service(real_db):
    from miloco.task_record.service import TaskRecordService

    return TaskRecordService()


@pytest.fixture
def db(real_db):
    from miloco.database.connector import get_db_connector

    return get_db_connector()


def _insert_task(db, task_id):
    from miloco.utils.time_utils import now_ms

    with db.get_connection() as conn:
        conn.execute(
            "INSERT INTO task (task_id, description, status, created_at) "
            "VALUES (?, ?, 'active', ?)",
            (task_id, "x", now_ms()),
        )
        conn.commit()


# ── _should_rollover 边界判断 ────────────────────────────────────────────────


class TestShouldRollover:
    def test_no_recurring_pattern_returns_false(self):
        from miloco.task_record.rollover import _should_rollover
        from miloco.task_record.schema import RecordKind

        row = {
            "recurring_pattern": None,
            "window": "day",
            "created_at": "2026-06-01T00:00:00",
        }
        assert (
            _should_rollover(
                row, RecordKind.PROGRESS, datetime(2026, 6, 10, 0, 5, 0), None
            )
            is False
        )

    def test_day_window_after_midnight_triggers(self):
        from miloco.task_record.rollover import _should_rollover
        from miloco.task_record.schema import RecordKind

        row = {
            "recurring_pattern": '{"window":"day"}',
            "window": "day",
            "created_at": "2026-06-09T00:00:00",
        }
        # 上次 archive 是昨天 0:05；今天 0:05 应该 rollover
        assert (
            _should_rollover(
                row,
                RecordKind.PROGRESS,
                datetime(2026, 6, 10, 0, 5, 0),
                "2026-06-09T00:05:00",
            )
            is True
        )

    def test_same_day_does_not_re_rollover(self):
        from miloco.task_record.rollover import _should_rollover
        from miloco.task_record.schema import RecordKind

        row = {
            "recurring_pattern": '{"window":"day"}',
            "window": "day",
            "created_at": "2026-06-10T00:00:00",
        }
        # 今天 0:05 已 archive 过；中午 12:00 重启 self-heal 不应再次 rollover
        assert (
            _should_rollover(
                row,
                RecordKind.PROGRESS,
                datetime(2026, 6, 10, 12, 0, 0),
                "2026-06-10T00:05:00",
            )
            is False
        )

    def test_week_window_monday_triggers(self):
        from miloco.task_record.rollover import _should_rollover
        from miloco.task_record.schema import RecordKind

        row = {
            "recurring_pattern": '{"window":"week"}',
            "window": "week",
            "created_at": "2026-06-01T00:00:00",
        }
        # 2026-06-08 是周一；上次 archive 在 2026-06-01 周一之前 → 触发
        assert (
            _should_rollover(
                row,
                RecordKind.PROGRESS,
                datetime(2026, 6, 8, 0, 5, 0),
                "2026-06-01T00:05:00",
            )
            is True
        )
        # 同周（周三）不再触发
        assert (
            _should_rollover(
                row,
                RecordKind.PROGRESS,
                datetime(2026, 6, 10, 0, 5, 0),
                "2026-06-08T00:05:00",
            )
            is False
        )

    def test_month_window_month_start(self):
        from miloco.task_record.rollover import _should_rollover
        from miloco.task_record.schema import RecordKind

        row = {
            "recurring_pattern": '{"window":"month"}',
            "window": "month",
            "created_at": "2026-05-15T00:00:00",
        }
        # 2026-06-01 触发
        assert (
            _should_rollover(
                row,
                RecordKind.PROGRESS,
                datetime(2026, 6, 1, 0, 5, 0),
                "2026-05-01T00:05:00",
            )
            is True
        )
        # 同月不再触发
        assert (
            _should_rollover(
                row,
                RecordKind.PROGRESS,
                datetime(2026, 6, 15, 0, 5, 0),
                "2026-06-01T00:05:00",
            )
            is False
        )

    def test_longterm_never_triggers(self):
        from miloco.task_record.rollover import _should_rollover
        from miloco.task_record.schema import RecordKind

        row = {
            "recurring_pattern": '{"window":"longterm"}',
            "window": "longterm",
            "created_at": "2024-01-01T00:00:00",
        }
        assert (
            _should_rollover(
                row,
                RecordKind.PROGRESS,
                datetime(2026, 6, 10, 0, 5, 0),
                None,
            )
            is False
        )


# ── seconds_until_next_run ───────────────────────────────────────────────────


class TestSecondsUntilNextRun:
    def test_before_target_today(self):
        from miloco.task_record.rollover import seconds_until_next_run

        now = datetime(2026, 6, 10, 0, 4, 0)
        # 到 0:05 还有 60 秒
        assert seconds_until_next_run(now, 0, 5) == 60.0

    def test_after_target_jumps_to_tomorrow(self):
        from miloco.task_record.rollover import seconds_until_next_run

        now = datetime(2026, 6, 10, 12, 0, 0)
        # 跨日，到明天 0:05
        sec = seconds_until_next_run(now, 0, 5)
        assert 0 < sec <= 86400
        # 12:00 → 次日 0:05 = 12小时5分钟 = 43500
        assert sec == 12 * 3600 + 5 * 60


# ── rollover_daily_job 集成 ──────────────────────────────────────────────────


class TestRolloverDailyJob:
    def test_progress_day_rollover_resets_current(self, service, db):
        from miloco.task_record.rollover import rollover_daily_job
        from miloco.task_record.schema import RecordKind

        _insert_task(db, "p1")
        service.init_record(
            "p1",
            RecordKind.PROGRESS,
            {
                "target": 8,
                "unit": "杯",
                "window": "day",
                "recurring_pattern": {"window": "day"},
            },
        )
        service.progress_increment("p1", delta=3)

        # 提前一天 mock now：上次 archived_at=None，created_at=now 之前
        # 直接把 created_at 改到昨天
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE task_record_progress SET created_at = ?, updated_at = ?",
                ("2026-06-09T08:00:00", "2026-06-09T08:00:00"),
            )
            conn.commit()

        result = rollover_daily_job(service, now=datetime(2026, 6, 10, 0, 5, 0))
        assert result["progress"] == 1
        assert result["failed"] == 0

        with db.get_connection() as conn:
            rows = list(
                conn.execute(
                    "SELECT current, archived_at FROM task_record_progress "
                    "WHERE task_id = 'p1' ORDER BY id"
                )
            )
        assert len(rows) == 2
        assert rows[0]["archived_at"] is not None
        assert rows[1]["archived_at"] is None
        assert rows[1]["current"] == 0

    def test_duration_rollover_splits_active_session(self, service, db):
        from miloco.task_record.rollover import rollover_daily_job
        from miloco.task_record.schema import RecordKind

        _insert_task(db, "d1")
        service.init_record(
            "d1",
            RecordKind.DURATION,
            {
                "target_minutes": 60,
                "recurring_pattern": {"window": "day"},
            },
        )
        service.session_start("d1", at="2026-06-09T23:30:00")

        with db.get_connection() as conn:
            conn.execute(
                "UPDATE task_record_duration SET created_at = ?, updated_at = ?",
                ("2026-06-09T08:00:00", "2026-06-09T08:00:00"),
            )
            conn.commit()

        rollover_daily_job(service, now=datetime(2026, 6, 10, 0, 5, 0))

        with db.get_connection() as conn:
            sessions = list(
                conn.execute(
                    "SELECT * FROM task_record_duration_session "
                    "WHERE task_id = 'd1' ORDER BY id"
                )
            )
            new_main = conn.execute(
                "SELECT active_session_start_at FROM task_record_duration "
                "WHERE task_id = 'd1' AND archived_at IS NULL"
            ).fetchone()
        # 旧 session（被切的前半段）+ 1 行
        # v10 起 start_at/end_at/active_session_start_at 是 INTEGER ms,用 helper 转字符串再比对
        from miloco.utils.time_utils import iso_to_ms, ms_to_aware_dt

        assert len(sessions) == 1
        assert sessions[0]["start_at"] == iso_to_ms("2026-06-09T23:30:00")
        end_local = ms_to_aware_dt(sessions[0]["end_at"]).strftime(
            "%Y-%m-%dT%H:%M"
        )
        assert end_local == "2026-06-10T00:05"
        assert sessions[0]["duration_seconds"] == 35 * 60
        active_local = ms_to_aware_dt(new_main["active_session_start_at"]).strftime(
            "%Y-%m-%dT%H:%M"
        )
        assert active_local == "2026-06-10T00:05"

    def test_duration_rollover_callback_receives_pre_state(self, service, db):
        """duration rollover 回调签名 (task_id, pre_state)：pre_state 是 archive
        前 snapshot 的 (target_minutes, accumulated_minutes_today)，让 rule
        engine 跨日兜底 fire on_target 时能判断旧一天是否达标。"""
        from miloco.task_record.rollover import rollover_daily_job
        from miloco.task_record.schema import RecordKind

        _insert_task(db, "d2")
        service.init_record(
            "d2",
            RecordKind.DURATION,
            {
                "target_minutes": 60,
                "recurring_pattern": {"window": "day"},
            },
        )
        # 23:00 起 session，跨日时累计已超 60min（23:00 → 0:05 = 65min）
        service.session_start("d2", at="2026-06-09T23:00:00")
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE task_record_duration SET created_at = ?, updated_at = ?",
                ("2026-06-09T08:00:00", "2026-06-09T08:00:00"),
            )
            conn.commit()
        captured: list[tuple[str, tuple[int | None, int] | None]] = []

        def hook(task_id, pre_state):
            captured.append((task_id, pre_state))

        rollover_daily_job(
            service, now=datetime(2026, 6, 10, 0, 5, 0),
            on_duration_rollover=hook,
        )
        assert len(captured) == 1
        assert captured[0][0] == "d2"
        target, accumulated = captured[0][1]
        assert target == 60
        # 23:00 → 0:05 跨段，旧一天 23:00-24:00 = 60min 已达标
        assert accumulated >= 60

    def test_skipped_when_no_recurring(self, service, db):
        from miloco.task_record.rollover import rollover_daily_job
        from miloco.task_record.schema import RecordKind

        _insert_task(db, "p1")
        service.init_record(
            "p1",
            RecordKind.PROGRESS,
            {"target": 8, "unit": "杯", "window": "longterm"},
        )
        result = rollover_daily_job(service, now=datetime(2026, 6, 10, 0, 5, 0))
        assert result["progress"] == 0
        # longterm 任务 recurring_pattern 为 NULL，list_recurring_active 不返回
        # → skipped 计数也不会增加，但 progress=0 / failed=0
        with db.get_connection() as conn:
            n = conn.execute(
                "SELECT COUNT(*) AS n FROM task_record_progress WHERE task_id='p1'"
            ).fetchone()["n"]
        assert n == 1

    def test_event_kind_ignored(self, service, db):
        from miloco.task_record.rollover import rollover_daily_job
        from miloco.task_record.schema import RecordKind

        _insert_task(db, "e1")
        service.init_record(
            "e1",
            RecordKind.EVENT,
            {"recurring_pattern": {"window": "day"}},
        )
        service.event_append("e1", "x", at="2026-06-09T09:00:00")

        result = rollover_daily_job(service, now=datetime(2026, 6, 10, 0, 5, 0))
        assert result["progress"] == 0
        assert result["duration"] == 0
        # event 表无 archive 字段，未受影响
        with db.get_connection() as conn:
            n = conn.execute(
                "SELECT COUNT(*) FROM task_record_event_entry WHERE task_id='e1'"
            ).fetchone()[0]
        assert n == 1

    def test_rollover_archived_at_belongs_to_prev_period(self, service, db):
        """rollover_one 在次日 00:05 跑时,archived_at 应写昨日 period_end
        (23:59:59),保证 compute --date <昨日> 走 LIKE '<昨日>%' 能命中归档行。"""
        from miloco.task_record.schema import RecordKind

        _insert_task(db, "p1")
        service.init_record(
            "p1",
            RecordKind.PROGRESS,
            {
                "target": 8,
                "unit": "杯",
                "window": "day",
                "recurring_pattern": {"window": "day"},
            },
        )
        service.progress_increment("p1", delta=5)
        # 把活跃行 created_at 改到昨天 (rollover 才会触发)
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE task_record_progress SET created_at = ?, updated_at = ? "
                "WHERE task_id = 'p1'",
                ("2026-06-09T08:00:00+08:00", "2026-06-09T08:00:00+08:00"),
            )
            conn.commit()

        # 次日 00:05 触发 rollover
        service.rollover_one(
            "p1", RecordKind.PROGRESS, datetime(2026, 6, 10, 0, 5, 0)
        )

        # 归档行的 archived_at 应为 2026-06-09T23:59:59+08:00 (昨日 period_end)
        with db.get_connection() as conn:
            row = conn.execute(
                "SELECT archived_at FROM task_record_progress "
                "WHERE task_id='p1' AND archived_at IS NOT NULL"
            ).fetchone()
        assert row is not None
        # v10 起 archived_at 是 INTEGER ms,转回部署时区日期再断言
        from miloco.utils.time_utils import ms_to_aware_dt

        archived_day = ms_to_aware_dt(row[0]).strftime("%Y-%m-%d")
        assert archived_day == "2026-06-09"  # 不是 06-10

        # compute --date 2026-06-09 必须命中
        r = service.compute_derived("p1", window="all", date="2026-06-09")
        assert r["kind"] == "progress"
        assert r["derived"]["remaining"] == 3  # target=8, current=5, remaining=3

    def test_self_heal_idempotent_same_period(self, service, db):
        """同一 day period 内重复跑 daily_job，不应叠加 rollover。"""
        from miloco.task_record.rollover import rollover_daily_job
        from miloco.task_record.schema import RecordKind

        _insert_task(db, "p1")
        service.init_record(
            "p1",
            RecordKind.PROGRESS,
            {
                "target": 8,
                "unit": "杯",
                "window": "day",
                "recurring_pattern": {"window": "day"},
            },
        )
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE task_record_progress SET created_at = ?, updated_at = ?",
                ("2026-06-09T08:00:00", "2026-06-09T08:00:00"),
            )
            conn.commit()

        rollover_daily_job(service, now=datetime(2026, 6, 10, 0, 5, 0))
        # 立即再跑（self-heal 重启场景）
        rollover_daily_job(service, now=datetime(2026, 6, 10, 12, 0, 0))

        with db.get_connection() as conn:
            n = conn.execute(
                "SELECT COUNT(*) FROM task_record_progress WHERE task_id='p1'"
            ).fetchone()[0]
        assert n == 2  # 1 旧归档 + 1 新活跃；没有叠加

    def test_default_now_uses_deploy_timezone(self, service, db, monkeypatch):
        """R2-2 回归:rollover_daily_job 不传 now 时 fallback 必带 deploy_timezone() 的
        tzinfo,不会取 naive datetime.now(UTC 容器场景下会偏移导致 period_start 错位)。"""
        from zoneinfo import ZoneInfo

        from miloco.task_record import rollover as rollover_mod

        # 锁定 deploy_timezone() 返回固定 Asia/Shanghai,断言独立于 CI 容器时区
        fixed_tz = ZoneInfo("Asia/Shanghai")
        monkeypatch.setattr(rollover_mod, "deploy_timezone", lambda: fixed_tz)

        captured: list = []
        original_now = rollover_mod.datetime.now

        class _MockDatetime:
            @staticmethod
            def now(tz=None):
                result = original_now(tz)
                captured.append(("now", tz, result))
                return result

            @staticmethod
            def fromisoformat(s):
                return original_now.__self__.fromisoformat(s)

            min = original_now.__self__.min

        monkeypatch.setattr(rollover_mod, "datetime", _MockDatetime)

        rollover_mod.rollover_daily_job(service)

        # fallback 必带 deploy_timezone() 返回的 tzinfo
        assert any(
            tz is fixed_tz for _, tz, _ in captured
        ), "rollover_daily_job 默认 now 必须用 deploy_timezone() aware,不能是 naive"

    def test_one_task_failure_does_not_abort_others(self, service, db):
        from miloco.task_record.rollover import rollover_daily_job
        from miloco.task_record.schema import RecordKind

        _insert_task(db, "p1")
        _insert_task(db, "p2")
        for tid in ("p1", "p2"):
            service.init_record(
                tid,
                RecordKind.PROGRESS,
                {
                    "target": 8,
                    "unit": "杯",
                    "window": "day",
                    "recurring_pattern": {"window": "day"},
                },
            )
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE task_record_progress SET created_at = ?, updated_at = ?",
                ("2026-06-09T08:00:00", "2026-06-09T08:00:00"),
            )
            conn.commit()

        # mock service.rollover_one：p1 抛错，p2 正常
        original = service.rollover_one

        def faulty(task_id, kind, now):
            if task_id == "p1":
                raise RuntimeError("simulated failure")
            return original(task_id, kind, now)

        with patch.object(service, "rollover_one", side_effect=faulty):
            result = rollover_daily_job(
                service, now=datetime(2026, 6, 10, 0, 5, 0)
            )
        assert result["progress"] == 1  # p2 成功
        assert result["failed"] == 1  # p1 失败
