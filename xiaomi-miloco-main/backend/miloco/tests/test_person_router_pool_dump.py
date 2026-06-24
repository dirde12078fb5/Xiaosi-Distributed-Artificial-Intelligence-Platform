# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""``/pool/dump`` 端点的路径白名单校验单测 (security boundary)。

抽成纯函数 ``_validate_pool_dump_path`` 让 security 边界可单测 (不引入 FastAPI
TestClient 这类此 codebase 暂无的测试基础设施)。覆盖:

  - SAFE_PREFIX 跟随 ``$MILOCO_HOME`` (核心契约)
  - SAFE_PREFIX 下合法目录 → 返回 realpath
  - SAFE_PREFIX 字面 (前缀本身) → 通过
  - 越界绝对路径 → ValueError
  - ``..`` 拼接越界 → ValueError
  - 相对路径 cwd 在 SAFE_PREFIX 外 → ValueError

函数 raise ``ValueError`` 而非 ``HTTPException``: 校验逻辑不耦合 web 层,handler
翻译异常,测试断 ``ValueError`` 才是 layering 真相。
"""

import os

import pytest
from miloco.person.router import _pool_dump_safe_prefix, _validate_pool_dump_path


@pytest.fixture(autouse=True)
def _miloco_home_in_tmp(tmp_path, monkeypatch):
    """每个用例独立 $MILOCO_HOME 锚到 pytest tmp_path, 避免污染真实 ~/.openclaw/miloco。

    _pool_dump_safe_prefix() 每次调用读 env(不缓存), 所以 fixture 设了 env 之后
    本测试文件里所有函数都能拿到 tmp_path 下的 SAFE_PREFIX。
    """
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    yield


def test_safe_prefix_follows_miloco_home(tmp_path):
    """核心契约: SAFE_PREFIX 派生自 $MILOCO_HOME, 不是硬编码 /tmp/。"""
    assert _pool_dump_safe_prefix() == str(tmp_path / "snapshots" / "tier_u")


def test_validate_safe_prefix_subpath(tmp_path):
    target = str(tmp_path / "snapshots" / "tier_u" / "snap1")
    real = _validate_pool_dump_path(target)
    safe_real = os.path.realpath(_pool_dump_safe_prefix())
    assert real.startswith(safe_real + os.sep)


def test_validate_safe_prefix_itself_passes(tmp_path):
    """SAFE_PREFIX 字面本身 (前缀目录) 也算合法 → 用于 dump_to 写到根。"""
    real = _validate_pool_dump_path(_pool_dump_safe_prefix())
    assert real == os.path.realpath(_pool_dump_safe_prefix())


def test_validate_absolute_outside_rejected(tmp_path):
    """落在 SAFE_PREFIX 外的绝对路径 → ValueError。

    新 SAFE_PREFIX 是 tmp_path/snapshots/tier_u, /tmp/foo 现在也属于"外"。
    """
    with pytest.raises(ValueError, match="必须在"):
        _validate_pool_dump_path("/etc/cron.d/evil")
    with pytest.raises(ValueError, match="必须在"):
        _validate_pool_dump_path("/tmp/foo")  # /tmp 在新设计里也越界


def test_validate_traversal_rejected(tmp_path):
    """``..`` 拼接想跳出 SAFE_PREFIX → ValueError。"""
    traversal = f"{_pool_dump_safe_prefix()}/../../etc/passwd"
    with pytest.raises(ValueError, match="必须在"):
        _validate_pool_dump_path(traversal)


def test_validate_relative_path_rejected(tmp_path, monkeypatch):
    """相对路径 → ValueError。

    显式 chdir 到 ``/`` 锚定 cwd 在 SAFE_PREFIX 外 —— 避免 cwd 恰好在
    SAFE_PREFIX 内时 realpath("foo") 解到 SAFE_PREFIX 内, 测试假绿。
    """
    monkeypatch.chdir("/")
    with pytest.raises(ValueError, match="必须在"):
        _validate_pool_dump_path("foo")


def test_validator_has_no_side_effects(tmp_path):
    """validator 是纯函数: SAFE_PREFIX 不存在也不会被建出 (留给 handler 落盘前调)。

    覆盖 dry-run 场景 — 未来 CLI 复用 validator 做路径检查时不该污染文件系统。
    """
    safe_dir = tmp_path / "snapshots" / "tier_u"
    assert not safe_dir.exists()
    # 调一次校验, 目录应仍不存在 (validator 不带副作用)
    _validate_pool_dump_path(str(safe_dir / "snap1"))
    assert not safe_dir.exists()
