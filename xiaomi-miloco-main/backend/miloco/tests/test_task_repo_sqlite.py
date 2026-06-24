# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""TaskRepo SQLite 集成测试（方案 P：create_task 仅占位，link 由后续 endpoint 挂）。"""

import pytest


@pytest.fixture
def real_db(tmp_path, monkeypatch):
    """每个测试起全新的 SQLite + initialize_database 建表。"""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("MILOCO_DATABASE__PATH", str(db_file))

    from miloco.config import reset_settings

    reset_settings()
    import miloco.database.connector as connector_module

    monkeypatch.setattr(connector_module, "db_connector", None)
    connector_module.init_database()

    yield db_file
    reset_settings()


@pytest.fixture
def repo(real_db):
    from miloco.database.task_repo import TaskRepo

    return TaskRepo()


def test_create_task_inserts_placeholder_only(repo):
    repo.create_task(task_id="drink_water", description="每天喝 8 杯水")
    view = repo.get_full_view("drink_water")
    assert view["status"] == "active"
    assert view["description"] == "每天喝 8 杯水"
    # 方案 P：create 不再写 task_link
    assert view["links"] == []


def test_create_409_on_duplicate_task_id(repo):
    from miloco.database.task_repo import TaskLinkConflict

    repo.create_task(task_id="drink_water", description="d1")
    with pytest.raises(TaskLinkConflict):
        repo.create_task(task_id="drink_water", description="d2")
    view = repo.get_full_view("drink_water")
    assert view["description"] == "d1"


def test_add_link_fk_rejects_missing_task(repo):
    from miloco.database.task_repo import TaskLinkConflict

    with pytest.raises(TaskLinkConflict):
        repo.add_link("ghost", "rule", "r1")


def test_add_link_rejects_memory_kind(repo):
    """方案 P：memory kind 已废除。"""
    from miloco.database.task_repo import TaskLinkConflict

    repo.create_task(task_id="t1", description="d")
    with pytest.raises(TaskLinkConflict):
        repo.add_link("t1", "memory", "x")


def test_add_link_unique_rejects_cross_task_ref(repo):
    from miloco.database.task_repo import TaskLinkConflict

    repo.create_task(task_id="t1", description="d")
    repo.create_task(task_id="t2", description="d")
    repo.add_link("t1", "cron", "job1")
    with pytest.raises(TaskLinkConflict):
        repo.add_link("t2", "cron", "job1")


def test_set_status_paused_then_active(repo):
    repo.create_task(task_id="t1", description="d")
    assert repo.set_status("t1", "paused") == "ok"
    view = repo.get_full_view("t1")
    assert view["status"] == "paused"
    assert view["paused_at"] is not None
    assert repo.set_status("t1", "paused") == "noop"
    assert repo.set_status("t1", "active") == "ok"
    view = repo.get_full_view("t1")
    assert view["status"] == "active"
    assert view["paused_at"] is None


def test_set_status_not_found(repo):
    assert repo.set_status("ghost", "paused") == "not_found"


def test_update_description(repo):
    repo.create_task(task_id="t1", description="old")
    assert repo.update_description("t1", "new") is True
    assert repo.get_full_view("t1")["description"] == "new"
    assert repo.update_description("ghost", "x") is False


def test_delete_task_cascades_to_task_link(repo, real_db):
    import sqlite3

    repo.create_task(task_id="t1", description="d")
    repo.add_link("t1", "cron", "job1")
    deleted = repo.delete_task("t1")
    assert deleted == 1
    assert repo.get_full_view("t1") is None
    with sqlite3.connect(str(real_db)) as conn:
        cnt = conn.execute(
            "SELECT COUNT(*) FROM task_link WHERE task_id='t1'"
        ).fetchone()[0]
        assert cnt == 0


def test_delete_task_idempotent_returns_zero(repo):
    assert repo.delete_task("ghost") == 0


def test_get_full_view_returns_none_for_missing(repo):
    assert repo.get_full_view("nope") is None


def test_get_rule_refs(repo):
    """方案 P：rule link 由 rule create 内部写；此处直接 add_link 模拟。"""
    repo.create_task(task_id="t1", description="d")
    repo.add_link("t1", "rule", "r1")
    repo.add_link("t1", "rule", "r2")
    assert sorted(repo.get_rule_refs("t1")) == ["r1", "r2"]
    assert repo.get_rule_refs("ghost") == []


def test_delete_link_by_ref_clears_dangling_row(repo):
    repo.create_task(task_id="t1", description="d")
    repo.add_link("t1", "rule", "r1")
    repo.add_link("t1", "rule", "r2")
    repo.add_link("t1", "cron", "c1")
    assert repo.delete_link_by_ref("rule", "r1") == 1
    assert repo.get_rule_refs("t1") == ["r2"]
    full = repo.get_full_view("t1")
    assert {(ln["kind"], ln["ref"]) for ln in full["links"]} == {
        ("rule", "r2"),
        ("cron", "c1"),
    }


def test_delete_link_by_ref_missing_returns_zero(repo):
    assert repo.delete_link_by_ref("rule", "ghost") == 0


def test_list_all_returns_all_tasks_with_links(repo):
    repo.create_task(task_id="t1", description="d1")
    repo.add_link("t1", "rule", "r1")
    repo.create_task(task_id="t2", description="d2")
    repo.add_link("t2", "cron", "c2")
    rows = repo.list_all()
    assert {r["task_id"] for r in rows} == {"t1", "t2"}
    by_id = {r["task_id"]: r for r in rows}
    assert by_id["t1"]["links"] == [{"kind": "rule", "ref": "r1"}]
    assert by_id["t2"]["links"] == [{"kind": "cron", "ref": "c2"}]
