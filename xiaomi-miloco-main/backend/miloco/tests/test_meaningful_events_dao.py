# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Unit tests for MeaningfulEventDao(D3-T3)."""

import time
import uuid

import pytest


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


@pytest.fixture
def dao(real_db):
    from miloco.database.meaningful_events_dao import MeaningfulEventDao

    return MeaningfulEventDao()


def _new_event_id() -> str:
    return str(uuid.uuid4())


def _insert(dao, **overrides):
    """Insert one event with sensible defaults; returns event_id."""
    eid = overrides.pop("event_id", _new_event_id())
    defaults = dict(
        event_id=eid,
        timestamp=overrides.pop("timestamp", int(time.time() * 1000)),
        text="test text",
        payload_json='{"caption": []}',
        has_rule_hit=False,
        has_suggestion=False,
        has_asr=False,
        device_ids=["cam_living_01"],
    )
    defaults.update(overrides)
    assert dao.insert(**defaults) is True
    return eid


class TestInsert:
    def test_basic_insert(self, dao):
        eid = _insert(
            dao,
            has_rule_hit=True,
            device_ids=["cam_living_01", "cam_kitchen_01"],
        )
        got = dao.get_by_id(eid)
        assert got is not None
        assert got["id"] == eid
        assert got["schema_version"] == 1
        assert got["has_rule_hit"] is True
        assert got["has_suggestion"] is False
        assert got["device_ids"] == ["cam_living_01", "cam_kitchen_01"]
        assert got["snapshot_count"] == 0

    def test_device_ids_json_roundtrip(self, dao):
        eid = _insert(dao, device_ids=["cam_a", "cam_b", "cam_c"])
        got = dao.get_by_id(eid)
        assert got["device_ids"] == ["cam_a", "cam_b", "cam_c"]

    def test_empty_device_ids(self, dao):
        """metadata-only 降级路径:device_ids 为空列表也应能写入(写前预检失败的场景)."""
        eid = _insert(dao, device_ids=[])
        got = dao.get_by_id(eid)
        assert got["device_ids"] == []

    def test_insert_duplicate_id_returns_false(self, dao):
        eid = _insert(dao)
        # 重复主键应失败(返回 False),不应抛
        ok = dao.insert(
            event_id=eid,
            timestamp=1,
            text="dup",
            payload_json="{}",
            has_rule_hit=False,
            has_suggestion=False,
            has_asr=False,
            device_ids=[],
        )
        assert ok is False


class TestUpdateSnapshotCount:
    def test_update_after_insert(self, dao):
        eid = _insert(dao, device_ids=["cam_living_01"])
        assert dao.get_by_id(eid)["snapshot_count"] == 0
        assert dao.update_snapshot_count(eid, 3) is True
        assert dao.get_by_id(eid)["snapshot_count"] == 3

    def test_update_partial_failure(self, dao):
        """模拟部分帧落盘失败:期望 3 张落 2 张,count = 2."""
        eid = _insert(dao, device_ids=["cam_a", "cam_b"])
        dao.update_snapshot_count(eid, 4)  # 2 device × 3 = 6 期望,实际 4
        assert dao.get_by_id(eid)["snapshot_count"] == 4


class TestQuery:
    def test_empty_db(self, dao):
        assert dao.query() == []

    def test_returns_desc_timestamp(self, dao):
        """timestamp DESC 排序:最新事件在前."""
        eid1 = _insert(dao, timestamp=1000)
        eid2 = _insert(dao, timestamp=3000)
        eid3 = _insert(dao, timestamp=2000)
        rows = dao.query()
        assert [r["id"] for r in rows] == [eid2, eid3, eid1]

    def test_time_window(self, dao):
        _insert(dao, timestamp=1000)
        eid2 = _insert(dao, timestamp=2000)
        eid3 = _insert(dao, timestamp=3000)
        _insert(dao, timestamp=4000)
        # since_ms <= ts < before_ms
        rows = dao.query(since_ms=2000, before_ms=3500)
        assert {r["id"] for r in rows} == {eid2, eid3}

    def test_pagination(self, dao):
        for i in range(5):
            _insert(dao, timestamp=1000 + i)
        page1 = dao.query(limit=2, offset=0)
        page2 = dao.query(limit=2, offset=2)
        page3 = dao.query(limit=2, offset=4)
        assert len(page1) == 2
        assert len(page2) == 2
        assert len(page3) == 1
        # 不重叠
        ids = {r["id"] for r in page1} | {r["id"] for r in page2} | {r["id"] for r in page3}
        assert len(ids) == 5


class TestGetById:
    def test_existing_event(self, dao):
        eid = _insert(dao, has_asr=True, device_ids=["cam_x"])
        got = dao.get_by_id(eid)
        assert got["id"] == eid
        assert got["has_asr"] is True

    def test_nonexistent_event(self, dao):
        assert dao.get_by_id("does-not-exist") is None


class TestDeleteBeforeDays:
    def test_no_delete_when_all_fresh(self, dao):
        _insert(dao)
        assert dao.delete_before_days(30) == 0
        assert len(dao.query()) == 1

    def test_delete_old_rows(self, dao, real_db):
        """v10 起 created_at 是 INTEGER ms (UTC 绝对时刻),cutoff 是 ms 数值比较。"""
        import sqlite3

        eid_old = _insert(dao)
        eid_fresh = _insert(dao)
        old_ms = int((time.time() - 31 * 86400) * 1000)
        conn = sqlite3.connect(str(real_db))
        try:
            conn.execute(
                "UPDATE meaningful_events SET created_at = ? WHERE id = ?",
                (old_ms, eid_old),
            )
            conn.commit()
        finally:
            conn.close()

        deleted = dao.delete_before_days(30)
        assert deleted == 1
        assert dao.get_by_id(eid_old) is None
        assert dao.get_by_id(eid_fresh) is not None

    def test_cutoff_uses_ms_absolute_time(self, dao, real_db):
        """v10 起 created_at 是 INTEGER ms,cutoff 数值比较,无时区歧义。"""
        import sqlite3

        eid = _insert(dao)
        # 25h ago
        ts_ms = int((time.time() - 25 * 3600) * 1000)
        conn = sqlite3.connect(str(real_db))
        try:
            conn.execute(
                "UPDATE meaningful_events SET created_at = ? WHERE id = ?",
                (ts_ms, eid),
            )
            conn.commit()
        finally:
            conn.close()

        # 2 天阈值:row 是 25h ago,< 48h,保留
        assert dao.delete_before_days(2) == 0
        assert dao.get_by_id(eid) is not None
        # 1 天阈值:row 是 25h ago,> 24h,应删
        assert dao.delete_before_days(1) == 1
        assert dao.get_by_id(eid) is None


class TestManagerSingleton:
    def test_lazy_singleton(self, monkeypatch, real_db):
        """连续两次 mgr.meaningful_events_dao 返回同一实例(对齐 register_session_manager 套路)."""
        # 不调 manager.initialize()(它会做完整初始化太重);直接构造 Manager 测 lazy property
        from miloco.manager import Manager

        # 重置 singleton 避免状态污染
        Manager._instance = None
        mgr = Manager()

        dao1 = mgr.meaningful_events_dao
        dao2 = mgr.meaningful_events_dao
        assert dao1 is dao2

        # 类型正确
        from miloco.database.meaningful_events_dao import MeaningfulEventDao

        assert isinstance(dao1, MeaningfulEventDao)
