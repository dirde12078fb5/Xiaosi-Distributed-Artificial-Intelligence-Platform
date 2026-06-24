"""LRU snapshot client tests — implementation lives in catalog module."""

from __future__ import annotations

import pytest

import miloco_cli.catalog as catalog
import miloco_cli.client as client_mod


@pytest.fixture
def fake_backend(monkeypatch):
    """Inject a preset LRU snapshot via api_get; CLI no longer POSTs touches."""
    state: dict = {"version": 1, "updated_at": None, "histories": {}}

    def fake_get(path, params=None):
        assert path == "/api/miot/device_history"
        return {"code": 0, "message": "ok", "data": dict(state)}

    monkeypatch.setattr(client_mod, "api_get", fake_get)
    return state


def test_load_returns_empty_when_backend_unreachable(monkeypatch):
    """api_get sys.exits on connection failure; load_lru_state should swallow → empty state."""

    def fail(*a, **kw):
        raise SystemExit(2)

    monkeypatch.setattr(client_mod, "api_get", fail)
    state = catalog.load_lru_state()
    assert state["histories"] == {}


def test_load_returns_backend_snapshot(fake_backend):
    fake_backend["histories"]["dev1"] = ["prop.2.1", "prop.2.2"]
    assert catalog.load_lru_state()["histories"]["dev1"] == ["prop.2.1", "prop.2.2"]


def test_cold_start_dedup_and_cap():
    keys = catalog.cold_start_keys(
        ["a", "b", "a", "c", "d", "e", "f", "g", "h"], capacity=5
    )
    assert keys == ["a", "b", "c", "d", "e"]


def test_merged_keys_translates_iid_to_type_name(fake_backend):
    fake_backend["histories"]["dev1"] = ["prop.2.2", "prop.2.1"]  # MRU first
    iid_to_key = {
        "prop.2.1": "brightness",
        "prop.2.2": "color_temp",
    }
    merged = catalog.merged_keys(
        "dev1",
        cold_start=["on", "brightness", "battery"],
        capacity=5,
        iid_to_key=iid_to_key,
    )
    # LRU 翻译后 ["color_temp", "brightness"] 优先 → cold_start 顶上去重
    assert merged == ["color_temp", "brightness", "on", "battery"]


def test_merged_keys_drops_unknown_iids(fake_backend):
    """spec 改名 / 白名单变动 → 老 iid 翻译不到，应静默丢弃。"""
    fake_backend["histories"]["dev1"] = ["prop.99.99", "prop.2.1"]
    iid_to_key = {"prop.2.1": "brightness"}
    merged = catalog.merged_keys(
        "dev1",
        cold_start=["on"],
        capacity=5,
        iid_to_key=iid_to_key,
    )
    assert merged == ["brightness", "on"]


def test_merged_keys_with_explicit_state():
    """merged_keys 接受预加载 state，避免每个设备多打一次 API。"""
    state = {"histories": {"dev1": ["prop.2.1", "prop.2.2"]}}
    iid_to_key = {"prop.2.1": "alpha", "prop.2.2": "beta"}
    merged = catalog.merged_keys(
        "dev1",
        cold_start=["x", "y"],
        capacity=5,
        state=state,
        iid_to_key=iid_to_key,
    )
    assert merged == ["alpha", "beta", "x", "y"]
