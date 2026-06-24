"""update_person 文件层同步守卫 + _resolve_member 漂移补写/幂等 的回归测试。

锁两条状态交互型分支:
  - update_person 仅对"已有样本目录"的 person 同步 meta——无样本 person 被改名/改角色时
    不凭空建 persons/<id>/ 目录(否则 list_persons 多出 (pid,False,0,0) 扰动 IdentityEngine
    snapshot、触发全相机识别重置)。
  - _resolve_member 按 member_id 绑定既有成员时,带了与 SQL 不同的 name/role 才补写 SQL,
    相同则不写(幂等);按 name 走新建/复用。

不引入 TestClient:直接 await 路由协程 + 桩 manager / 真 IdentityLibrary(tmp_path)。
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from miloco.perception.engine.identity.library import IdentityLibrary
from miloco.person import router as prouter
from miloco.person.router import _resolve_member, update_person
from miloco.person.schema import PersonUpdate

_PID = "33333333-3333-4333-8333-333333333333"


# ---- update_person 文件层同步守卫 ----


@pytest.fixture
def lib(tmp_path, monkeypatch) -> IdentityLibrary:
    library = IdentityLibrary(tmp_path / "identity_lib")
    monkeypatch.setattr(prouter, "_get_identity_library", lambda: library)
    # 端点只用 manager.person_service.update_person(写 SQL),桩成 no-op。
    monkeypatch.setattr(
        prouter, "manager",
        SimpleNamespace(person_service=SimpleNamespace(update_person=lambda *a, **k: None)),
    )
    return library


async def test_update_person_no_dir_skips_meta_and_no_mkdir(lib: IdentityLibrary):
    # 无样本 person(无 persons/<id>/ 目录):改名/改角色不该凭空建目录、不写 meta
    await update_person(_PID, PersonUpdate(name="张三", role="爸爸"), current_user="t")
    assert not (lib.persons_dir / _PID).exists()
    assert lib.get_name(_PID) is None and lib.get_role(_PID) is None


async def test_update_person_with_dir_syncs_meta(lib: IdentityLibrary):
    # 已有样本目录(模拟已注册)的 person:改名/改角色即时同步进 meta
    lib.set_name(_PID, "旧名")  # 建目录 + 写 meta
    await update_person(_PID, PersonUpdate(name="新名", role="爸爸"), current_user="t")
    assert lib.get_name(_PID) == "新名"
    assert lib.get_role(_PID) == "爸爸"


# ---- _resolve_member 漂移补写 / 幂等 ----


def _stub_svc(existing, monkeypatch) -> SimpleNamespace:
    svc = SimpleNamespace(get_person=lambda pid: existing, update_person=MagicMock())
    monkeypatch.setattr(prouter, "manager", SimpleNamespace(person_service=svc))
    return svc


def test_resolve_member_syncs_changed_name_and_role(monkeypatch):
    svc = _stub_svc(SimpleNamespace(name="张三", role="爸爸"), monkeypatch)
    assert _resolve_member(_PID, "王五", "妈妈") == _PID
    svc.update_person.assert_called_once_with(_PID, "王五", "妈妈")


def test_resolve_member_syncs_only_changed_field(monkeypatch):
    # name 与现值相同、role 变 → 只补 role(name 传 None=不改)
    svc = _stub_svc(SimpleNamespace(name="张三", role="爸爸"), monkeypatch)
    _resolve_member(_PID, "张三", "妈妈")
    svc.update_person.assert_called_once_with(_PID, None, "妈妈")


def test_resolve_member_noop_when_same(monkeypatch):
    # name/role 都与现值相同 → 不写 SQL(幂等)
    svc = _stub_svc(SimpleNamespace(name="张三", role="爸爸"), monkeypatch)
    assert _resolve_member(_PID, "张三", "爸爸") == _PID
    svc.update_person.assert_not_called()


def test_resolve_member_by_name_delegates_to_get_or_create(monkeypatch):
    monkeypatch.setattr(prouter, "_get_or_create_person_by_name", lambda n, r: "new-pid")
    monkeypatch.setattr(prouter, "manager", SimpleNamespace(person_service=SimpleNamespace()))
    assert _resolve_member(None, "张三", "爸爸") == "new-pid"


def test_resolve_member_none_when_no_id_no_name(monkeypatch):
    monkeypatch.setattr(prouter, "manager", SimpleNamespace(person_service=SimpleNamespace()))
    assert _resolve_member(None, None, None) is None
