# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""守门测试:rule / task / kv / person 四张表 v10 schema (INTEGER ms) 后:

1. DB 内时间字段必须是 INTEGER 类型(用 PRAGMA table_info 断言)
2. DB 内存的是 Unix ms (UTC 绝对时刻),写入时间在合理范围内
3. repo 出口转部署时区带偏移 ISO 字符串(``deploy_timezone()`` 在测试下锁 Asia/Shanghai)
"""

import re
import time

import pytest

ISO_LOCAL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")


@pytest.fixture(autouse=True)
def _lock_deploy_tz(monkeypatch):
    """守门测试锁 Asia/Shanghai,断言完整 ISO 字符串后缀 +08:00。"""
    monkeypatch.setenv("MILOCO_TIMEZONE", "Asia/Shanghai")
    from miloco.config import reset_settings

    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def real_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("MILOCO_DATABASE__PATH", str(db_file))

    from miloco.config import reset_settings

    reset_settings()
    import miloco.database.connector as connector_module

    monkeypatch.setattr(connector_module, "db_connector", None)
    connector_module.init_database()

    yield db_file
    reset_settings()


def _assert_ms_in_range(label: str, value, lo: int, hi: int) -> None:
    assert value is not None, f"{label} is None"
    assert isinstance(value, int), f"{label}={value!r} not INTEGER"
    assert lo <= value <= hi, f"{label}={value} 不在 [{lo}, {hi}] 范围内"


def _assert_iso_local(label: str, value) -> None:
    assert value is not None, f"{label} is None"
    assert isinstance(value, str), f"{label}={value!r} not str"
    assert ISO_LOCAL_RE.match(value), f"{label}={value!r} 不符合本地 ISO ``±HH:MM`` 格式"


def _assert_column_integer(db_file, table: str, column: str) -> None:
    import sqlite3

    conn = sqlite3.connect(str(db_file))
    try:
        col_info = {r[1]: r[2].upper() for r in conn.execute(f"PRAGMA table_info({table})")}
        assert col_info.get(column) == "INTEGER", (
            f"{table}.{column} type={col_info.get(column)!r} 不是 INTEGER"
        )
    finally:
        conn.close()


# ── DB 层:时间字段必须是 INTEGER ────────────────────────────────────────────


@pytest.mark.parametrize(
    "table,column",
    [
        ("kv", "created_at"),
        ("kv", "updated_at"),
        ("person", "created_at"),
        ("person", "updated_at"),
        ("task", "created_at"),
        ("task", "paused_at"),
        ("rule", "created_at"),
        ("rule", "updated_at"),
        ("rule_log", "created_at"),
        ("perception_log", "created_at"),
        ("meaningful_events", "created_at"),
        ("token_usage", "created_at"),
        ("biometric", "created_at"),
        ("task_record_progress", "created_at"),
        ("task_record_progress", "updated_at"),
        ("task_record_progress", "archived_at"),
        ("task_record_progress", "expires_at"),
        ("task_record_duration", "created_at"),
        ("task_record_duration", "updated_at"),
        ("task_record_duration", "archived_at"),
        ("task_record_duration", "active_session_start_at"),
        ("task_record_duration_session", "start_at"),
        ("task_record_duration_session", "end_at"),
        ("task_record_duration_session", "archived_at"),
        ("task_record_event", "created_at"),
        ("task_record_event", "updated_at"),
        ("task_record_event", "expires_at"),
        ("task_record_event_entry", "at"),
        ("task_terminate_log", "terminated_at"),
    ],
)
def test_schema_time_column_is_integer(real_db, table, column):
    _assert_column_integer(real_db, table, column)


def test_user_version_at_baseline(real_db):
    import sqlite3

    from miloco.database.connector import _DB_SCHEMA_VERSION

    conn = sqlite3.connect(str(real_db))
    try:
        v = conn.execute("PRAGMA user_version").fetchone()[0]
        assert v == _DB_SCHEMA_VERSION, (
            f"PRAGMA user_version={v} 应为 {_DB_SCHEMA_VERSION}"
        )
    finally:
        conn.close()


# ── 应用层:INSERT 写 Unix ms,SELECT 出口转 UTC ISO ──────────────────────────


def test_task_create_writes_ms_and_exits_iso(real_db):
    from miloco.database.connector import get_db_connector
    from miloco.database.task_repo import TaskRepo

    repo = TaskRepo()
    ts_lo = int(time.time() * 1000) - 5000
    repo.create_task(task_id="t1", description="d1")
    ts_hi = int(time.time() * 1000) + 5000

    row = get_db_connector().execute_query(
        "SELECT created_at FROM task WHERE task_id = ?", ("t1",)
    )[0]
    _assert_ms_in_range("task.created_at DB", row["created_at"], ts_lo, ts_hi)

    view = repo.get_full_view("t1")
    _assert_iso_local("task.created_at API", view["created_at"])


def test_task_pause_writes_ms(real_db):
    from miloco.database.connector import get_db_connector
    from miloco.database.task_repo import TaskRepo

    repo = TaskRepo()
    repo.create_task(task_id="t1", description="d1")
    ts_lo = int(time.time() * 1000) - 5000
    repo.set_status("t1", "paused")
    ts_hi = int(time.time() * 1000) + 5000

    row = get_db_connector().execute_query(
        "SELECT paused_at FROM task WHERE task_id = ?", ("t1",)
    )[0]
    _assert_ms_in_range("task.paused_at", row["paused_at"], ts_lo, ts_hi)


def test_kv_set_writes_ms(real_db):
    from miloco.database.connector import get_db_connector
    from miloco.database.kv_repo import KVRepo

    ts_lo = int(time.time() * 1000) - 5000
    KVRepo().set("k1", "v1")
    ts_hi = int(time.time() * 1000) + 5000

    row = get_db_connector().execute_query(
        "SELECT created_at, updated_at FROM kv WHERE key = ?", ("k1",)
    )[0]
    _assert_ms_in_range("kv.created_at", row["created_at"], ts_lo, ts_hi)
    _assert_ms_in_range("kv.updated_at", row["updated_at"], ts_lo, ts_hi)


def test_kv_upsert_writes_ms(real_db):
    from miloco.database.connector import get_db_connector
    from miloco.database.kv_repo import KVRepo

    repo = KVRepo()
    repo.set("k1", "v1")
    ts_lo = int(time.time() * 1000) - 5000
    repo.set("k1", "v2")
    ts_hi = int(time.time() * 1000) + 5000

    row = get_db_connector().execute_query(
        "SELECT updated_at FROM kv WHERE key = ?", ("k1",)
    )[0]
    _assert_ms_in_range("kv.updated_at(upsert)", row["updated_at"], ts_lo, ts_hi)


def test_person_create_writes_ms_and_exits_iso(real_db):
    from miloco.database.connector import get_db_connector
    from miloco.database.person_repo import PersonRepo

    repo = PersonRepo()
    ts_lo = int(time.time() * 1000) - 5000
    pid = repo.create(name="张三", role=None)
    ts_hi = int(time.time() * 1000) + 5000

    row = get_db_connector().execute_query(
        "SELECT created_at, updated_at FROM person WHERE id = ?", (pid,)
    )[0]
    _assert_ms_in_range("person.created_at DB", row["created_at"], ts_lo, ts_hi)
    _assert_ms_in_range("person.updated_at DB", row["updated_at"], ts_lo, ts_hi)

    p = repo.get_by_id(pid)
    _assert_iso_local("person.created_at API", p.created_at)
    _assert_iso_local("person.updated_at API", p.updated_at)


def test_person_update_writes_ms(real_db):
    from miloco.database.connector import get_db_connector
    from miloco.database.person_repo import PersonRepo

    repo = PersonRepo()
    pid = repo.create(name="张三", role=None)
    ts_lo = int(time.time() * 1000) - 5000
    repo.update(pid, name="李四")
    ts_hi = int(time.time() * 1000) + 5000

    row = get_db_connector().execute_query(
        "SELECT updated_at FROM person WHERE id = ?", (pid,)
    )[0]
    _assert_ms_in_range(
        "person.updated_at(after update)", row["updated_at"], ts_lo, ts_hi
    )


def _make_rule(task_id: str, name: str):
    from miloco.rule.schema import Rule, RuleCondition, RuleLifecycle, RuleMode

    return Rule(
        id="will-be-overwritten",
        name=name,
        task_id=task_id,
        mode=RuleMode.EVENT,
        lifecycle=RuleLifecycle.PERMANENT,
        enabled=True,
        condition=RuleCondition(
            perceive_device_ids=["dev1"], query="测试查询"
        ),
        actions=[],
        action_descriptions=[],
        on_enter_actions=[],
        on_enter_desc=None,
        on_exit_actions=[],
        on_exit_desc=None,
        on_target_desc=None,
        terminate_when=None,
        exit_debounce_seconds=60,
        duration_seconds=None,
        duration_ratio=0.8,
    )


def test_rule_create_writes_ms_and_exits_iso(real_db):
    from miloco.database.connector import get_db_connector
    from miloco.database.rule_repo import RuleRepo
    from miloco.database.task_repo import TaskRepo

    TaskRepo().create_task(task_id="task1", description="d1")
    repo = RuleRepo()
    ts_lo = int(time.time() * 1000) - 5000
    rule_id = repo.create(_make_rule("task1", "测试规则"))
    ts_hi = int(time.time() * 1000) + 5000
    assert rule_id is not None

    row = get_db_connector().execute_query(
        "SELECT created_at, updated_at FROM rule WHERE id = ?", (rule_id,)
    )[0]
    _assert_ms_in_range("rule.created_at DB", row["created_at"], ts_lo, ts_hi)
    _assert_ms_in_range("rule.updated_at DB", row["updated_at"], ts_lo, ts_hi)

    rule = repo.get_by_id(rule_id)
    _assert_iso_local("rule.created_at API", rule.created_at)
    _assert_iso_local("rule.updated_at API", rule.updated_at)


def test_rule_update_writes_ms(real_db):
    from miloco.database.connector import get_db_connector
    from miloco.database.rule_repo import RuleRepo
    from miloco.database.task_repo import TaskRepo

    TaskRepo().create_task(task_id="task1", description="d1")
    repo = RuleRepo()
    rule_id = repo.create(_make_rule("task1", "原始名"))
    rule = repo.get_by_id(rule_id)
    rule.name = "改名"
    ts_lo = int(time.time() * 1000) - 5000
    assert repo.update(rule) is True
    ts_hi = int(time.time() * 1000) + 5000

    row = get_db_connector().execute_query(
        "SELECT updated_at FROM rule WHERE id = ?", (rule_id,)
    )[0]
    _assert_ms_in_range(
        "rule.updated_at(after update)", row["updated_at"], ts_lo, ts_hi
    )
