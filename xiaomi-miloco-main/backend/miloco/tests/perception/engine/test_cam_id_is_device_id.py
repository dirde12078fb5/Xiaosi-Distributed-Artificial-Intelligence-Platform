"""Tests for cam_id == device_id (v2 重构).

之前 TierU entry.cam_id 用 scope_label (``"<room>-dev<idx>"``) 格式, 跟前端 device
list 拿到的米家 device_id 命名空间不一致, 导致 pool fetch --cam 用 device_id 永远
0 候选。v2 重构把 cam_id 统一改成米家 device_id, 命名空间打通。

参 ``backend/.../perception/engine/identity/tier_u.py:cam_id_from_device_id``。
"""

from miloco.perception.engine.identity.tier_u import cam_id_from_device_id


def test_cam_id_from_device_id_identity():
    """非空 device_id 直接返回 (placeholder identity 行为)。"""
    assert cam_id_from_device_id("1178866901") == "1178866901"
    assert cam_id_from_device_id("MI_C700_AABBCC") == "MI_C700_AABBCC"
    # 即使传 scope_label 格式也按 identity 返回 (v2 之后这种用法是 deprecated, 但行为不崩)
    assert cam_id_from_device_id("客厅-dev0") == "客厅-dev0"


def test_cam_id_from_device_id_empty_fallback():
    """空字符串 fallback "default" — 兼容单测 / scope_label="" 老路径。"""
    assert cam_id_from_device_id("") == "default"


def test_identity_engine_cam_id_uses_device_id():
    """IdentityEngine.cam_id 必须等于 device_id 入参 (v2 重构核心保证)。

    这是 push_crop 路径 CropEntry.cam_id 的源头, 与 PerceptionEngine
    _deep_sort_trackers dict key 必须严格同源, 否则 provider 反查 emb 失败。
    """
    import tempfile

    from miloco.perception.engine.config import IdentityEngineConfig
    from miloco.perception.engine.identity.engine import build_identity_engine
    from miloco.perception.engine.identity.library import IdentityLibrary

    # 用 in-memory library 跑(临时目录免污染)
    with tempfile.TemporaryDirectory() as tmpdir:
        lib = IdentityLibrary(tmpdir)
        cfg = IdentityEngineConfig()
        eng = build_identity_engine(
            cfg,
            library=lib,
            scope_label="客厅-dev0",   # 渲染用, 不影响 cam_id
            device_id="1178866901",   # 真值 — cam_id 必须等于这个
        )
        # 核心断言: cam_id == device_id (不是 scope_label)
        assert eng.cam_id == "1178866901"
        # 渲染字段保留 scope_label
        assert eng.scope_label == "客厅-dev0"


def test_identity_engine_empty_device_id_fallback_default():
    """device_id 空时 cam_id 走 fallback "default" (兼容老入口 / 单测)。"""
    import tempfile

    from miloco.perception.engine.config import IdentityEngineConfig
    from miloco.perception.engine.identity.engine import build_identity_engine
    from miloco.perception.engine.identity.library import IdentityLibrary

    with tempfile.TemporaryDirectory() as tmpdir:
        lib = IdentityLibrary(tmpdir)
        cfg = IdentityEngineConfig()
        eng = build_identity_engine(cfg, library=lib, scope_label="客厅-dev0")
        # device_id 未传 = "" → cam_id fallback
        assert eng.cam_id == "default"
