"""GET/POST /api/admin/debug 的端到端测试。"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from miloco.admin.router import router
from miloco.observability import debug as debug_mod


@pytest.fixture
def client(tmp_path, monkeypatch):
    from miloco.config.settings import reset_settings

    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    monkeypatch.delenv("MILOCO_DIRECTORIES__STORAGE", raising=False)
    debug_mod._reset_cache_for_tests()
    reset_settings()  # 让 log-pack endpoint 用新的 workspace_dir
    app = FastAPI()
    app.include_router(router, prefix="/api")
    yield TestClient(app)
    reset_settings()


def test_get_debug_default(client):
    resp = client.get("/api/admin/debug")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["enabled"] is False
    assert data["source"] == "default"
    assert data["runtime_override"] is None
    assert data["file_flag_present"] is False


def test_post_debug_enables_runtime_override(client):
    resp = client.post("/api/admin/debug", json={"enabled": True})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["enabled"] is True
    assert data["source"] == "runtime"
    assert data["runtime_override"] is True


def test_post_debug_invalid_body_422(client):
    resp = client.post("/api/admin/debug", json={"enabled": "yes"})
    assert resp.status_code == 422


def test_post_debug_null_body_422(client):
    """enabled=null 已不再支持,应返 422。"""
    resp = client.post("/api/admin/debug", json={"enabled": None})
    assert resp.status_code == 422


# ─── log-pack endpoint ─────────────────────────────────────────────────────────

import sqlite3 as _sqlite3  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

from miloco.admin import log_pack  # noqa: E402


def _seed_db(path: _Path) -> None:
    conn = _sqlite3.connect(path)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (1)")
    conn.commit()
    conn.close()


def _seed_min(home: _Path) -> None:
    # workspace_dir = MILOCO_HOME 顶级(storage=".",settings 默认),db 在 home 根。
    _seed_db(home / "observability.db")


def test_post_log_pack_success(client, tmp_path, monkeypatch):
    _seed_min(tmp_path)
    resp = client.post("/api/admin/debug/log-pack")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert _Path(data["path"]).exists()
    assert data["size_bytes"] > 0
    assert data["components"]["observability_db"]["present"] is True
    assert "miloco_db" not in data["components"]


def test_post_log_pack_excludes_miloco_db(client, tmp_path, monkeypatch):
    """miloco.db 含 MiOT token / PII,即便存在也不入包。"""
    import tarfile as _tar
    _seed_db(tmp_path / "observability.db")
    _seed_db(tmp_path / "miloco.db")
    resp = client.post("/api/admin/debug/log-pack")
    assert resp.status_code == 200
    data = resp.json()["data"]
    with _tar.open(data["path"], "r:gz") as t:
        names = t.getnames()
    assert "observability.db" in names
    assert "miloco.db" not in names


def test_post_log_pack_size_exceeded_returns_422(client, tmp_path, monkeypatch):
    _seed_min(tmp_path)
    monkeypatch.setattr(log_pack, "MAX_TOTAL_BYTES", 1)
    resp = client.post("/api/admin/debug/log-pack")
    assert resp.status_code == 422
    body = resp.json()
    assert "estimated_size_bytes" in body["detail"]
    assert body["detail"]["limit_bytes"] == 1
