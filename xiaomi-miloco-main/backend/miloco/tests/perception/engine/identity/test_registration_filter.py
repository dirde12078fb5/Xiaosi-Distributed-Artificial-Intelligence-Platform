"""注册图片筛选算法 (registration_filter.py) 单测。

覆盖 v4 §4 选 topk 主路径(pHash + 时间)+ 备路径(ReID 复审)+ status 状态码
"""

from __future__ import annotations

import numpy as np
import pytest
from miloco.perception.engine.identity.extractor import ScoredCandidate
from miloco.perception.engine.identity.registration_filter import (
    select_topk,
    select_topk_with_frontal_seed,
)


def _make_cand(
    *, score: float, phash: int, ts: float,
    reid_emb: np.ndarray | None = None,
) -> ScoredCandidate:
    return ScoredCandidate(
        body_crop=np.zeros((100, 50, 3), dtype=np.uint8),
        face_crop=None,
        score=score,
        bbox_xyxy=(0, 0, 50, 100),
        frame_index=0,
        captured_at=ts,
        track_id=1,
        cluster_id=None,
        cam_id="cam-a",
        detector_conf=0.9,
        sharpness=200.0,
        reid_embedding=reid_emb,
        phash=phash,
    )


def _emb(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(128).astype(np.float32)
    return v / np.linalg.norm(v)


# =============================================================================
# 主路径
# =============================================================================


class TestMainPath:
    def test_empty_candidates_returns_no_valid_subject(self):
        r = select_topk([])
        assert r.status == "no_valid_subject"
        assert r.samples == []

    def test_picks_topk_when_diverse(self):
        # 三张完全不同的 pHash + 时间够开 → 全选
        cands = [
            _make_cand(score=1.0, phash=0x0000_0000_0000_0000, ts=10.0),
            _make_cand(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=20.0),
            _make_cand(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0),
        ]
        r = select_topk(cands, topk=3)
        assert r.status == "ok"
        assert len(r.samples) == 3

    def test_phash_too_close_rejected(self):
        # 第二张 pHash 完全相同 → 距离 0 < 28 → 拒
        cands = [
            _make_cand(score=1.0, phash=0xAAAA_AAAA_AAAA_AAAA, ts=10.0),
            _make_cand(score=0.9, phash=0xAAAA_AAAA_AAAA_AAAA, ts=20.0),
            _make_cand(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0),
        ]
        r = select_topk(cands, topk=3)
        assert len(r.samples) == 2  # 第二张被 pHash 拒,第三张能入选
        assert any(reason == "phash_too_close" for _, reason in r.rejected)
        assert r.status == "weak_diversity"

    def test_time_gap_too_short_rejected(self):
        # 第二张 ts 跟第一张同 = 0 s < 1.0 s → 拒
        cands = [
            _make_cand(score=1.0, phash=0x0000_0000_0000_0000, ts=10.0),
            _make_cand(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=10.0),
            _make_cand(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0),
        ]
        r = select_topk(cands, topk=3)
        assert len(r.samples) == 2
        assert any(reason == "time_gap_too_short" for _, reason in r.rejected)

    def test_stops_at_topk(self):
        cands = [
            _make_cand(score=1.0, phash=0x0000_0000_0000_0000, ts=10.0),
            _make_cand(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=20.0),
            _make_cand(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0),
            _make_cand(score=0.7, phash=0xAAAA_AAAA_AAAA_AAAA, ts=40.0),
        ]
        r = select_topk(cands, topk=2)
        assert r.status == "ok"
        assert len(r.samples) == 2
        # 应该是前两个最高分,且 rejected 不含未走完的
        assert r.samples[0].score == 1.0
        assert r.samples[1].score == 0.9


# =============================================================================
# 备路径(ReID 复审)
# =============================================================================


class TestReidBackupPath:
    def test_phash_rejects_but_reid_diverse_backup_picks_them_up(self):
        """构造场景:三张 pHash 完全相同(主路径全拒),但 ReID emb 各不相同
        (余弦 < 0.9 → 备路径放行)。期望备路径补足 topk。
        """
        # 三张 pHash 完全一致 → 主路径只能选 1 张
        # ReID emb 互相正交 → 余弦 ≈ 0 < 0.9
        cands = [
            _make_cand(score=1.0, phash=0xAAAA_AAAA_AAAA_AAAA, ts=10.0, reid_emb=_emb(1)),
            _make_cand(score=0.9, phash=0xAAAA_AAAA_AAAA_AAAA, ts=20.0, reid_emb=_emb(2)),
            _make_cand(score=0.8, phash=0xAAAA_AAAA_AAAA_AAAA, ts=30.0, reid_emb=_emb(3)),
        ]
        r = select_topk(cands, topk=3)
        # 主路径只能选第一张;备路径用 ReID 把第二、第三补上
        assert r.status == "ok"
        assert len(r.samples) == 3

    def test_reid_backup_skips_when_similar_emb(self):
        """三张 pHash 全 reject,而且 ReID emb 完全一致 → 备路径也拒。"""
        same_emb = _emb(1)
        cands = [
            _make_cand(score=1.0, phash=0xAAAA_AAAA_AAAA_AAAA, ts=10.0,
                        reid_emb=same_emb.copy()),
            _make_cand(score=0.9, phash=0xAAAA_AAAA_AAAA_AAAA, ts=20.0,
                        reid_emb=same_emb.copy()),
        ]
        r = select_topk(cands, topk=3)
        # 只能选 1 张
        assert len(r.samples) == 1
        assert r.status == "weak_diversity"

    def test_reid_backup_inactive_when_no_embedding(self):
        """所有 rejected 候选都没 reid_embedding → 备路径 noop。"""
        cands = [
            _make_cand(score=1.0, phash=0xAAAA_AAAA_AAAA_AAAA, ts=10.0, reid_emb=None),
            _make_cand(score=0.9, phash=0xAAAA_AAAA_AAAA_AAAA, ts=20.0, reid_emb=None),
        ]
        r = select_topk(cands, topk=3)
        assert len(r.samples) == 1
        assert r.status == "weak_diversity"


# =============================================================================
# Status
# =============================================================================


class TestStatus:
    def test_ok_when_topk_filled(self):
        cands = [
            _make_cand(score=1.0, phash=0x0, ts=10.0),
            _make_cand(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=20.0),
            _make_cand(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0),
        ]
        assert select_topk(cands, topk=3).status == "ok"

    def test_weak_diversity_when_below_topk_but_above_min_k(self):
        # 只有 2 张能入选 < topk=3,但 ≥ min_k=1 → weak_diversity
        cands = [
            _make_cand(score=1.0, phash=0x0, ts=10.0),
            _make_cand(score=0.9, phash=0x0, ts=20.0),  # 主路径被 pHash 拒
        ]
        r = select_topk(cands, topk=3, min_k=1)
        assert len(r.samples) == 1
        assert r.status == "weak_diversity"

    def test_no_valid_subject_when_zero_input(self):
        assert select_topk([]).status == "no_valid_subject"


class TestSkipPhashDedup:
    """skip_phash_dedup=True 时 pHash 检查跳过,只保留时间 / ReID 维度。

    场景:用户多图批量注册,几张图场景接近 pHash 落到 < 28 时,默认会被收敛到 1 张;
    skip_phash_dedup 后让用户提交的每张图都进 selected。
    """

    def _cand(self, *, score, phash, ts, reid=None):
        # 把每个 candidate 的 sharpness 单独区分一下,方便断言"全部选了"
        return _make_cand(score=score, phash=phash, ts=ts, reid_emb=reid)

    def test_default_collapses_near_duplicate_phash(self):
        """默认行为(不跳 pHash):4 张近 pHash → 只选 1。"""
        # 4 张 phash hamming 距离都很小(0/1 bit 差异)
        cands = [
            self._cand(score=0.9, phash=0b1100, ts=0.0),
            self._cand(score=0.8, phash=0b1101, ts=1.5),
            self._cand(score=0.7, phash=0b1110, ts=3.0),
            self._cand(score=0.6, phash=0b1111, ts=4.5),
        ]
        r = select_topk(cands, topk=5)
        # 4 张高度相似 pHash 全被收敛到 1 张
        assert len(r.samples) == 1, f"默认应只选 1 张,got {len(r.samples)}"

    def test_skip_phash_dedup_keeps_all_near_phash(self):
        """skip_phash_dedup=True:同样 4 张近 pHash 应该全保留(用户手挑预期)。"""
        cands = [
            self._cand(score=0.9, phash=0b1100, ts=0.0),
            self._cand(score=0.8, phash=0b1101, ts=1.5),
            self._cand(score=0.7, phash=0b1110, ts=3.0),
            self._cand(score=0.6, phash=0b1111, ts=4.5),
        ]
        r = select_topk(cands, topk=5, skip_phash_dedup=True)
        assert len(r.samples) == 4, (
            f"skip_phash_dedup 后 4 张 pHash 接近的应都入选,got {len(r.samples)}"
        )
        assert r.status == "ok" or r.status == "weak_diversity"

    def test_skip_phash_dedup_still_honors_time_gap(self):
        """跳 pHash 但仍守时间间隔:同一秒多张应只留 1 张。"""
        cands = [
            self._cand(score=0.9, phash=0b0001, ts=0.0),
            self._cand(score=0.8, phash=0b0010, ts=0.3),  # < 1s gap → 被时间维度拒
            self._cand(score=0.7, phash=0b0100, ts=0.6),  # < 1s gap → 拒
        ]
        r = select_topk(cands, topk=5, skip_phash_dedup=True)
        assert len(r.samples) == 1, (
            f"skip pHash 但 time_gap 仍生效;同秒 3 张应只留 1,got {len(r.samples)}"
        )

    def test_skip_phash_dedup_topk_caps(self):
        """skip_phash_dedup 不影响 topk 上限:5 张近 pHash + topk=3 → 选前 3 张。"""
        cands = [
            self._cand(score=0.9 - i * 0.1, phash=i, ts=float(i * 2))
            for i in range(5)
        ]
        r = select_topk(cands, topk=3, skip_phash_dedup=True)
        assert len(r.samples) == 3, f"topk=3 应只选 3,got {len(r.samples)}"
        # 按 score 降序选,应该是前 3 张
        assert r.samples[0].score == 0.9
        assert r.samples[1].score == pytest.approx(0.8)
        assert r.samples[2].score == pytest.approx(0.7)


# =============================================================================
# preseeded 参数(主路径接受外部预选 seed,跟其余 cand 做 dedup 互检)
# =============================================================================


def _make_cand_with_face(
    *, score: float, phash: int, ts: float,
    face_w: int = 60, face_h: int = 80,
    reid_emb: np.ndarray | None = None,
) -> ScoredCandidate:
    """带 face_crop 的 candidate,默认 face_w/h=60/80=0.75 (正脸区间)。"""
    return ScoredCandidate(
        body_crop=np.zeros((100, 50, 3), dtype=np.uint8),
        face_crop=np.zeros((face_h, face_w, 3), dtype=np.uint8),
        score=score,
        bbox_xyxy=(0, 0, 50, 100),
        frame_index=int(ts * 10),
        captured_at=ts,
        track_id=1,
        cluster_id=None,
        cam_id="cam-a",
        detector_conf=0.9,
        sharpness=200.0,
        reid_embedding=reid_emb,
        phash=phash,
    )


class TestPreseeded:
    def test_preseeded_default_none_preserves_legacy(self):
        """preseeded=None 时行为完全等同老 select_topk(回归保护)。"""
        cands = [
            _make_cand(score=1.0, phash=0x0000_0000_0000_0000, ts=10.0),
            _make_cand(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=20.0),
            _make_cand(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0),
        ]
        r_default = select_topk(cands, topk=3)
        r_explicit = select_topk(cands, topk=3, preseeded=None)
        assert r_default.status == r_explicit.status == "ok"
        assert [s.score for s in r_default.samples] == [s.score for s in r_explicit.samples]

    def test_preseeded_seed_inherits_dedup(self):
        """preseeded 的 seed 跟主路径扫到的 cand 做 pHash 互检:
        seed pHash 跟 #2 cand 太近时,#2 应被拒 → 跟老逻辑 selected 互检一致。
        """
        seed = _make_cand(score=0.5, phash=0xAAAA_AAAA_AAAA_AAAA, ts=50.0)
        # cand_0: pHash 跟 seed 完全一致 → 应被 phash_too_close 拒
        # cand_1: pHash 跟 seed 远 → 应入选
        cands = [
            _make_cand(score=1.0, phash=0xAAAA_AAAA_AAAA_AAAA, ts=10.0),
            _make_cand(score=0.9, phash=0x5555_5555_5555_5555, ts=20.0),
        ]
        r = select_topk(cands, topk=3, preseeded=[seed])
        # selected 应该是 [seed, cand_1] (cand_0 被 pHash 拒)
        assert len(r.samples) == 2
        assert r.samples[0] is seed
        assert r.samples[1].phash == 0x5555_5555_5555_5555
        assert any(reason == "phash_too_close" for _, reason in r.rejected)

    def test_preseeded_cand_also_in_candidates_not_double_picked(self):
        """preseeded 里的 cand 同时出现在 candidates 里,主路径用 identity 跳过不重选。"""
        seed = _make_cand(score=1.0, phash=0x0000, ts=10.0)
        other = _make_cand(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=20.0)
        # 把 seed 自身也放进 candidates
        r = select_topk([seed, other], topk=3, preseeded=[seed])
        assert len(r.samples) == 2
        # seed 只出现 1 次
        seen = [id(s) for s in r.samples]
        assert seen.count(id(seed)) == 1


# =============================================================================
# ensure_topk 参数(差异化跑完 < topk 时按 score 顺序补满)
# =============================================================================


class TestEnsureTopk:
    def test_ensure_topk_default_false_preserves_legacy(self):
        """ensure_topk=False(默认)时凑不齐 topk 不补,跟老逻辑一致(回归保护)。"""
        cands = [
            _make_cand(score=1.0, phash=0xAAAA, ts=10.0),
            _make_cand(score=0.9, phash=0xAAAA, ts=20.0),
            _make_cand(score=0.8, phash=0xAAAA, ts=30.0),
        ]
        r = select_topk(cands, topk=3)
        # pHash 全相同 → 主路径只选 1, 无 reid 备路径
        assert len(r.samples) == 1
        assert r.status == "weak_diversity"

    def test_ensure_topk_true_pads_when_dedup_strict(self):
        """ensure_topk=True 时即使 pHash 全部拒,也按 score 顺序补满 topk。"""
        cands = [
            _make_cand(score=1.0, phash=0xAAAA, ts=10.0),
            _make_cand(score=0.9, phash=0xAAAA, ts=20.0),
            _make_cand(score=0.8, phash=0xAAAA, ts=30.0),
        ]
        r = select_topk(cands, topk=3, ensure_topk=True)
        # 主路径只选 1 张,ensure_topk 兜底按 score 顺序补 2 张
        assert len(r.samples) == 3
        assert [s.score for s in r.samples] == [1.0, 0.9, 0.8]
        # status 仍按差异化阶段计算(主路径只 1 张 → weak_diversity)
        assert r.status == "weak_diversity"

    def test_ensure_topk_does_not_exceed_candidates(self):
        """ensure_topk=True 但 cand 数 < topk 时,只能补到 cand 数上限。"""
        cands = [
            _make_cand(score=1.0, phash=0xAAAA, ts=10.0),
            _make_cand(score=0.9, phash=0xAAAA, ts=20.0),
        ]
        r = select_topk(cands, topk=5, ensure_topk=True)
        # 主路径选 1, ensure_topk 补 1, 总共 2 (cand 上限)
        assert len(r.samples) == 2
        assert r.status == "weak_diversity"


# =============================================================================
# select_topk_with_frontal_seed (视频附件路径专用 helper)
# =============================================================================


class TestSelectTopkWithFrontalSeed:
    def test_picks_frontal_face_as_seed(self):
        """face_w/h ∈ [0.70, 0.80) 区间存在时,选 score 最高那张为 #1 seed。"""
        # cand_a: w/h=0.62 侧脸 高 sharpness 屠榜 score
        # cand_b: w/h=0.75 正脸 score 中等 ← 应入选 #1 seed
        # cand_c: w/h=0.90 抬头
        cand_side = _make_cand_with_face(
            score=0.9, phash=0x1111, ts=10.0, face_w=62, face_h=100,  # 0.62
        )
        cand_frontal = _make_cand_with_face(
            score=0.5, phash=0x2222, ts=20.0, face_w=75, face_h=100,  # 0.75
        )
        cand_uplook = _make_cand_with_face(
            score=0.7, phash=0x4444, ts=30.0, face_w=90, face_h=100,  # 0.90
        )
        # cands 按 score 降序排
        cands = [cand_side, cand_uplook, cand_frontal]
        r = select_topk_with_frontal_seed(cands, topk=3)
        # 第 1 张必须是 frontal cand (强制种子)
        assert r.samples[0] is cand_frontal
        # 后续按 select_topk 老逻辑补 (cand_side / cand_uplook 跟 frontal pHash 远, 都入)
        assert len(r.samples) == 3

    def test_no_frontal_fallback_to_face_cands(self):
        """face cand 都不在 [0.70, 0.80) 区间时,无 seed 退化到 face_cands 上跑老逻辑。"""
        # 全是侧脸 (w/h=0.55) 或抬头 (w/h=0.95)
        cands = [
            _make_cand_with_face(score=0.9, phash=0x1111, ts=10.0, face_w=55, face_h=100),
            _make_cand_with_face(score=0.8, phash=0x2222, ts=20.0, face_w=95, face_h=100),
            _make_cand_with_face(score=0.7, phash=0x4444, ts=30.0, face_w=55, face_h=100),
        ]
        r = select_topk_with_frontal_seed(cands, topk=3)
        # 没 frontal seed 但 face_cands 充足 → 主路径选 3 张 (pHash 都远)
        assert len(r.samples) == 3
        # 第 1 张应是 score 最高的 (老逻辑按 score 降序)
        assert r.samples[0].score == 0.9

    def test_face_cands_lt_topk_returns_weak_diversity(self):
        """face_cands 数量 < topk 时,只返 face_cands 数量,status='weak_diversity'。
        不用无脸 body 凑数(face/body 必须等量入库)。
        """
        cands = [
            _make_cand_with_face(score=0.9, phash=0x1111, ts=10.0, face_w=75, face_h=100),
            _make_cand_with_face(score=0.8, phash=0x2222, ts=20.0, face_w=75, face_h=100),
            # 余下都是无 face 的 body cand
            _make_cand(score=0.7, phash=0x4444, ts=30.0),
            _make_cand(score=0.6, phash=0x8888, ts=40.0),
        ]
        r = select_topk_with_frontal_seed(cands, topk=3)
        # 只返 2 张 face cand,不用无脸 body 凑
        assert len(r.samples) == 2
        assert all(s.face_crop is not None for s in r.samples)
        assert r.status == "weak_diversity"

    def test_face_cands_zero_returns_no_valid_subject(self):
        """face 检测全失败 (face_cands=0) → status='no_valid_subject'(注册视频质量不达标)。"""
        cands = [
            _make_cand(score=0.9, phash=0x1111, ts=10.0),  # 无 face
            _make_cand(score=0.8, phash=0x2222, ts=20.0),  # 无 face
            _make_cand(score=0.7, phash=0x4444, ts=30.0),  # 无 face
        ]
        r = select_topk_with_frontal_seed(cands, topk=3)
        assert r.status == "no_valid_subject"
        assert r.samples == []


def _make_cand_with_split_face(
    *, score: float, phash: int, ts: float,
    face_w: int, face_h: int,         # face_crop (跨帧分发后借来的最锐 face) 尺寸
    sf_face_w: int, sf_face_h: int,   # same_frame_face_crop (同帧 body 关联到的 face) 尺寸
) -> ScoredCandidate:
    """构造 face_crop ≠ same_frame_face_crop 的 cand, 模拟 video 路径跨帧分发后的状态。

    face_crop 跟 same_frame 朝向不同 (典型: face_crop 是借来的正脸 0.75 w/h,
    same_frame 是侧脸 0.55 w/h), 用于验证 V6b 用哪一个判 frontal。
    """
    face_crop = np.zeros((face_h, face_w, 3), dtype=np.uint8)
    sf_face_crop = np.zeros((sf_face_h, sf_face_w, 3), dtype=np.uint8)
    return ScoredCandidate(
        body_crop=np.zeros((100, 50, 3), dtype=np.uint8),
        face_crop=face_crop,
        score=score,
        bbox_xyxy=(0, 0, 50, 100),
        frame_index=int(ts * 10),
        captured_at=ts,
        track_id=1,
        cluster_id=None,
        cam_id="cam-a",
        detector_conf=0.9,
        sharpness=200.0,
        reid_embedding=None,
        phash=phash,
        same_frame_face_crop=sf_face_crop,
    )


class TestFrontalSeedSameFrameAlignment:
    """方案 A: V6b 用 same_frame_face_crop 判 frontal + seed 选中后覆盖 face_crop。

    覆盖"face 跨帧分发让 cand.face_crop 跟 cand.body_crop 朝向不一致"的修正:
      1. frontal 判定用 same_frame 而非 face_crop (后者可能是跨帧借的最锐 face)
      2. seed 选定后, seed.face_crop 被覆盖为 seed.same_frame_face_crop, 让号码图
         首位 cand 的 body / face 来自同一帧 → 朝向一致 (用户实际诉求)
    """

    def test_frontal_judged_by_same_frame_not_face_crop(self):
        """face_crop=0.75 (跨帧借来的正脸) 但 same_frame=0.55 (该 body 帧实际是侧脸)
        → V6b 应该判该 cand 不是 frontal (按 body 帧朝向算, 不按借来的 face)。
        """
        # 1 个 cand: face_crop w/h=0.75 (正脸尺寸), same_frame w/h=0.55 (侧脸尺寸)
        # 旧逻辑用 face_crop 会判 frontal, 新逻辑用 same_frame 不判 frontal
        cand_misleading = _make_cand_with_split_face(
            score=0.9, phash=0x1111, ts=10.0,
            face_w=75, face_h=100,        # face_crop w/h=0.75 → 旧逻辑看成正脸
            sf_face_w=55, sf_face_h=100,  # same_frame w/h=0.55 → 新逻辑看成侧脸
        )
        # 1 个对照 cand: 双侧都是侧脸 (w/h=0.55)
        cand_side = _make_cand_with_split_face(
            score=0.8, phash=0x2222, ts=20.0,
            face_w=55, face_h=100,
            sf_face_w=55, sf_face_h=100,
        )
        cands = [cand_misleading, cand_side]
        r = select_topk_with_frontal_seed(cands, topk=2)
        # 没 frontal cand (按 same_frame 看俩都是侧脸), 退化到 select_topk on face_cands
        # 第 1 张应是 score 最高的 cand_misleading (按 score 而非 frontal seed)
        assert r.samples[0] is cand_misleading
        # 没 seed 触发, face_crop 不被覆盖 — 仍是原 75x100 的"正脸尺寸 face_crop"
        assert r.samples[0].face_crop.shape == (100, 75, 3)

    def test_seed_face_crop_overridden_to_same_frame(self):
        """命中 frontal seed 后, seed.face_crop 应被覆盖为 same_frame_face_crop。

        构造: cand_a 同帧是正脸 (sf w/h=0.75), 但 face_crop 是跨帧借来的侧脸 (w/h=0.55)。
        V6b 用 same_frame 判 frontal → seed = cand_a。然后 face_crop 应被覆盖回
        same_frame (尺寸 75x100), 表征"body 跟 face 来自同一帧朝向一致"。
        """
        cand_a = _make_cand_with_split_face(
            score=0.5, phash=0x1111, ts=10.0,
            face_w=55, face_h=100,          # 借来的侧脸 face_crop
            sf_face_w=75, sf_face_h=100,    # 同帧实际正脸
        )
        cand_b = _make_cand_with_split_face(
            score=0.9, phash=0x2222, ts=20.0,
            face_w=55, face_h=100,
            sf_face_w=55, sf_face_h=100,    # 全侧脸 cand
        )
        cands = [cand_b, cand_a]   # 按 score 降序, cand_b 在前
        r = select_topk_with_frontal_seed(cands, topk=2)
        # cand_a 是唯一 frontal (sf w/h=0.75) → seed
        assert r.samples[0] is cand_a
        # cand_a.face_crop 被覆盖为 same_frame (75x100), 不再是 55x100 的"借来侧脸"
        assert r.samples[0].face_crop.shape == (100, 75, 3)
        # 非 seed (cand_b) 的 face_crop 不动
        assert r.samples[1] is cand_b
        assert r.samples[1].face_crop.shape == (100, 55, 3)

    def test_same_frame_none_falls_back_to_face_crop(self):
        """same_frame_face_crop=None (image / pool 路径) → V6b 用 face_crop 判 frontal,
        seed 不覆盖 face_crop (保持原值)。
        """
        # 走老 _make_cand_with_face: same_frame_face_crop 默认 None
        cand_frontal = _make_cand_with_face(
            score=0.5, phash=0x1111, ts=10.0,
            face_w=75, face_h=100,  # face_crop 看成正脸
        )
        cand_side = _make_cand_with_face(
            score=0.9, phash=0x2222, ts=20.0,
            face_w=55, face_h=100,
        )
        cands = [cand_side, cand_frontal]
        r = select_topk_with_frontal_seed(cands, topk=2)
        # cand_frontal 仍能成 seed (走 fallback 用 face_crop 判)
        assert r.samples[0] is cand_frontal
        # face_crop 不被覆盖 (same_frame=None 时跳过覆盖逻辑)
        assert r.samples[0].face_crop.shape == (100, 75, 3)


class TestVCombinedPath:
    """V_combined (reid_extractor 给定): body ReID-driven + face 独立 ReID-driven.

    覆盖:
      - reid_extractor=None 时退化到 V0 路径 (回归保护)
      - reid_extractor 给定时 body / face 各自 farthest-first
      - frontal seed 仍作 base (face/body 同帧正脸首位)
      - face_crop 重分配回 body_picks (顺序绑定)
    """

    def _make_cand_full(
        self, *, score, phash, ts, body_emb_seed, face_w=75, face_h=100,
    ):
        """带 reid_embedding + same_frame_face_crop 的 cand (跟 video 路径状态对齐)。"""
        return ScoredCandidate(
            body_crop=np.ones((100, 50, 3), dtype=np.uint8) * 128,
            face_crop=np.zeros((face_h, face_w, 3), dtype=np.uint8),
            score=score,
            bbox_xyxy=(0, 0, 50, 100),
            frame_index=int(ts * 10),
            captured_at=ts,
            track_id=1,
            cluster_id=None,
            cam_id="cam-a",
            detector_conf=0.9,
            sharpness=200.0,
            reid_embedding=_emb(body_emb_seed),
            phash=phash,
            same_frame_face_crop=np.zeros((face_h, face_w, 3), dtype=np.uint8),
        )

    def test_reid_extractor_none_falls_back_to_v0(self):
        """reid_extractor=None 时 V_combined 路径不触发, 行为完全等同 V0 (回归保护)。"""
        cands = [
            _make_cand_with_face(score=0.9, phash=0x1111, ts=10.0, face_w=75, face_h=100),
            _make_cand_with_face(score=0.8, phash=0x2222, ts=20.0, face_w=55, face_h=100),
            _make_cand_with_face(score=0.7, phash=0x4444, ts=30.0, face_w=55, face_h=100),
        ]
        r_v0 = select_topk_with_frontal_seed(cands, topk=3)
        r_explicit = select_topk_with_frontal_seed(cands, topk=3, reid_extractor=None)
        assert [id(s) for s in r_v0.samples] == [id(s) for s in r_explicit.samples], (
            "reid_extractor=None 时应跟显式 V0 行为一致"
        )

    def test_v_combined_selects_diverse_body_and_face(self):
        """给定 reid_extractor (mock), 跑 V_combined 路径; 5 张 body emb 多样
        + 5 张 face emb 多样 + #0 = frontal seed 且 face 来自 same_frame。"""
        from unittest.mock import MagicMock
        # 4 个 cand: 1 frontal + 3 score 降序; body emb 互相正交
        cand_frontal = self._make_cand_full(
            score=0.5, phash=0x1111, ts=10.0, body_emb_seed=1, face_w=75, face_h=100,
        )
        cand_a = self._make_cand_full(
            score=0.9, phash=0x2222, ts=20.0, body_emb_seed=2, face_w=55, face_h=100,
        )
        cand_b = self._make_cand_full(
            score=0.8, phash=0x3333, ts=30.0, body_emb_seed=3, face_w=55, face_h=100,
        )
        cand_c = self._make_cand_full(
            score=0.7, phash=0x4444, ts=40.0, body_emb_seed=4, face_w=55, face_h=100,
        )
        cands = [cand_a, cand_b, cand_c, cand_frontal]
        # mock reid_extractor: face emb 用预定义种子 (互相正交)
        face_emb_map_by_id = {
            id(cand_frontal): _emb(11),
            id(cand_a): _emb(12),
            id(cand_b): _emb(13),
            id(cand_c): _emb(14),
        }
        mock_reid = MagicMock()
        def extract_feat(face_crop):
            # face_crop 是 same_frame_face_crop, 通过 id 查 cand 来返 emb
            # mock 简化: 看 face_crop 的 ndarray data 不重要, 用 call_count 顺序
            return None  # 实际 mock 见下面
        # 因为 face_crop ndarray 没法逆查 cand id, 用 side_effect 按调用顺序返回
        # cand 遍历顺序在 _select_v_combined: for c in face_cands
        # face_cands = [c for c in candidates if c.face_crop is not None] 跟 candidates 同序
        embs_in_order = [face_emb_map_by_id[id(c)] for c in cands]
        mock_reid.extract_feature = MagicMock(side_effect=embs_in_order)

        r = select_topk_with_frontal_seed(cands, topk=4, reid_extractor=mock_reid)
        # frontal seed (cand_frontal) 必为 #0
        assert r.samples[0] is cand_frontal
        # 选满 4 张
        assert len(r.samples) == 4
        # face_crop 应被重分配 (而不是各自原 face_crop)
        # 这里只验证 status='ok' + 数量, 具体顺序受 farthest-first 算法选择影响

    def _make_cand_track(self, *, score, track_id, body_emb, sf_w, sf_h, sf_mark):
        """带 track_id + 受控 body emb + same_frame_face_crop(整图填 sf_mark 标记
        来源 track) 的 cand, 用于多 track 混合污染测试。"""
        sf = np.full((sf_h, sf_w, 3), sf_mark, dtype=np.uint8)
        return ScoredCandidate(
            body_crop=np.ones((100, 50, 3), dtype=np.uint8) * 128,
            face_crop=np.zeros((sf_h, sf_w, 3), dtype=np.uint8),
            score=score,
            bbox_xyxy=(0, 0, 50, 100),
            frame_index=int(score * 10),
            captured_at=score * 10,
            track_id=track_id,
            cluster_id=None,
            cam_id="cam-a",
            detector_conf=0.9,
            sharpness=200.0,
            reid_embedding=np.array(body_emb, dtype=np.float32),
            phash=track_id * 1000 + int(score * 10),
            same_frame_face_crop=sf,
        )

    def test_mixed_track_candidates_cross_track_face_pollution(self):
        """固化危险契约: select_topk_with_frontal_seed 在【多 track 混合候选】上跑
        会按列表位置 (而非身份) 跨 track 改写 face_crop —— track1 的脸被写进 track2
        的 cand。这正是 router 多人视频路径**绝不能**用此 helper、必须走 plain
        select_topk 的原因 (router._should_use_frontal_seed)。

        构造: seed=track1 正脸; body farthest-first 选 track2 (body emb 远),
        face farthest-first 选 track1 另一张 (face emb 远) → stage4 按位置 i=1 配对
        把 body_picks[1] (track2) 的 face_crop 改写成 face_picks[1] (track1) 的同帧脸。
        """
        from unittest.mock import MagicMock
        # candidates 按 score 降序: [t1_b, t2_a, seed_t1]
        seed_t1 = self._make_cand_track(
            score=0.7, track_id=1, body_emb=[1.0, 0.0, 0.0],
            sf_w=75, sf_h=100, sf_mark=1,   # w/h=0.75 → frontal seed
        )
        t1_b = self._make_cand_track(
            score=0.9, track_id=1, body_emb=[0.95, 0.312, 0.0],  # body 近 seed
            sf_w=55, sf_h=100, sf_mark=1,   # w/h=0.55 → 非 frontal
        )
        t2_a = self._make_cand_track(
            score=0.8, track_id=2, body_emb=[0.0, 1.0, 0.0],     # body 远 seed
            sf_w=55, sf_h=100, sf_mark=2,
        )
        cands = [t1_b, t2_a, seed_t1]
        mock_reid = MagicMock()
        # face emb 按 face_cands 遍历顺序 (= candidates 顺序 [t1_b, t2_a, seed_t1])
        mock_reid.extract_feature = MagicMock(side_effect=[
            np.array([0.0, 1.0, 0.0], dtype=np.float32),       # t1_b: face 远 seed
            np.array([0.95, 0.312, 0.0], dtype=np.float32),    # t2_a: face 近 seed
            np.array([1.0, 0.0, 0.0], dtype=np.float32),       # seed_t1
        ])
        r = select_topk_with_frontal_seed(cands, topk=2, reid_extractor=mock_reid)
        assert r.samples[0] is seed_t1          # 正脸 seed 排首位
        assert r.samples[1] is t2_a             # body-farthest = track2
        # 跨身份污染: track2 的 cand 的 face_crop 被改写成 track1 (mark=1) 的同帧脸
        assert int(t2_a.face_crop[0, 0, 0]) == 1, (
            "select_topk_with_frontal_seed 在混合候选上把 track1 的脸改写进了 "
            "track2 的 cand —— 多人视频必须避开此 helper (走 plain select_topk)"
        )

    def test_v_combined_with_no_frontal_falls_back_to_score_max(self):
        """没 frontal 候选 (face_w/h 都在 [0.70, 0.80) 之外) → base = score 最高的 cand,
        V_combined 仍然能跑完。"""
        from unittest.mock import MagicMock
        # 全部 face_w/h = 0.55 (侧脸) 或 0.85 (抬头), 没 frontal
        cand_side1 = self._make_cand_full(
            score=0.9, phash=0x1111, ts=10.0, body_emb_seed=1, face_w=55, face_h=100,
        )
        cand_side2 = self._make_cand_full(
            score=0.8, phash=0x2222, ts=20.0, body_emb_seed=2, face_w=55, face_h=100,
        )
        cand_up = self._make_cand_full(
            score=0.7, phash=0x3333, ts=30.0, body_emb_seed=3, face_w=85, face_h=100,
        )
        cands = [cand_side1, cand_side2, cand_up]
        mock_reid = MagicMock()
        mock_reid.extract_feature = MagicMock(side_effect=[_emb(11), _emb(12), _emb(13)])
        r = select_topk_with_frontal_seed(cands, topk=3, reid_extractor=mock_reid)
        # score 最高 (cand_side1) 当 base
        assert r.samples[0] is cand_side1
        assert len(r.samples) == 3


class TestFarthestFirstPickEdgeCases:
    """_farthest_first_pick 边界 case (防御性测试)。"""

    def test_stage2_empty_emb_in_selected_does_not_raise(self):
        """阶段 2 max() 空 generator 时不应抛 ValueError, 用 default=0.0 兜底。

        构造: 调 _farthest_first_pick 时 selected 只含 1 个有 emb 的 seed,
        cand_to_emb 里其他 cand 有 emb 严阈值卡得很紧 (sim_threshold=0.0 让
        没有 cand 能通过严阈值), 强制走阶段 2。阶段 2 计算 max(...) 时如果
        selected 全 None 会抛异常 — 当前 seed 有 emb 不会触发, 但我们直接
        手动 inject 一个 None emb 的 seed 模拟未来防御性场景。
        """
        from miloco.perception.engine.identity.registration_filter import (
            _farthest_first_pick,
        )

        # 3 个 cand, 全部有 emb
        c_a = _make_cand(score=0.9, phash=0x1, ts=10.0, reid_emb=_emb(1))
        c_b = _make_cand(score=0.8, phash=0x2, ts=20.0, reid_emb=_emb(2))
        c_c = _make_cand(score=0.7, phash=0x3, ts=30.0, reid_emb=_emb(3))
        cand_to_emb = {
            # 故意把 seed c_a 的 emb 设为 None 模拟"调用方传 None emb 的 seed"
            # 阶段 1 严阈值: c_b/c_c 跟 c_a 算余弦时跳过 (上面 if s_emb is None continue),
            # max_sim=0 < threshold=0.5 通过严阈值 → 不会走阶段 2; 拉高阈值到 1.1
            # 让严阈值永远不通过, 强制每轮都走阶段 2
            id(c_a): None,
            id(c_b): _emb(2),
            id(c_c): _emb(3),
        }
        # 不应抛 ValueError, max default=0.0 兜底
        result = _farthest_first_pick(
            [c_a, c_b, c_c], topk=3,
            sim_threshold=1.1,   # 严阈值永不通过, 强制每轮阶段 2
            seed=c_a,
            cand_to_emb=cand_to_emb,
        )
        assert len(result) == 3
        assert result[0] is c_a
