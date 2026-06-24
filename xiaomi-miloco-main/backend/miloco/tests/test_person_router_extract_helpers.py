"""``extract_samples`` 内"算 auto_selected 下标 + 平展候选"两段纯逻辑单测。

reviewer 关心的"index 计算"——body / face 交错排版时哪个 flat 下标该入
``auto_selected``——是最容易在重构里 silently 弄错的部分。已从 ``extract_samples``
里拆出 ``_topup_selected_to_target`` + ``_flatten_candidates_with_auto`` 两个纯函数,
本测试不引入 detector / ReID / TestClient 这些"现 codebase 不 mock 的重 ML 链路"。
"""

from __future__ import annotations

import numpy as np
from miloco.perception.engine.identity.extractor import ScoredCandidate
from miloco.person.router import (
    _flatten_candidates_with_auto,
    _topup_selected_to_target,
)


def _mk(score: float = 1.0, with_face: bool = True, face_size_zero: bool = False) -> ScoredCandidate:
    body = np.zeros((16, 16, 3), dtype=np.uint8)
    if not with_face:
        face = None
    elif face_size_zero:
        face = np.zeros((0, 0, 3), dtype=np.uint8)
    else:
        face = np.zeros((16, 16, 3), dtype=np.uint8)
    return ScoredCandidate(
        body_crop=body, face_crop=face, score=score,
        bbox_xyxy=(0, 0, 16, 16), frame_index=0, captured_at=0.0,
        track_id=None, cluster_id=None, cam_id=None,
        detector_conf=0.9, sharpness=1.0,
    )


class TestTopupSelectedToTarget:
    def test_already_at_target_noop(self):
        scored = [_mk() for _ in range(5)]
        sel = {id(scored[0]), id(scored[1]), id(scored[2]), id(scored[3]), id(scored[4])}
        out = _topup_selected_to_target(scored, sel, target=5)
        assert out == sel

    def test_under_target_fills_by_order(self):
        scored = [_mk(score=1.0 - 0.1 * i) for i in range(5)]
        # select_topk 只挑出第 0 / 第 2 张
        sel = {id(scored[0]), id(scored[2])}
        out = _topup_selected_to_target(scored, sel, target=5)
        # 按 scored 顺序补:加 scored[1] scored[3] scored[4]
        assert out == {id(c) for c in scored}

    def test_short_of_target_caps_at_available(self):
        scored = [_mk() for _ in range(3)]
        sel: set[int] = set()
        out = _topup_selected_to_target(scored, sel, target=5)
        # 只有 3 个候选,target=5 也只能补 3 个
        assert out == {id(c) for c in scored}

    def test_does_not_mutate_input(self):
        scored = [_mk() for _ in range(3)]
        sel = {id(scored[0])}
        sel_snapshot = set(sel)
        _topup_selected_to_target(scored, sel, target=5)
        assert sel == sel_snapshot


class TestFlattenCandidatesWithAuto:
    def test_body_and_face_interleave_with_correct_indices(self):
        # 3 个候选,都有 face。flat list 应为 [body0, face0, body1, face1, body2, face2]
        scored = [_mk() for _ in range(3)]
        selected = {id(scored[0]), id(scored[2])}
        cands, auto_b, auto_f = _flatten_candidates_with_auto(scored, selected)
        # 6 行 candidate,顺序交错
        assert [c["type"] for c in cands] == ["body", "face", "body", "face", "body", "face"]
        # auto_body 指 flat[0] 和 flat[4]
        assert auto_b == [0, 4]
        # auto_face 跟随,指 flat[1] 和 flat[5]
        assert auto_f == [1, 5]

    def test_face_none_skipped(self):
        # 第二个候选 face_crop=None → flat 只有 1 行 body
        scored = [_mk(), _mk(with_face=False), _mk()]
        selected = {id(c) for c in scored}
        cands, auto_b, auto_f = _flatten_candidates_with_auto(scored, selected)
        assert [c["type"] for c in cands] == ["body", "face", "body", "body", "face"]
        # body 选中下标:0(候选 0)、2(候选 1,无 face)、3(候选 2)
        assert auto_b == [0, 2, 3]
        # face 选中下标:1、4(只有候选 0 / 2 有 face)
        assert auto_f == [1, 4]

    def test_face_zero_size_skipped(self):
        # face_crop 不为 None 但 size==0 也应跳过
        scored = [_mk(face_size_zero=True)]
        cands, auto_b, auto_f = _flatten_candidates_with_auto(scored, {id(scored[0])})
        assert [c["type"] for c in cands] == ["body"]
        assert auto_b == [0]
        assert auto_f == []

    def test_unselected_face_not_in_auto(self):
        # 候选有 face,但未入 selected → auto_face 不包含其下标
        scored = [_mk()]
        cands, auto_b, auto_f = _flatten_candidates_with_auto(scored, set())
        assert len(cands) == 2  # body + face 都吐
        assert auto_b == []
        assert auto_f == []
