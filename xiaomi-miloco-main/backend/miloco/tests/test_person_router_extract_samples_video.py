"""``/persons/{id}/extract`` 视频路径回归测试。

b0bb25f 的护栏: ``extractor._sample_video_frames`` 在 433b2c4 改签名为
``-> tuple[list[(int, ndarray)], float]``, 但 ``router.extract_samples`` 视频分支
漏拆元组 (``frames = _sample_video_frames(...)``), 下一行 ``for fi, frame in frames``
首轮就会拿 list 整个去解包成 2 变量, 视频附件注册接口直接挂。本测试用 3 个 N
(0/1/3) 都精确探到那行解包: 三种情况各自能在元组 vs 列表两层语义下触发不同的
ValueError, 任何一种 silently 回归都会先红。

设计:不引入 TestClient (对齐 ``test_person_router_samples_batch.py`` 的注释:
"现 codebase 不 mock 重链路");直接 await 路由协程, 用 monkeypatch 关掉
detector / reid_extractor / select_topk 这些跟本 bug 无关但会拖整条 ML 链路的
依赖, 让单测聚焦"路由层 ↔ extractor 层的元组契约"。
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
from miloco.perception.engine.identity import extractor as ext_mod
from miloco.perception.engine.identity import registration_filter as filter_mod
from miloco.perception.engine.identity.extractor import ScoredCandidate
from miloco.person import router as prouter

_PID = "33333333-3333-4333-8333-333333333333"


def _mk_candidate(frame_index: int) -> ScoredCandidate:
    body = np.zeros((16, 16, 3), dtype=np.uint8)
    face = np.zeros((16, 16, 3), dtype=np.uint8)
    return ScoredCandidate(
        body_crop=body, face_crop=face, score=1.0,
        bbox_xyxy=(0, 0, 16, 16), frame_index=frame_index, captured_at=float(frame_index),
        track_id=None, cluster_id=None, cam_id=None,
        detector_conf=0.9, sharpness=1.0,
    )


def _mk_media() -> SimpleNamespace:
    """UploadFile duck-type: 路由只读 .filename / .content_type 并 await .read()。
    .mp4 扩展 + video/* content-type 双重命中 is_video 分支判定。"""
    async def _read() -> bytes:
        return b"\x00fake-mp4-bytes\x00"
    return SimpleNamespace(filename="x.mp4", content_type="video/mp4", read=_read)


@pytest.fixture
def stubbed(monkeypatch):
    """共用桩:关掉 detector / reid / select_topk 等 ML 依赖,只让测试覆写
    _sample_video_frames + extract_from_image 两个被测函数。"""
    monkeypatch.setattr(
        prouter, "manager",
        SimpleNamespace(
            person_service=SimpleNamespace(exists=lambda pid: True),
            perception_service=SimpleNamespace(get_reid_extractor=lambda: None),
        ),
    )
    monkeypatch.setattr(prouter, "_load_detector", lambda: object())
    # select_topk 返回什么都行: 本测试不验"挑哪几张", 只验"接口不挂 + n_frames 等于
    # _sample_video_frames 返回的 list 长度"。
    monkeypatch.setattr(
        filter_mod, "select_topk",
        lambda candidates, **kw: SimpleNamespace(samples=list(candidates)),
    )
    return monkeypatch


async def test_video_three_frames_unpacks_tuple_correctly(stubbed):
    """3 帧 — 回归点核心场景: 漏拆 tuple 时 ``for fi, frame in (list_of_3, fps)``
    首轮 ``fi, frame = list_of_3`` 报 "too many values to unpack (expected 2)"。
    修复后 n_frames=3 + 候选完整平展。"""
    frames_returned = [(i, np.zeros((32, 32, 3), dtype=np.uint8)) for i in range(3)]
    stubbed.setattr(
        ext_mod, "_sample_video_frames",
        lambda path, max_frames: (frames_returned, 30.0),
    )
    stubbed.setattr(
        ext_mod, "extract_from_image",
        lambda image, **kw: [_mk_candidate(int(kw.get("captured_at", 0)))],
    )

    res = await prouter.extract_samples(
        person_id=_PID, media=_mk_media(), max_frames=12, current_user="t",
    )

    assert res.code == 0
    assert res.data["is_video"] is True
    # n_frames 等于 _sample_video_frames 返回 list 长度 (3) 而非 tuple 长度 (2):
    # 这条 assert 直接区分"正确拆出 list"和"误把 tuple 当 frames"两种状态。
    assert res.data["n_frames"] == 3
    # 3 candidate × (body + face) = 6 行 flat 平展
    assert len(res.data["candidates"]) == 6
    assert [c["type"] for c in res.data["candidates"]] == ["body", "face"] * 3


async def test_video_single_frame_unpacks_tuple_correctly(stubbed):
    """1 帧 — 漏拆 tuple 时 ``for fi, frame in (list_of_1, fps)`` 首轮
    ``fi, frame = list_of_1`` 报 "not enough values to unpack (expected 2, got 1)"。
    与 3 帧路径走的是同一行解包但触发的是另一种 ValueError, 一并护栏。"""
    frames_returned = [(0, np.zeros((32, 32, 3), dtype=np.uint8))]
    stubbed.setattr(
        ext_mod, "_sample_video_frames",
        lambda path, max_frames: (frames_returned, 30.0),
    )
    stubbed.setattr(
        ext_mod, "extract_from_image",
        lambda image, **kw: [_mk_candidate(0)],
    )

    res = await prouter.extract_samples(
        person_id=_PID, media=_mk_media(), max_frames=12, current_user="t",
    )

    assert res.code == 0
    assert res.data["n_frames"] == 1


async def test_video_zero_frames_early_returns(stubbed):
    """0 帧 (损坏视频 / 抽帧全失败) — 漏拆 tuple 时 ``if not frames`` 检查的是
    ``([], 30.0)`` 这个真值 tuple, 早退路径被跳过, 接着 ``for fi, frame in tuple``
    首轮 ``fi, frame = []`` 报 "not enough values to unpack (expected 2, got 0)"。
    修复后路由应走 "no decodable frames" 早退。"""
    stubbed.setattr(
        ext_mod, "_sample_video_frames",
        lambda path, max_frames: ([], 30.0),
    )
    # extract_from_image 不应被调到 (早退提前结束), 但留个无害桩防 import 报错。
    stubbed.setattr(ext_mod, "extract_from_image", lambda image, **kw: [])

    res = await prouter.extract_samples(
        person_id=_PID, media=_mk_media(), max_frames=12, current_user="t",
    )

    assert res.code == 0
    assert res.data["n_frames"] == 0
    assert res.data["candidates"] == []
    assert res.data["auto_selected"] == {"body": [], "face": []}
