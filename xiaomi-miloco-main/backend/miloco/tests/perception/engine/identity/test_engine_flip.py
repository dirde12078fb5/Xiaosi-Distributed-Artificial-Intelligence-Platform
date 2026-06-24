"""翻身份(flip)在 engine 层的行为单测。

- `_on_result` 翻转黏滞计数: 退回后每次未 commit 的重审回流 +1, 达 flip_sticky_max_recheck
  放手(reverted_from_confirmed→False), 防 omni 乱跳时旧名长期挂错人(ID-switch)。
- 集成: `_promote_all_to_pending`(library 变化重置) / `_revoke_track_to_pending`(drift 撤回)
  必须清翻转态, 否则被重置的 track 残留 reverted 会误用 flip 阈值 / 豁免超时。

纯函数级翻转语义(阈值/黏旧名/下窗即派/超时豁免)见 test_state.py::TestFlipIdentity。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from miloco.perception.engine.config import IdentityEngineConfig
from miloco.perception.engine.identity.dispatcher import (
    FusedDispatcher,
    OmniIdentityResult,
)
from miloco.perception.engine.identity.engine import IdentityEngine
from miloco.perception.engine.identity.library import IdentityLibrary
from miloco.perception.engine.identity.state import TrackIdentityState


@pytest.fixture
def lib(tmp_path: Path) -> IdentityLibrary:
    return IdentityLibrary(tmp_path / "identity_lib")


def _make_engine(lib: IdentityLibrary) -> IdentityEngine:
    config = IdentityEngineConfig()  # flip 默认: 高2/中2/低3, flip_sticky_max_recheck=2
    return IdentityEngine(
        config=config, library=lib,
        dispatcher=FusedDispatcher(config=config.dispatch),
        scope_label="cam-test", device_id="cam-test", engine_fps=1.0,
    )


class TestFlipOutcomes:
    """设计 §7 三种翻转结局(均从"退回 pending 预存第 1 票"的真实态起):
    成员高置信→黏 1 窗 commit B; 陌生人→黏 2 窗 commit unknown; omni 乱跳→黏满 2 窗放手。
    """

    @staticmethod
    def _reverted_state(track_id: int, candidate, best_conf=0.9, committed="A") -> TrackIdentityState:
        # 模拟 apply_recheck_result 退回 pending 后的真实态: 黏旧名 committed=A, 预存候选第 1 票。
        # best_conf 决定 flip 门: 成员高置信 0.9→门2; 陌生人(看脸否定低置信)0.1→门3。
        return TrackIdentityState(
            track_id=track_id, status="pending",
            reverted_from_confirmed=True, committed_person_id=committed,
            candidate_person_id=candidate, stability_count=1, best_conf=best_conf,
        )

    @pytest.mark.asyncio
    async def test_member_flip_commits_b_one_window(self, lib):
        """成员·高置信(flip 门=2): 退回预存 B 第 1 票, 再 1 票 B → commit B, 黏 1 窗不放手。"""
        engine = _make_engine(lib)
        st = self._reverted_state(7, candidate="B")
        engine._states[7] = st
        on_result = engine._make_on_result(now_ts=100.0)
        await on_result(OmniIdentityResult(track_id=7, person_id="B", confidence=0.9))
        assert st.status == "confirmed" and st.committed_person_id == "B"
        assert st.reverted_from_confirmed is False and st.flip_recheck_count == 0

    @pytest.mark.asyncio
    async def test_stranger_flip_commits_unknown_no_release(self, lib):
        """陌生人(看脸否定, 退回预存 None 第 1 票, flip 低门=3): 再 2 票 None → 第 2 票 commit
        unknown(黏 2 窗), 早于放手(flip_sticky_max_recheck=2)触发——commit 优先。"""
        engine = _make_engine(lib)
        st = self._reverted_state(7, candidate=None, best_conf=0.1)  # 看脸否定低置信 → flip 低门=3
        engine._states[7] = st
        on_result = engine._make_on_result(now_ts=100.0)
        await on_result(OmniIdentityResult(track_id=7, person_id=None, confidence=0.1))
        assert st.status == "pending" and st.reverted_from_confirmed is True  # 黏#2
        await on_result(OmniIdentityResult(track_id=7, person_id=None, confidence=0.1))
        assert st.status == "unknown"                 # 落陌生人(stability 达 3)
        assert st.reverted_from_confirmed is False     # commit 清翻转态(非放手)

    @pytest.mark.asyncio
    async def test_jitter_releases_after_max_recheck(self, lib):
        """omni 乱跳(候选每窗切换, stability 卡在 1, 永不达门): 黏满 flip_sticky_max_recheck=2
        窗 → 放手, 交还正常状态机(不无限黏旧名, 防 ID-switch)。也覆盖 omni 持续漏报合成 None 的情形。"""
        engine = _make_engine(lib)
        st = self._reverted_state(7, candidate="B")
        engine._states[7] = st
        on_result = engine._make_on_result(now_ts=100.0)
        # 乱跳: C 然后 D, 候选每次切换 → stability 重置为 1, 永不到 flip 门(高 2)
        await on_result(OmniIdentityResult(track_id=7, person_id="C", confidence=0.9))
        assert st.flip_recheck_count == 1 and st.reverted_from_confirmed is True
        await on_result(OmniIdentityResult(track_id=7, person_id="D", confidence=0.9))
        assert st.reverted_from_confirmed is False     # 放手
        assert st.status == "pending"                  # 未掉 unknown, 交还正常状态机


class TestResetHelpersClearFlip:
    def test_promote_all_clears_flip(self, lib):
        engine = _make_engine(lib)
        st = TrackIdentityState(
            track_id=1, status="pending",
            reverted_from_confirmed=True, flip_recheck_count=1, committed_person_id="A",
        )
        engine._states[1] = st
        engine._promote_all_to_pending(now_ts=100.0)
        assert st.reverted_from_confirmed is False
        assert st.flip_recheck_count == 0
        assert st.committed_person_id is None  # library 变化全员去先验

    def test_revoke_track_clears_flip(self, lib):
        """drift enforce 撤回也清翻转态(去先验干净重判, 非翻转)。"""
        engine = _make_engine(lib)
        st = TrackIdentityState(
            track_id=1, status="confirmed", committed_person_id="A",
            reverted_from_confirmed=True, flip_recheck_count=1,
        )
        engine._states[1] = st
        engine._revoke_track_to_pending(st, now_ts=100.0)
        assert st.status == "pending"
        assert st.committed_person_id is None
        assert st.reverted_from_confirmed is False
        assert st.flip_recheck_count == 0
