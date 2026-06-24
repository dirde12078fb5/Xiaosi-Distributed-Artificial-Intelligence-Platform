"""注册会话管理单测:pending session lifecycle + commit + sessions + rollback。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from miloco.perception.engine.identity.extractor import ScoredCandidate
from miloco.perception.engine.identity.library import IdentityLibrary
from miloco.perception.engine.identity.registration_session import (
    DEFAULT_PENDING_TTL_SEC,
    CommitResult,
    HistorySession,
    RegistrationSessionManager,
)


def _clock(start: float = 1_700_000_000.0):
    t = [start]
    def fn() -> float:
        return t[0]
    fn.advance = lambda dt: t.__setitem__(0, t[0] + dt)  # type: ignore[attr-defined]
    return fn


def _make_candidate(*, score: float, phash: int, ts: float,
                     reid_emb: np.ndarray | None = None) -> ScoredCandidate:
    return ScoredCandidate(
        body_crop=np.ones((100, 50, 3), dtype=np.uint8) * 128,
        face_crop=None,
        score=score,
        bbox_xyxy=(0, 0, 50, 100),
        frame_index=0,
        captured_at=ts,
        track_id=1,
        cluster_id="cl-test",
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


@pytest.fixture
def lib(tmp_path: Path) -> IdentityLibrary:
    return IdentityLibrary(tmp_path / "identity_lib")


@pytest.fixture
def mgr(lib: IdentityLibrary) -> RegistrationSessionManager:
    return RegistrationSessionManager(lib, now_fn=_clock())


# =============================================================================
# preview / commit 两步走
# =============================================================================


class TestPreviewCommitFlow:
    def test_preview_returns_pending(self, mgr: RegistrationSessionManager):
        cands = [
            _make_candidate(score=1.0, phash=0x0, ts=10.0),
            _make_candidate(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=20.0),
            _make_candidate(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0),
        ]
        pid, sr, sess = mgr.create_pending(
            cands, source="from_media",
            member_id="11111111-1111-4111-8111-111111111111",
        )
        assert pid.startswith("rsp-")
        assert sr.status == "ok"
        assert sess.candidates == cands
        assert len(sess.auto_selected_indices) == 3

    def test_commit_writes_selected_indices(
        self, mgr: RegistrationSessionManager, lib: IdentityLibrary,
    ):
        member_id = "22222222-2222-4222-8222-222222222222"
        cands = [
            _make_candidate(score=1.0, phash=0x0, ts=10.0, reid_emb=_emb(1)),
            _make_candidate(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=20.0, reid_emb=_emb(2)),
            _make_candidate(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0, reid_emb=_emb(3)),
        ]
        pid, _, sess = mgr.create_pending(cands, source="from_pool", member_id=member_id)
        # 用户选了 0 + 2(跳过中间那张)
        result = mgr.commit_pending(pid, indices=[0, 2])
        assert isinstance(result, CommitResult)
        assert result.person_id == member_id
        assert result.register_session_id.startswith("rs-")
        assert len(result.written_samples) == 2
        # commit 后 pending 清掉
        assert mgr.pending_count() == 0
        # 真落盘了
        tier_a_files = list((lib.persons_dir / member_id / "tier_a").glob("body_*.png"))
        assert len(tier_a_files) == 2
        # 每张配 .npy
        npy_files = list((lib.persons_dir / member_id / "tier_a").glob("body_*.npy"))
        assert len(npy_files) == 2

    def test_commit_with_invalid_indices_silently_filtered(
        self, mgr: RegistrationSessionManager,
    ):
        cands = [_make_candidate(score=1.0, phash=0x0, ts=10.0, reid_emb=_emb(1))]
        pid, _, _ = mgr.create_pending(
            cands, source="from_media",
            member_id="33333333-3333-4333-8333-333333333333",
        )
        # indices 含越界 99 应被静默过滤,index 0 仍正常入库
        result = mgr.commit_pending(pid, indices=[0, 99])
        assert result is not None
        assert len(result.written_samples) == 1

    def test_commit_unknown_pending_returns_none(self, mgr: RegistrationSessionManager):
        assert mgr.commit_pending("rsp-ghost", indices=[0]) is None

    def test_auto_indices_preserves_select_fn_order(
        self, mgr: RegistrationSessionManager,
    ):
        """auto_selected_indices 应按 select_fn 输出 sr.samples 的顺序映射, 而非按
        candidates 原顺序枚举。这样 select_topk_with_frontal_seed 把正脸 seed 放在
        sr.samples[0] 时, auto_selected_indices[0] 也是 seed 在 candidates 里的 index
        → 拼图按本顺序展示 → 正脸排第一位 (不是中间)。

        构造: 自定义 select_fn 返回 sr.samples = [cands[2], cands[0]] (倒序),
        验证 auto_selected_indices == [2, 0] 而不是 [0, 2]。
        """
        from miloco.perception.engine.identity.registration_filter import (
            SelectionResult,
        )

        cands = [
            _make_candidate(score=1.0, phash=0x0, ts=10.0),
            _make_candidate(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=20.0),
            _make_candidate(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0),
        ]

        def fake_select(candidates, **kwargs):
            # 倒序: samples[0] 是原 cands[2], samples[1] 是原 cands[0]
            return SelectionResult(
                samples=[candidates[2], candidates[0]],
                status="ok",
                rejected=[],
            )

        pid, sr, sess = mgr.create_pending(
            cands, source="from_media",
            member_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaa01",
            select_fn=fake_select,
        )
        # 关键断言: 顺序跟 sr.samples 一致, 不是按 candidates 原顺序枚举
        assert sess.auto_selected_indices == [2, 0], (
            f"auto_selected_indices 应按 sr.samples 顺序映射 ([2, 0]), "
            f"got {sess.auto_selected_indices}"
        )


# =============================================================================
# 一气呵成 commit_oneshot
# =============================================================================


class TestOneshot:
    def test_oneshot_picks_auto_selected_indices(
        self, mgr: RegistrationSessionManager, lib: IdentityLibrary,
    ):
        member_id = "55555555-5555-4555-8555-555555555555"
        cands = [
            _make_candidate(score=1.0, phash=0x0, ts=10.0, reid_emb=_emb(1)),
            _make_candidate(score=0.9, phash=0xFFFF_FFFF_FFFF_FFFF, ts=20.0, reid_emb=_emb(2)),
            _make_candidate(score=0.8, phash=0x5555_5555_5555_5555, ts=30.0, reid_emb=_emb(3)),
        ]
        r = mgr.commit_oneshot(cands, source="from_pool", member_id=member_id)
        assert r is not None
        assert len(r.written_samples) == 3  # topk 默认 3 全选
        assert mgr.pending_count() == 0     # 内部已 commit 清掉


# =============================================================================
# Pending TTL / GC
# =============================================================================


class TestPendingTTL:
    def test_expired_pending_not_committable(self, lib: IdentityLibrary):
        clock = _clock()
        mgr = RegistrationSessionManager(lib, now_fn=clock, pending_ttl_sec=10.0)
        cands = [_make_candidate(score=1.0, phash=0x0, ts=1.0, reid_emb=_emb(1))]
        pid, _, _ = mgr.create_pending(
            cands, source="from_media",
            member_id="66666666-6666-4666-8666-666666666666",
        )
        # 推进时钟超 TTL
        clock.advance(11.0)  # type: ignore[attr-defined]
        # commit 应返 None(pending 已过期,GC 时被清)
        assert mgr.commit_pending(pid, indices=[0]) is None
        assert mgr.pending_count() == 0

    def test_default_ttl_is_10min(self):
        assert DEFAULT_PENDING_TTL_SEC == 600.0


# =============================================================================
# 历史批次 list / rollback
# =============================================================================


class TestSessionsHistoryAndRollback:
    def test_list_sessions(
        self, mgr: RegistrationSessionManager, lib: IdentityLibrary,
    ):
        member_id = "77777777-7777-4777-8777-777777777777"
        # commit 两批
        for _ in range(2):
            cands = [_make_candidate(score=1.0, phash=0x0, ts=10.0, reid_emb=_emb(1))]
            mgr.commit_oneshot(cands, source="from_media", member_id=member_id)

        sessions = mgr.list_sessions(member_id=member_id)
        assert len(sessions) == 2
        for s in sessions:
            assert isinstance(s, HistorySession)
            assert s.member_id == member_id
            assert s.written_count == 1

    def test_rollback_session_deletes_files(
        self, mgr: RegistrationSessionManager, lib: IdentityLibrary,
    ):
        member_id = "88888888-8888-4888-8888-888888888888"
        cands_a = [_make_candidate(score=1.0, phash=0x0, ts=10.0, reid_emb=_emb(1))]
        cands_b = [_make_candidate(score=1.0, phash=0xFFFF, ts=20.0, reid_emb=_emb(2))]
        r_a = mgr.commit_oneshot(cands_a, source="from_media", member_id=member_id)
        mgr.commit_oneshot(cands_b, source="from_media", member_id=member_id)

        # 两批入库 = 2 张
        assert len(list((lib.persons_dir / member_id / "tier_a").glob("body_*.png"))) == 2
        # rollback A → 剩 1 张
        n = mgr.rollback_session(r_a.register_session_id, member_id=member_id)
        assert n == 1
        assert len(list((lib.persons_dir / member_id / "tier_a").glob("body_*.png"))) == 1
