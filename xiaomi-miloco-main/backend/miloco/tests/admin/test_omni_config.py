"""GET/PUT/activate/delete/test/models /api/admin/omni-config 端到端测试。

多档案模型:档案名 label = 唯一 id;active = model.omni;profiles = model.omni_profiles。
- api_key 打码(前3…后4),不泄漏全文;
- PUT 按 label upsert + 激活;original_label 支持改名;重名→409;空名→400;
- api_key 留空 = 沿用该档案原 key(按 label 解析);
- activate / delete 按 label;models / test 按 label 取已存 key。
环境隔离:删 MILOCO_MODEL__OMNI__* 环境变量,否则 env 优先级高会盖过 config.json。
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from miloco.admin.router import router


@pytest.fixture
def client(tmp_path, monkeypatch):
    from miloco.config.settings import reset_settings

    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    monkeypatch.delenv("MILOCO_DIRECTORIES__STORAGE", raising=False)
    monkeypatch.delenv("MILOCO_MODEL__OMNI__API_KEY", raising=False)
    monkeypatch.delenv("MILOCO_MODEL__OMNI__MODEL", raising=False)
    monkeypatch.delenv("MILOCO_MODEL__OMNI__BASE_URL", raising=False)
    # 写空 config.json 覆盖 settings.yaml 出厂档案,给用例确定性的"干净起点"
    import json as _json

    (tmp_path / "config.json").write_text(
        _json.dumps(
            {
                "model": {
                    "omni": {
                        "label": "",
                        "model": "xiaomi/mimo-v2.5",
                        "base_url": "https://api.xiaomimimo.com/v1",
                        "api_key": "",
                    },
                    "omni_profiles": [],
                }
            }
        ),
        encoding="utf-8",
    )
    reset_settings()
    app = FastAPI()
    app.include_router(router, prefix="/api")
    yield TestClient(app)
    reset_settings()


def _get(client):
    return client.get("/api/admin/omni-config").json()["data"]


# ─── GET / PUT / 档案(label=id) ────────────────────────────────────────────


def test_get_default_active_no_profiles(client):
    data = _get(client)
    assert data["active"]["model"] == "xiaomi/mimo-v2.5"
    assert data["active"]["has_key"] is False
    assert data["profiles"] == []


def test_put_creates_and_activates(client):
    out = client.put(
        "/api/admin/omni-config",
        json={"label": "配置1", "model": "qwen3-omni-flash", "base_url": "https://q/v1", "api_key": "sk-faketestkey1234abcd"},
    ).json()["data"]
    assert out["active"]["label"] == "配置1"
    assert out["active"]["model"] == "qwen3-omni-flash"
    assert out["active"]["has_key"] is True
    assert out["active"]["api_key_masked"] == "sk-…abcd"
    assert len(out["profiles"]) == 1
    p = out["profiles"][0]
    assert p["label"] == "配置1" and p["active"] is True and p["has_key"] is True


def test_put_empty_label_400(client):
    resp = client.put(
        "/api/admin/omni-config",
        json={"label": "  ", "model": "m", "base_url": "https://x/v1", "api_key": "sk-k123456789"},
    )
    assert resp.status_code == 400


def test_second_profile_has_independent_key(client):
    # 第一套带 key
    client.put(
        "/api/admin/omni-config",
        json={"label": "甲", "model": "m1", "base_url": "https://x/v1", "api_key": "sk-keyforjia12"},
    )
    # 另一套(新 label)不传 key → 不借别人的(key 属该档案)
    out = client.put(
        "/api/admin/omni-config",
        json={"label": "乙", "model": "m2", "base_url": "https://x/v1"},
    ).json()["data"]
    assert out["active"]["label"] == "乙"
    assert out["active"]["has_key"] is False
    assert len(out["profiles"]) == 2


def test_update_same_label_blank_key_keeps_it(client):
    client.put(
        "/api/admin/omni-config",
        json={"label": "甲", "model": "m1", "base_url": "https://x/v1", "api_key": "sk-keyforjia12"},
    )
    # 同名再存、不传 key、改了 model → key 沿用
    out = client.put(
        "/api/admin/omni-config",
        json={"label": "甲", "model": "m2", "base_url": "https://x/v1", "original_label": "甲"},
    ).json()["data"]
    assert out["active"]["model"] == "m2"
    assert out["active"]["has_key"] is True
    assert len(out["profiles"]) == 1  # 同名 = 同一档案,未新增


def test_rename_via_original_label(client):
    client.put(
        "/api/admin/omni-config",
        json={"label": "配置1", "model": "m1", "base_url": "https://x/v1", "api_key": "sk-keyforaaa12"},
    )
    out = client.put(
        "/api/admin/omni-config",
        json={"label": "生产Q", "model": "m1", "base_url": "https://x/v1", "original_label": "配置1"},
    ).json()["data"]
    assert out["active"]["label"] == "生产Q"
    assert out["active"]["has_key"] is True  # key 沿用
    assert len(out["profiles"]) == 1  # 改名而非新增
    assert out["profiles"][0]["label"] == "生产Q"


def test_put_activate_false_only_adds_to_list(client):
    """activate=false:只入列表,不切换当前生效(「保存」按钮的行为)。"""
    out = client.put(
        "/api/admin/omni-config",
        json={"label": "甲", "model": "m1", "base_url": "https://x/v1", "api_key": "sk-k123456789", "activate": False},
    ).json()["data"]
    assert out["active"]["label"] != "甲"  # 未切换(active 仍是默认)
    assert any(p["label"] == "甲" for p in out["profiles"])  # 已入列表
    assert all(not p["active"] for p in out["profiles"])  # 列表里没有一行是当前


def test_put_activate_false_editing_active_still_syncs(client):
    """即便 activate=false,编辑的若正是当前生效那套,active 仍同步刷新(改 model/key 即时生效)。"""
    client.put(
        "/api/admin/omni-config",
        json={"label": "甲", "model": "m1", "base_url": "https://x/v1", "api_key": "sk-k111111111"},
    )  # 默认 activate=true → 甲 成为当前
    out = client.put(
        "/api/admin/omni-config",
        json={"label": "甲", "model": "m2", "base_url": "https://x/v1", "original_label": "甲", "activate": False},
    ).json()["data"]
    assert out["active"]["label"] == "甲"
    assert out["active"]["model"] == "m2"  # 当前生效那套的改动即时同步


def test_duplicate_label_409(client):
    client.put("/api/admin/omni-config", json={"label": "甲", "model": "m1", "base_url": "https://x/v1", "api_key": "sk-k111111111"})
    client.put("/api/admin/omni-config", json={"label": "乙", "model": "m2", "base_url": "https://x/v1"})
    # 把「乙」改名成已存在的「甲」→ 409
    resp = client.put(
        "/api/admin/omni-config",
        json={"label": "甲", "model": "m2", "base_url": "https://x/v1", "original_label": "乙"},
    )
    assert resp.status_code == 409


def test_activate_by_label(client):
    client.put("/api/admin/omni-config", json={"label": "甲", "model": "m1", "base_url": "https://x/v1", "api_key": "sk-k111111111"})
    client.put("/api/admin/omni-config", json={"label": "乙", "model": "m2", "base_url": "https://x/v1"})
    out = client.post("/api/admin/omni-config/activate", json={"label": "甲"}).json()["data"]
    assert out["active"]["label"] == "甲"
    actives = {p["label"]: p["active"] for p in out["profiles"]}
    assert actives == {"甲": True, "乙": False}


def test_activate_missing_404(client):
    resp = client.post("/api/admin/omni-config/activate", json={"label": "不存在"})
    assert resp.status_code == 404


def test_delete_by_label(client):
    client.put("/api/admin/omni-config", json={"label": "甲", "model": "m1", "base_url": "https://x/v1", "api_key": "sk-k111111111"})
    client.put("/api/admin/omni-config", json={"label": "乙", "model": "m2", "base_url": "https://x/v1"})
    out = client.post("/api/admin/omni-config/delete", json={"label": "乙"}).json()["data"]
    assert [p["label"] for p in out["profiles"]] == ["甲"]


def test_put_hot_reload_visible_to_resolve_live(client):
    """PUT 后 resolve_live_omni_config 立即取到新 model/base_url —— 热生效契约。"""
    from miloco.perception.engine.config import OmniConfig
    from miloco.perception.engine.omni.omni_client import resolve_live_omni_config

    client.put(
        "/api/admin/omni-config",
        json={"label": "热", "model": "hot-model", "base_url": "https://hot.example/v1", "api_key": "sk-hotkey123456"},
    )
    base = OmniConfig(model="old", base_url="old", api_key="k0", timeout=123.0)
    live = resolve_live_omni_config(base)
    assert live.model == "hot-model"
    assert live.base_url == "https://hot.example/v1"
    assert live.timeout == 123.0  # 非用户字段保持快照


# ─── 测试连接 / 列模型(mock httpx) ─────────────────────────────────────────


class _FakeResp:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.text = text

    def json(self):
        return self._json


def _fake_async_client(resp=None, exc=None, get_resp=None, post_resp=None):
    # get_resp/post_resp 可分别指定(probe_omni 先 GET /models,404/405 才回退 chat 的 POST)
    g = get_resp if get_resp is not None else resp
    p = post_resp if post_resp is not None else resp

    class _C:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, *a, **k):
            if exc:
                raise exc
            return g

        async def post(self, *a, **k):
            if exc:
                raise exc
            return p

    return _C


def test_test_connection_ok_model_in_list(client, monkeypatch):
    from miloco.admin import router as r

    monkeypatch.setattr(
        r.httpx, "AsyncClient",
        _fake_async_client(resp=_FakeResp(200, {"data": [{"id": "m1"}]})),
    )
    data = client.post(
        "/api/admin/omni-config/test",
        json={"model": "m1", "base_url": "https://x/v1", "api_key": "sk-xxx"},
    ).json()["data"]
    assert data["ok"] is True
    assert data["code"] == "ok_model_found"
    assert "模型可用" in data["message"]


def test_test_connection_ok_model_not_in_list(client, monkeypatch):
    from miloco.admin import router as r

    monkeypatch.setattr(
        r.httpx, "AsyncClient",
        _fake_async_client(resp=_FakeResp(200, {"data": [{"id": "other"}]})),
    )
    data = client.post(
        "/api/admin/omni-config/test",
        json={"model": "m1", "base_url": "https://x/v1", "api_key": "sk-xxx"},
    ).json()["data"]
    assert data["ok"] is True
    assert data["code"] == "ok"  # 连通但目标模型不在列表


def test_test_connection_not_found(client, monkeypatch):
    # GET /models 404 → 回退 chat 探测,chat 也 404 → not_found
    from miloco.admin import router as r

    monkeypatch.setattr(
        r.httpx, "AsyncClient",
        _fake_async_client(get_resp=_FakeResp(404), post_resp=_FakeResp(404, text="no such model")),
    )
    data = client.post(
        "/api/admin/omni-config/test",
        json={"model": "m1", "base_url": "https://x/v1", "api_key": "sk-x"},
    ).json()["data"]
    assert data["ok"] is False
    assert data["code"] == "not_found"


def test_test_connection_rejected_authed(client, monkeypatch):
    # GET /models 404 → 回退 chat,chat 返 400(鉴权过、仅请求体被拒)→ rejected_authed
    from miloco.admin import router as r

    monkeypatch.setattr(
        r.httpx, "AsyncClient",
        _fake_async_client(get_resp=_FakeResp(404), post_resp=_FakeResp(400, text="bad request")),
    )
    data = client.post(
        "/api/admin/omni-config/test",
        json={"model": "m1", "base_url": "https://x/v1", "api_key": "sk-x"},
    ).json()["data"]
    assert data["ok"] is False
    assert data["code"] == "rejected_authed"


def test_test_connection_bad_key(client, monkeypatch):
    from miloco.admin import router as r

    monkeypatch.setattr(
        r.httpx, "AsyncClient", _fake_async_client(resp=_FakeResp(401, text="unauthorized"))
    )
    data = client.post(
        "/api/admin/omni-config/test",
        json={"model": "m1", "base_url": "https://x/v1", "api_key": "sk-bad"},
    ).json()["data"]
    assert data["ok"] is False
    assert data["code"] == "bad_key"
    assert data["status"] == 401
    assert "API Key" in data["message"]


def test_test_connection_unreachable(client, monkeypatch):
    import httpx
    from miloco.admin import router as r

    monkeypatch.setattr(
        r.httpx, "AsyncClient", _fake_async_client(exc=httpx.ConnectError("boom"))
    )
    data = client.post(
        "/api/admin/omni-config/test",
        json={"model": "m1", "base_url": "https://nope.invalid/v1", "api_key": "sk-x"},
    ).json()["data"]
    assert data["ok"] is False
    assert data["code"] == "unreachable"
    assert "无法连接" in data["message"]


def test_test_connection_no_key(client):
    data = client.post(
        "/api/admin/omni-config/test",
        json={"model": "m1", "base_url": "https://x/v1"},
    ).json()["data"]
    assert data["ok"] is False
    assert data["code"] == "no_key"
    assert "未配置" in data["message"]


def test_list_models_ok(client, monkeypatch):
    from miloco.admin import router as r

    monkeypatch.setattr(
        r.httpx, "AsyncClient",
        _fake_async_client(resp=_FakeResp(200, {"data": [{"id": "b"}, {"id": "a"}]})),
    )
    data = client.post(
        "/api/admin/omni-config/models",
        json={"base_url": "https://x/v1", "api_key": "sk-x"},
    ).json()["data"]
    assert data["ok"] is True
    assert data["models"] == ["a", "b"]  # sorted


def test_list_models_no_key(client):
    data = client.post(
        "/api/admin/omni-config/models", json={"base_url": "https://x/v1"}
    ).json()["data"]
    assert data["ok"] is False
    assert data["code"] == "no_key"
    assert "未配置" in data["message"]
