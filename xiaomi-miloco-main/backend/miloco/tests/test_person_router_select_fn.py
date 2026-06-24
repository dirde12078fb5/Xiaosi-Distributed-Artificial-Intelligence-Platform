# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""``register/preview`` 的 select_fn 决策单测 (跨身份污染回归防护)。

``_should_use_frontal_seed`` 决定 create_pending 用 V_combined helper
(select_topk_with_frontal_seed) 还是 plain select_topk。**核心契约: 多人视频
(≥2 track) 绝不能用 V_combined** —— helper 在全量混合候选上跑 farthest-first,
stage 4 会就地把不同 track 的 face_crop 交叉改写 (A 的脸写进 B), 而 candidates
是共享对象 → multi_track commit 取到污染对象 → 跨身份污染 face gallery。

抽成纯函数让这条 security 边界可单测 (codebase 暂无 FastAPI TestClient 基础设施)。
此测试是防"未来有人去掉多 track gate 让 create_pending 重新跑 V_combined"的回归网。
"""

from miloco.person.router import _should_use_frontal_seed


def test_single_track_video_uses_frontal_seed():
    """单 track 视频 → V_combined (正是 helper 设计意图: 单人高质选样)。"""
    assert _should_use_frontal_seed(True, {1: ["c1", "c2"]}) is True


def test_multi_track_video_falls_back_to_plain():
    """≥2 track 视频 → plain select_topk (防混合候选跨 track 污染)。"""
    assert _should_use_frontal_seed(True, {1: ["c1"], 2: ["c2"]}) is False
    assert _should_use_frontal_seed(True, {1: ["c1"], 2: ["c2"], 3: ["c3"]}) is False


def test_non_video_never_uses_frontal_seed():
    """image / pool / batch 路径 (is_video=False) 一律 plain。"""
    assert _should_use_frontal_seed(False, None) is False
    assert _should_use_frontal_seed(False, {1: ["c1"]}) is False


def test_video_with_empty_tracks_treated_as_under_two():
    """is_video=True 但 video_per_track None / 空 dict → 0 track < 2 → True。

    (实际 0 track 时上游 candidates 为空, line ~695 已拦截不到 create_pending;
    本 case 仅固化 None 兜底不抛 TypeError。)
    """
    assert _should_use_frontal_seed(True, None) is True
    assert _should_use_frontal_seed(True, {}) is True
