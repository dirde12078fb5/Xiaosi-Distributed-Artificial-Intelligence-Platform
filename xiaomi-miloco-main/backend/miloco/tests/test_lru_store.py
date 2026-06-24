"""LRUStore behavior tests using a temp SQLite DB."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest
from miloco.miot.lru import LRUStore


class _TestConnector:
    """Minimum surface for LRUStore: execute_update / execute_query against a
    real SQLite file (in tempdir)。比 mock 更可信，schema bug 也能直接抓到。"""

    def __init__(self, path: Path):
        self._path = str(path)
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                """
                CREATE TABLE device_lru (
                    did TEXT NOT NULL,
                    key TEXT NOT NULL,
                    touched_at INTEGER NOT NULL,
                    PRIMARY KEY (did, key)
                )
                """
            )

    def execute_update(self, sql: str, params=None) -> int:
        with sqlite3.connect(self._path) as conn:
            cur = conn.cursor()
            cur.execute(sql, params or ())
            conn.commit()
            return cur.rowcount

    def execute_query(self, sql: str, params=None) -> list[dict]:
        with sqlite3.connect(self._path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql, params or ())
            return [dict(r) for r in cur.fetchall()]


@pytest.fixture
def store(tmp_path):
    return LRUStore(_TestConnector(tmp_path / "lru.sqlite"))


def _bump_touch(s, did, key, capacity=7):
    """Touch with a tiny sleep so timestamps are strictly increasing
    even when the test runs faster than 1µs."""
    time.sleep(0.001)
    s.touch(did, key, capacity=capacity)


def test_touch_inserts_to_head_and_caps(store):
    iids = [f"prop.2.{i}" for i in range(1, 9)]  # 8 iids, capacity=7 → 第一个 prop.2.1 被淘汰
    for iid in iids:
        _bump_touch(store, "dev1", iid, capacity=7)
    keys = store.load()["histories"]["dev1"]
    assert keys == list(reversed(iids[1:]))


def test_touch_reorders_existing(store):
    _bump_touch(store, "dev1", "prop.2.1")
    _bump_touch(store, "dev1", "prop.2.2")
    _bump_touch(store, "dev1", "prop.2.1")
    keys = store.load()["histories"]["dev1"]
    assert keys == ["prop.2.1", "prop.2.2"]


def test_touch_accepts_action_iid(store):
    """action.s.a 与 prop.s.p 同等存储，无形态过滤。"""
    _bump_touch(store, "dev1", "prop.2.1")
    _bump_touch(store, "dev1", "action.5.1")
    keys = store.load()["histories"]["dev1"]
    assert keys == ["action.5.1", "prop.2.1"]


def test_load_empty_when_not_initialized(store):
    state = store.load()
    assert state["histories"] == {}
    assert state["updated_at"] is None


def test_load_groups_by_did(store):
    _bump_touch(store, "dev1", "prop.2.1")
    _bump_touch(store, "dev2", "prop.3.1")
    _bump_touch(store, "dev1", "prop.2.2")
    state = store.load()
    assert state["histories"]["dev1"] == ["prop.2.2", "prop.2.1"]
    assert state["histories"]["dev2"] == ["prop.3.1"]


def test_capacity_per_device_independent(store):
    """capacity 是 per-did 的，dev1 满 7 不该影响 dev2。"""
    iids = [f"prop.2.{i}" for i in range(1, 9)]  # 8 iids, capacity=7 → 第一个被淘汰
    for iid in iids:
        _bump_touch(store, "dev1", iid, capacity=7)
    _bump_touch(store, "dev2", "prop.9.1")
    state = store.load()
    assert state["histories"]["dev1"] == list(reversed(iids[1:]))
    assert state["histories"]["dev2"] == ["prop.9.1"]
