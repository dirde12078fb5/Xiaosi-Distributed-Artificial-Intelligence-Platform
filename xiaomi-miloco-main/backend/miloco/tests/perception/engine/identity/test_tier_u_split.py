"""TierUPool.split_cluster 单测(M10:陌生人池 commit 前的"误合并修正"接口)。"""

from __future__ import annotations

import numpy as np
from miloco.perception.engine.identity.tier_u import (
    CropEntry,
    TierUConfig,
    TierUPool,
)


def _make_crop(cam: str, tid: int, frame: int, ts: float, sharpness: float = 100.0) -> CropEntry:
    return CropEntry(
        cam_id=cam, track_id=tid, frame_index=frame, captured_at=ts,
        body_crop=np.ones((128, 64, 3), dtype=np.uint8) * 128,
        face_crop=None, sharpness=sharpness,
        bbox_xyxy=(10, 10, 74, 138),
        detector_conf=0.8,
    )


class _MockProvider:
    def __init__(self, embs: dict[tuple[str, int], np.ndarray]):
        self._embs = embs
    def get_embedding(self, cam: str, tid: int):
        return self._embs.get((cam, tid))


def _norm(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


class TestSplitCluster:
    def _setup_cross_cam_cluster(self) -> tuple[TierUPool, str]:
        """搭一个 2-cam cluster:(cam-a, 1) + (cam-b, 1) 挂同 cluster_id。"""
        emb = _norm(np.array([1.0] + [0.0] * 127, dtype=np.float32))
        provider = _MockProvider({("cam-a", 1): emb, ("cam-b", 1): emb.copy()})
        pool = TierUPool(
            config=TierUConfig(l1_capacity=2, reid_threshold_intra_cam=0.9,
                                reid_threshold_cross_cam=0.9),
            reid_provider=provider,
        )
        for cam in ("cam-a", "cam-b"):
            for i in range(2):
                pool.push_crop(_make_crop(cam, 1, i, 1.0 + i))
        pool.flush_if_due()
        # 用全局 fetch 触发跨 cam union → 两条挂同 cluster
        pool.fetch()
        cid = pool._entries[("cam-a", 1)].cluster_id
        assert cid == pool._entries[("cam-b", 1)].cluster_id
        return pool, cid

    def test_split_by_remove_cam(self):
        pool, cid = self._setup_cross_cam_cluster()
        # 把 cam-b 拆出去
        res = pool.split_cluster(cid, remove_cams=["cam-b"])
        assert res is not None
        kept, new_cid = res
        assert kept == cid
        assert new_cid != cid
        # 验证 cluster 重组
        assert pool._clusters[kept].members == {("cam-a", 1)}
        assert pool._clusters[new_cid].members == {("cam-b", 1)}
        assert pool._entries[("cam-a", 1)].cluster_id == kept
        assert pool._entries[("cam-b", 1)].cluster_id == new_cid

    def test_split_by_remove_members(self):
        pool, cid = self._setup_cross_cam_cluster()
        res = pool.split_cluster(cid, remove_members=[("cam-b", 1)])
        assert res is not None
        kept, new_cid = res
        assert pool._clusters[kept].members == {("cam-a", 1)}
        assert pool._clusters[new_cid].members == {("cam-b", 1)}

    def test_split_invalid_cluster_returns_none(self):
        pool, _ = self._setup_cross_cam_cluster()
        assert pool.split_cluster("ghost-cluster", remove_cams=["cam-x"]) is None

    def test_split_no_selector_noop(self):
        pool, cid = self._setup_cross_cam_cluster()
        # selector 为空 → None
        assert pool.split_cluster(cid) is None
        # cluster 不变
        assert len(pool._clusters[cid].members) == 2

    def test_split_all_members_noop(self):
        """如果 selector 命中所有成员,拆光后原 cluster 为空 → 拒绝拆分。"""
        pool, cid = self._setup_cross_cam_cluster()
        res = pool.split_cluster(
            cid, remove_members=[("cam-a", 1), ("cam-b", 1)],
        )
        assert res is None
        # cluster 完好不动
        assert len(pool._clusters[cid].members) == 2

    def test_split_invalidates_match_cache(self):
        """拆分后 match_cache 涉及该 cluster 的项应被清。

        v2 (cluster_pairwise_union) 合并时已主动清涉及被弹 cluster_id 的 cache 项,
        所以 fetch 后 cache 可能为空。本测试手动 inject 一个涉及 cid 的 cache 项
        (模拟此前有过未合并的 pair 比对历史),验证 split 清理逻辑本身。
        """
        pool, cid = self._setup_cross_cam_cluster()
        # 手动 inject: 模拟 cid 跟某第三方 cluster 的 cache 项
        other_cid = "other-cluster-id"
        pool._match_cache[frozenset((cid, other_cid))] = 0.5
        assert len(pool._match_cache) > 0
        pool.split_cluster(cid, remove_cams=["cam-b"])
        # 两侧 cluster 涉及的 pair 都该清了
        for key in list(pool._match_cache.keys()):
            assert cid not in key
