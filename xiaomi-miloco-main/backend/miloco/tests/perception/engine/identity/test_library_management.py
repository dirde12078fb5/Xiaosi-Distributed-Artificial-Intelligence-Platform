"""身份库管理 (M10):IdentityLibrary.merge_persons / split_person 单测。"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from miloco.perception.engine.identity.library import (
    BodySample,
    IdentityLibrary,
    MergeResult,
    SplitResult,
)


def _make_crop(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, size=(96, 64, 3), dtype=np.uint8)


def _make_emb(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(128).astype(np.float32)
    return v / np.linalg.norm(v)


@pytest.fixture
def lib(tmp_path: Path) -> IdentityLibrary:
    return IdentityLibrary(tmp_path / "identity_lib")


# =============================================================================
# merge_persons
# =============================================================================


class TestMerge:
    def test_merge_two_into_target(self, lib: IdentityLibrary):
        tgt = "11111111-1111-4111-8111-111111111111"
        src = "22222222-2222-4222-8222-222222222222"
        # tgt 已有 2 张
        lib.add_tier_a_sample(tgt, _make_crop(seed=1), source="seed-tgt")
        lib.add_tier_a_sample(tgt, _make_crop(seed=2), source="seed-tgt")
        # src 有 2 张
        lib.add_tier_a_sample(src, _make_crop(seed=10), source="seed-src")
        lib.add_tier_a_sample(src, _make_crop(seed=11), source="seed-src")

        result = lib.merge_persons(tgt, [src])
        assert isinstance(result, MergeResult)
        assert result.target_id == tgt
        assert src in result.merged_sources
        assert result.written_tier_a == 2  # src 全部 2 张并入 tgt(容量 5,够装)

        # source 目录已删
        assert not (lib.persons_dir / src).is_dir()
        # target tier_a 含 4 张 body
        tgt_bodies = list((lib.persons_dir / tgt / "tier_a").glob("body_*.png"))
        assert len(tgt_bodies) == 4

    def test_merge_caps_at_tier_a_max(self, lib: IdentityLibrary):
        """target 已满或合并超过 tier_a_max // 2 时按 sidecar score 降序截断。"""
        tgt = "33333333-3333-4333-8333-333333333333"
        src = "44444444-4444-4444-8444-444444444444"
        # target 已写 5 张(占满 body 容量 5)
        for i in range(5):
            lib.add_tier_a_sample(tgt, _make_crop(seed=i), source="seed-tgt")
        # source 还有 3 张
        for i in range(3):
            lib.add_tier_a_sample(src, _make_crop(seed=20 + i), source="seed-src")

        r = lib.merge_persons(tgt, [src])
        # target 满了,merge 不能再加
        assert r.written_tier_a == 0
        # target 仍 5 张
        assert len(list((lib.persons_dir / tgt / "tier_a").glob("body_*.png"))) == 5

    def test_merge_with_npy_moves_emb_files(self, lib: IdentityLibrary):
        tgt = "77777777-7777-4777-8777-777777777777"
        src = "88888888-8888-4888-8888-888888888888"
        lib.add_tier_a_sample(tgt, _make_crop(), source="seed")
        emb = _make_emb(seed=99)
        lib.add_tier_a_sample(src, _make_crop(seed=50), source="seed",
                                reid_embedding=emb)
        assert list((lib.persons_dir / src / "tier_a").glob("body_*.npy"))

        lib.merge_persons(tgt, [src])
        # src 已删,emb 应该跟着 body 一起搬到 tgt
        tgt_npys = list((lib.persons_dir / tgt / "tier_a").glob("body_*.npy"))
        assert len(tgt_npys) == 1
        loaded = np.load(str(tgt_npys[0]))
        np.testing.assert_allclose(loaded, emb, atol=1e-6)

    def test_merge_writes_audit_field(self, lib: IdentityLibrary):
        """sidecar 应包含 merged_from 字段,便于事后审计来源。"""
        tgt = "99999999-9999-4999-8999-999999999999"
        src = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        lib.add_tier_a_sample(src, _make_crop(seed=70), source="seed")
        lib.add_tier_a_sample(tgt, _make_crop(seed=71), source="seed")

        lib.merge_persons(tgt, [src])
        # 找新进的那一张 sidecar(后写的 idx 更大)
        sidecars = sorted(
            (lib.persons_dir / tgt / "tier_a").glob("body_*.json"),
            key=lambda p: int(p.stem.replace("body_", "")),
        )
        assert len(sidecars) == 2
        last_meta = json.loads(sidecars[-1].read_text(encoding="utf-8"))
        assert last_meta.get("merged_from") == src


# =============================================================================
# split_person
# =============================================================================


class TestSplit:
    def test_split_by_session_id(self, lib: IdentityLibrary):
        """按 register_session_id 把某次注册写入的样本拆到新 person。"""
        src = "00000000-1111-4222-8333-444444444444"
        new_pid = "00000000-2222-4333-8444-555555555555"

        # 灌两次 batch,各带 session_id
        samples_a = [BodySample(body_crop=_make_crop(seed=i),
                                  reid_embedding=_make_emb(i))
                     for i in range(2)]
        samples_b = [BodySample(body_crop=_make_crop(seed=10 + i),
                                  reid_embedding=_make_emb(10 + i))
                     for i in range(2)]
        lib.add_tier_a_samples_batch(src, samples_a, "rs-A")
        lib.add_tier_a_samples_batch(src, samples_b, "rs-B")
        assert len(list((lib.persons_dir / src / "tier_a").glob("body_*.png"))) == 4

        # 拆 rs-A 的样本到新 person
        result = lib.split_person(
            src, new_pid, new_name="拆出来的人",
            selector_session_ids=["rs-A"],
        )
        assert isinstance(result, SplitResult)
        assert result.new_person_id == new_pid
        assert len(result.moved) == 2

        # src 剩 2 张(rs-B)
        src_left = list((lib.persons_dir / src / "tier_a").glob("body_*.png"))
        assert len(src_left) == 2
        # new 有 2 张(rs-A 的)
        new_files = list((lib.persons_dir / new_pid / "tier_a").glob("body_*.png"))
        assert len(new_files) == 2
        # new 的真名落盘到 meta.json
        assert lib.get_name(new_pid) == "拆出来的人"

    def test_split_by_cluster_id(self, lib: IdentityLibrary):
        src = "00000000-3333-4444-8555-666666666666"
        new_pid = "00000000-4444-4555-8666-777777777777"
        # samples_a 的 metadata 带 cluster_id="cl-1",samples_b 带 cluster_id="cl-2"
        samples_a = [
            BodySample(body_crop=_make_crop(seed=i),
                        metadata={"cluster_id": "cl-1"})
            for i in range(2)
        ]
        samples_b = [
            BodySample(body_crop=_make_crop(seed=10 + i),
                        metadata={"cluster_id": "cl-2"})
            for i in range(2)
        ]
        lib.add_tier_a_samples_batch(src, samples_a, "rs-x")
        lib.add_tier_a_samples_batch(src, samples_b, "rs-y")

        r = lib.split_person(src, new_pid, new_name="cl-2 的人",
                              selector_cluster_ids=["cl-2"])
        assert len(r.moved) == 2

    def test_split_empty_selector_noop(self, lib: IdentityLibrary):
        src = "00000000-5555-4666-8777-888888888888"
        new_pid = "00000000-6666-4777-8888-999999999999"
        lib.add_tier_a_samples_batch(src,
                                       [BodySample(body_crop=_make_crop())],
                                       "rs-z")
        # 全部 selector 为 None → noop
        r = lib.split_person(src, new_pid, new_name="empty")
        assert r.moved == []
        # new_pid 目录不该创建
        assert not (lib.persons_dir / new_pid).exists()

    def test_split_no_match_noop(self, lib: IdentityLibrary):
        src = "00000000-7777-4888-8999-aaaaaaaaaaaa"
        new_pid = "00000000-8888-4999-8aaa-bbbbbbbbbbbb"
        lib.add_tier_a_samples_batch(src,
                                       [BodySample(body_crop=_make_crop())],
                                       "rs-real")
        # selector 命中 0 个
        r = lib.split_person(src, new_pid, new_name="x",
                              selector_session_ids=["rs-ghost"])
        assert r.moved == []
        # src 文件不动
        assert len(list((lib.persons_dir / src / "tier_a").glob("body_*.png"))) == 1
