"""IdentityLibrary v1.2 主动注册新增功能单测。

覆盖：
- ``add_tier_a_samples_batch`` 批量入库 + sidecar 含 register_session_id + metadata
- ``delete_by_register_session`` 精确删该批次写入的所有文件 + sidecar
- 老 sidecar（无 register_session_id）向后兼容
- 批量入库到容量上限时按"先到先得"截断
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import pytest
from miloco.perception.engine.identity.library import (
    BodySample,
    IdentityLibrary,
    _sanitize_cam_did,
)


def _make_crop(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, size=(96, 64, 3), dtype=np.uint8)


def _make_samples(n: int, seed_base: int = 0, with_face: bool = False) -> list[BodySample]:
    return [
        BodySample(
            body_crop=_make_crop(seed_base + i),
            face_crop=_make_crop(seed_base + 100 + i) if with_face else None,
            source="register_session",
            captured_at=1_700_000_000.0 + i,
            metadata={
                "cluster_id": f"cluster-{seed_base}",
                "score": 1.0 + 0.1 * i,
                "camera_id": "foyer_cam",
                "track_id": 7,
                "phash": f"{seed_base:016x}",
            },
        )
        for i in range(n)
    ]


@pytest.fixture
def lib(tmp_path: Path) -> IdentityLibrary:
    return IdentityLibrary(tmp_path / "identity_lib")


class TestBatchWrite:
    def test_batch_writes_sidecar_with_session_id(self, lib: IdentityLibrary):
        pid = "11111111-1111-4111-8111-111111111111"
        session_id = "rs-batch-1"
        samples = _make_samples(3, with_face=True)

        written = lib.add_tier_a_samples_batch(pid, samples, session_id, name="阿飞")

        assert len(written) == 3
        # body sidecar 含 register_session_id + 调用方传入的 cluster_id / score
        for fname in written:
            sidecar = lib.persons_dir / pid / "tier_a" / fname.replace(".png", ".json")
            meta = json.loads(sidecar.read_text(encoding="utf-8"))
            assert meta["register_session_id"] == session_id
            assert meta["cluster_id"] == "cluster-0"
            assert meta["score"] == pytest.approx(1.0, abs=0.3)
            assert meta["tier"] == "a"
            assert meta["kind"] == "body"
        # face 同名跟随 + 也带 register_session_id
        face_sidecars = list((lib.persons_dir / pid / "tier_a").glob("face_*.json"))
        assert len(face_sidecars) == 3
        for fs in face_sidecars:
            assert json.loads(fs.read_text(encoding="utf-8"))["register_session_id"] == session_id

    def test_batch_truncates_at_capacity(self, lib: IdentityLibrary):
        # tier_a_max_per_person 默认 10 → body 上限 5
        pid = "22222222-2222-4222-8222-222222222222"
        samples = _make_samples(8)  # 灌 8 张，应该只写下 5

        written = lib.add_tier_a_samples_batch(pid, samples, "rs-cap-1")

        assert len(written) == 5
        actual_files = list((lib.persons_dir / pid / "tier_a").glob("body_*.png"))
        assert len(actual_files) == 5

    def test_batch_empty_returns_empty(self, lib: IdentityLibrary):
        pid = "33333333-3333-4333-8333-333333333333"
        assert lib.add_tier_a_samples_batch(pid, [], "rs-empty") == []


class TestRollbackBySession:
    def test_delete_exactly_session_files(self, lib: IdentityLibrary):
        pid = "44444444-4444-4444-8444-444444444444"
        # 灌两批不同 session 的样本
        a = lib.add_tier_a_samples_batch(pid, _make_samples(2, seed_base=0), "rs-A")
        b = lib.add_tier_a_samples_batch(pid, _make_samples(2, seed_base=10), "rs-B")
        assert len(a) == 2 and len(b) == 2

        # rollback rs-A
        n = lib.delete_by_register_session(pid, "rs-A")
        assert n == 2  # 2 个 sidecar 被删

        # rs-B 的样本应当还在
        remaining = sorted((lib.persons_dir / pid / "tier_a").glob("body_*.png"))
        assert len(remaining) == 2
        for jpg in remaining:
            sidecar = jpg.with_suffix(".json")
            assert json.loads(sidecar.read_text(encoding="utf-8"))["register_session_id"] == "rs-B"

    def test_delete_unknown_session_noop(self, lib: IdentityLibrary):
        pid = "55555555-5555-4555-8555-555555555555"
        lib.add_tier_a_samples_batch(pid, _make_samples(2), "rs-real")
        assert lib.delete_by_register_session(pid, "rs-ghost") == 0
        # 真实 session 文件不动
        assert len(list((lib.persons_dir / pid / "tier_a").glob("body_*.png"))) == 2

    def test_old_sidecar_no_session_field_survives_rollback(self, lib: IdentityLibrary):
        """老 sidecar 没有 register_session_id 字段时，不该被任何 rollback 误删。"""
        pid = "66666666-6666-4666-8666-666666666666"
        # 模拟老接口写入（没有 register_session_id）
        lib.add_tier_a_sample(pid, _make_crop(), source="legacy_upload")
        lib.add_tier_a_samples_batch(pid, _make_samples(1), "rs-new")

        # 任意 session rollback
        n = lib.delete_by_register_session(pid, "rs-anything")
        assert n == 0  # 老 sidecar 无字段，rs-new sidecar 不匹配，都安全
        # rollback rs-new → 只清新 session 的
        assert lib.delete_by_register_session(pid, "rs-new") == 1
        # 老样本仍在
        remaining = list((lib.persons_dir / pid / "tier_a").glob("body_*.png"))
        assert len(remaining) == 1


class TestReIDEmbedding:
    """ReID embedding 落盘 / 读取(v1.2 主动注册系列)。"""

    def _make_emb(self, seed: int = 0) -> np.ndarray:
        """构造 L2-normalized 128-dim emb。"""
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(128).astype(np.float32)
        return v / np.linalg.norm(v)

    def test_add_sample_writes_npy(self, lib: IdentityLibrary):
        pid = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        emb = self._make_emb(seed=1)
        lib.add_tier_a_sample(pid, _make_crop(), source="test", reid_embedding=emb)

        body_files = sorted((lib.persons_dir / pid / "tier_a").glob("body_*.png"))
        assert len(body_files) == 1
        npy_path = body_files[0].with_suffix(".npy")
        assert npy_path.exists()
        loaded = np.load(str(npy_path))
        np.testing.assert_allclose(loaded, emb, atol=1e-6)

    def test_get_sample_embedding(self, lib: IdentityLibrary):
        pid = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
        emb = self._make_emb(seed=2)
        lib.add_tier_a_sample(pid, _make_crop(), source="test", reid_embedding=emb)

        body_files = sorted((lib.persons_dir / pid / "tier_a").glob("body_*.png"))
        loaded = lib.get_sample_embedding(pid, "a", body_files[0].name)
        np.testing.assert_allclose(loaded, emb, atol=1e-6)

    def test_get_embedding_returns_none_when_missing(self, lib: IdentityLibrary):
        pid = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
        # 不传 emb,只写 jpg
        lib.add_tier_a_sample(pid, _make_crop(), source="test")
        body_files = sorted((lib.persons_dir / pid / "tier_a").glob("body_*.png"))
        assert lib.get_sample_embedding(pid, "a", body_files[0].name) is None

    def test_batch_write_emb_per_sample(self, lib: IdentityLibrary):
        pid = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
        samples = _make_samples(3, seed_base=0)
        # 给每个 BodySample 塞自己的 emb
        embs = [self._make_emb(seed=i + 10) for i in range(3)]
        for s, e in zip(samples, embs):
            s.reid_embedding = e

        written = lib.add_tier_a_samples_batch(pid, samples, "rs-emb-1")
        assert len(written) == 3

        # 三个 .npy 都该落盘且内容一致
        for fname, expected in zip(sorted(written), embs):
            loaded = lib.get_sample_embedding(pid, "a", fname)
            np.testing.assert_allclose(loaded, expected, atol=1e-6)

    def test_batch_falls_back_to_reid_extractor_when_sample_emb_missing(
        self, lib: IdentityLibrary,
    ):
        """sample.reid_embedding 为 None 时,若传了 reid_extractor,现场抽一次落盘。

        覆盖陌生人池 L1/L2 都没拉到 emb 的极端 race。
        """
        pid = "11111111-2222-4333-8444-555555555555"
        samples = _make_samples(2, seed_base=50)
        # 故意全部 reid_embedding=None
        for s in samples:
            s.reid_embedding = None

        # mock extractor:每次返一个固定 emb
        fake_emb = self._make_emb(seed=99)

        class _FakeExtractor:
            calls = 0

            def extract_feature(self, body_crop):
                _FakeExtractor.calls += 1
                return fake_emb

        extractor = _FakeExtractor()
        written = lib.add_tier_a_samples_batch(
            pid, samples, "rs-fallback-1", reid_extractor=extractor,
        )
        assert len(written) == 2
        assert extractor.calls == 2, "每个 sample 都应触发一次 extract_feature"

        # 所有 .npy 都落盘
        for fname in written:
            loaded = lib.get_sample_embedding(pid, "a", fname)
            assert loaded is not None, f"{fname} 应有 .npy"
            np.testing.assert_allclose(loaded, fake_emb, atol=1e-6)

    def test_batch_skips_extractor_when_sample_already_has_emb(
        self, lib: IdentityLibrary,
    ):
        """sample.reid_embedding 已经填好时,不应触发 reid_extractor 抽取(避免无谓推理)。"""
        pid = "22222222-3333-4444-8555-666666666666"
        samples = _make_samples(2, seed_base=60)
        for s in samples:
            s.reid_embedding = self._make_emb(seed=int(s.captured_at) + 100)

        class _FakeExtractor:
            calls = 0

            def extract_feature(self, body_crop):
                _FakeExtractor.calls += 1
                return np.zeros(128, dtype=np.float32)

        extractor = _FakeExtractor()
        lib.add_tier_a_samples_batch(
            pid, samples, "rs-skip-1", reid_extractor=extractor,
        )
        assert extractor.calls == 0, "sample 自带 emb 时不该再抽"

    def test_batch_no_extractor_no_npy_when_sample_emb_missing(
        self, lib: IdentityLibrary,
    ):
        """无 sample emb 又无 reid_extractor → 跳过 .npy,旧行为兼容。"""
        pid = "33333333-4444-4555-8666-777777777777"
        samples = _make_samples(1, seed_base=70)
        samples[0].reid_embedding = None

        lib.add_tier_a_samples_batch(pid, samples, "rs-noext-1")
        body_files = sorted((lib.persons_dir / pid / "tier_a").glob("body_*.png"))
        npy = body_files[0].with_suffix(".npy")
        assert not npy.exists(), "无 extractor 时 .npy 不应被写"

    def test_normalize_on_write_if_needed(self, lib: IdentityLibrary):
        """写盘前自动归一化非 L2-norm 输入,防下游误用未归一化向量。"""
        pid = "ffffffff-ffff-4fff-8fff-ffffffffffff"
        raw = np.ones(128, dtype=np.float32) * 5.0  # 未归一化,模长 = 5*sqrt(128)
        lib.add_tier_a_sample(pid, _make_crop(), source="test", reid_embedding=raw)

        body_files = sorted((lib.persons_dir / pid / "tier_a").glob("body_*.png"))
        loaded = lib.get_sample_embedding(pid, "a", body_files[0].name)
        # 落盘后应该已 L2-norm
        assert abs(np.linalg.norm(loaded) - 1.0) < 1e-5

    def test_rollback_cleans_npy(self, lib: IdentityLibrary):
        """rollback 按 register_session_id 删 jpg+sidecar+npy 全部清。"""
        pid = "00000000-1111-4222-8333-444444444444"
        samples = _make_samples(2)
        for s in samples:
            s.reid_embedding = self._make_emb(seed=20)
        lib.add_tier_a_samples_batch(pid, samples, "rs-rollback-emb")

        # 落盘前确认 .npy 存在
        npys = list((lib.persons_dir / pid / "tier_a").glob("body_*.npy"))
        assert len(npys) == 2

        # rollback
        n = lib.delete_by_register_session(pid, "rs-rollback-emb")
        assert n == 2
        # .npy 也跟着清干净
        npys_after = list((lib.persons_dir / pid / "tier_a").glob("body_*.npy"))
        assert npys_after == []

    def test_tier_c_fifo_cleans_npy(self, lib: IdentityLibrary):
        """tier_c FIFO 弹最旧时,同名 .npy 也一并清。"""
        import time
        pid = "00000000-2222-4333-8444-555555555555"
        # 先建 tier_a(否则 tier_c 写入被拒)
        lib.add_tier_a_sample(pid, _make_crop(), source="seed")

        # 灌满 tier_c_max(默认 10) + 1 触发 FIFO（同相机 cam_A）
        for i in range(11):
            # 错开 mtime 让 FIFO 顺序确定
            lib.add_tier_c_sample(
                pid, _make_crop(seed=i + 100),
                captured_at=time.time() + i,
                reid_embedding=self._make_emb(seed=i + 30),
                cam_id="cam_A",
            )

        tier_c_dir = lib.persons_dir / pid / "tier_c" / "cam_A"
        jpgs = sorted(tier_c_dir.glob("body_*.png"), key=lambda p: p.stat().st_mtime)
        npys = sorted(tier_c_dir.glob("body_*.npy"), key=lambda p: p.stat().st_mtime)
        # 总数 = tier_c_max
        assert len(jpgs) == lib.tier_c_max
        assert len(npys) == lib.tier_c_max
        # 一一配对:每个 jpg 都有同 stem 的 .npy
        for j in jpgs:
            assert j.with_suffix(".npy").exists()


class TestTierCFromCamera:
    """tier_c sidecar 记录来源相机(多相机来源审计)。"""

    def test_from_camera_fields_persisted_to_sidecar(self, lib: IdentityLibrary):
        """add_tier_c_sample 传入的 camera_id/camera_name 落进 sidecar。

        回归守卫:§4 把 tier_c 落盘改成 per-(person,cam) 子目录后,来源相机字段不得丢
        (用 rglob 兼容子目录布局,§4 落地后本测试仍应通过)。
        """
        pid = "cccccccc-0000-4ccc-8ccc-cccccccccccc"
        lib.add_tier_a_sample(pid, _make_crop(), source="seed")  # tier_c 写入前置
        ok = lib.add_tier_c_sample(
            pid, _make_crop(seed=7),
            extra_meta={
                "camera_id": "1178866901",
                "camera_name": "小米智能摄像机C700",
            },
            cam_id="1178866901",
        )
        assert ok
        sidecars = list((lib.persons_dir / pid / "tier_c").rglob("body_*.json"))
        assert len(sidecars) == 1
        meta = json.loads(sidecars[0].read_text(encoding="utf-8"))
        assert meta["camera_id"] == "1178866901"
        assert meta["camera_name"] == "小米智能摄像机C700"


class TestTierCMultiCamIsolation:
    """§4: tier_c per-(person,cam) 子目录隔离。"""

    def test_per_cam_fifo_no_eviction_across_cams(self, lib: IdentityLibrary):
        """camA 灌 11、camB 灌 3 → camA 留 10(FIFO)、camB 留 3，互不挤占。"""
        pid = "a1000000-0000-4000-8000-000000000001"
        lib.add_tier_a_sample(pid, _make_crop(), source="seed")
        for i in range(11):
            lib.add_tier_c_sample(pid, _make_crop(seed=i + 1),
                                  captured_at=1_700_000_000.0 + i, cam_id="camA")
        for i in range(3):
            lib.add_tier_c_sample(pid, _make_crop(seed=100 + i),
                                  captured_at=1_700_000_500.0 + i, cam_id="camB")
        cam_a = lib.persons_dir / pid / "tier_c" / "camA"
        cam_b = lib.persons_dir / pid / "tier_c" / "camB"
        assert len(list(cam_a.glob("body_*.png"))) == lib.tier_c_max  # 10
        assert len(list(cam_b.glob("body_*.png"))) == 3

    def test_pick_body_files_per_cam_isolation(self, lib: IdentityLibrary):
        """_pick_body_files 只取本相机 tier_c;本相机无 tier_c → 纯 tier_a。"""
        person_dir = lib.persons_dir / "person-mc"
        (person_dir / "tier_a").mkdir(parents=True)
        (person_dir / "tier_a" / "body_a1.jpg").touch()
        for cam in ("camA", "camB"):
            d = person_dir / "tier_c" / cam
            d.mkdir(parents=True)
            f = d / f"body_{cam}.jpg"
            f.touch()
            f.with_suffix(".json").write_text(
                json.dumps({"verify_same_person": True}), encoding="utf-8")
        _, c_a = lib._pick_body_files(person_dir, body_n=3, cam_id="camA")
        _, c_b = lib._pick_body_files(person_dir, body_n=3, cam_id="camB")
        assert [p.name for p in c_a] == ["body_camA.jpg"]
        assert [p.name for p in c_b] == ["body_camB.jpg"]
        # 本相机无 tier_c → c 空、纯 tier_a
        a_z, c_z = lib._pick_body_files(person_dir, body_n=3, cam_id="camZ")
        assert c_z == []
        assert len(a_z) >= 1

    def test_legacy_flat_frozen(self, lib: IdentityLibrary):
        """根下 legacy 扁平样本:不进 gallery 选样、写新样本 FIFO 不淘汰它、跨摄(emb/计数)仍读到。"""
        pid = "a1000000-0000-4000-8000-00000000000c"
        lib.add_tier_a_sample(pid, _make_crop(), source="seed")
        tier_c = lib.persons_dir / pid / "tier_c"
        tier_c.mkdir(parents=True, exist_ok=True)
        legacy = tier_c / "body_1.jpg"
        legacy.touch()
        legacy.with_suffix(".json").write_text(
            json.dumps({"verify_same_person": True}), encoding="utf-8")
        _write_npy(tier_c / "body_1.npy", _make_unit_emb(1))
        # ① gallery 选样(任何 cam)不取 legacy(只看 tier_c/<cam>/)
        _, c_picked = lib._pick_body_files(lib.persons_dir / pid, body_n=3, cam_id="camA")
        assert c_picked == []
        # ② 写新样本到 camA 灌满触发 FIFO，legacy 不被淘汰(冻结)
        for i in range(11):
            lib.add_tier_c_sample(pid, _make_crop(seed=200 + i),
                                  captured_at=1_700_000_000.0 + i, cam_id="camA")
        assert legacy.exists()
        # ③ 跨摄 emb 读到 legacy(camA 样本没带 emb → 仅 legacy 1 张 npy)
        assert len(lib.get_person_tier_c_embs(pid)) == 1
        # ④ num_tier_c 计入 legacy + camA
        ref = next(r for r in lib.list_persons() if r.person_id == pid)
        assert ref.num_tier_c == 1 + lib.tier_c_max

    def test_dedup_emb_reads_all_cams(self, lib: IdentityLibrary):
        """get_person_tier_c_embs 跨摄全读:camA + camB 的 emb 都返回。"""
        pid = "a1000000-0000-4000-8000-00000000000d"
        lib.add_tier_a_sample(pid, _make_crop(), source="seed")
        lib.add_tier_c_sample(pid, _make_crop(seed=1), cam_id="camA",
                              reid_embedding=_make_unit_emb(1))
        lib.add_tier_c_sample(pid, _make_crop(seed=2), cam_id="camB",
                              reid_embedding=_make_unit_emb(2))
        assert len(lib.get_person_tier_c_embs(pid)) == 2

    def test_gallery_cache_key_per_cam(self, lib: IdentityLibrary):
        """缓存键 (pid,cam):cam=A 与 cam=B 各一条;person_ids 缩小后 GC 都 pop。"""
        pid = "a1000000-0000-4000-8000-00000000000e"
        lib.add_tier_a_sample(pid, _make_crop(), source="seed")
        lib.get_gallery_composites_for_omni(person_ids=[pid], cam_id="camA")
        lib.get_gallery_composites_for_omni(person_ids=[pid], cam_id="camB")
        keys = set(lib._composite_cache.keys())
        assert (pid, "camA") in keys
        assert (pid, "camB") in keys
        # GC:传不含 pid 的列表 → 两条都清
        lib.get_gallery_composites_for_omni(person_ids=[], cam_id="camA")
        assert all(k[0] != pid for k in lib._composite_cache)

    def test_sanitize_cam_did_in_path(self, lib: IdentityLibrary):
        """cam_id 含非法目录字符 → 子目录名被 sanitize;写入不抛、能按同 cam_id 取回。"""
        pid = "a1000000-0000-4000-8000-00000000000f"
        lib.add_tier_a_sample(pid, _make_crop(), source="seed")
        weird = "lumi/1:2*3"
        ok = lib.add_tier_c_sample(pid, _make_crop(seed=1), cam_id=weird,
                                   extra_meta={"verify_same_person": True})
        assert ok
        safe = _sanitize_cam_did(weird)
        assert "/" not in safe and ":" not in safe and "*" not in safe
        assert (lib.persons_dir / pid / "tier_c" / safe).is_dir()
        _, c_picked = lib._pick_body_files(lib.persons_dir / pid, body_n=3, cam_id=weird)
        assert len(c_picked) == 1

    def test_merge_persons_preserves_cam_subdirs(self, lib: IdentityLibrary):
        """merge 保留来源相机子目录:src tier_c/camX/ → target tier_c/camX/，各 cam 各 FIFO。"""
        src = "a1000000-0000-4000-8000-0000000000a1"
        tgt = "a1000000-0000-4000-8000-0000000000a2"
        for pid in (src, tgt):
            lib.add_tier_a_sample(pid, _make_crop(), source="seed")
        # src camX 放 2 张、camY 1 张
        for i in range(2):
            lib.add_tier_c_sample(src, _make_crop(seed=i + 1),
                                  captured_at=1_700_000_000.0 + i, cam_id="camX")
        lib.add_tier_c_sample(src, _make_crop(seed=9),
                              captured_at=1_700_000_100.0, cam_id="camY")
        lib.merge_persons(target_id=tgt, source_ids=[src])
        tgt_tier_c = lib.persons_dir / tgt / "tier_c"
        assert len(list((tgt_tier_c / "camX").glob("body_*.png"))) == 2
        assert len(list((tgt_tier_c / "camY").glob("body_*.png"))) == 1
        assert not (lib.persons_dir / src).exists()  # src 已删


class TestBackfillReIDEmbeddings:
    """老库适配:backfill_reid_embeddings 给历史 body 补 .npy。"""

    def _make_emb(self, seed: int = 0) -> np.ndarray:
        rng = np.random.default_rng(seed)
        v = rng.standard_normal(128).astype(np.float32)
        return v / np.linalg.norm(v)

    def _make_extractor(self, seed: int = 0):
        """mock HumanReID:每次调用返同一个 emb,便于断言写盘内容。"""
        from unittest.mock import MagicMock
        emb = self._make_emb(seed)
        extractor = MagicMock()
        extractor.extract_feature = MagicMock(return_value=emb)
        return extractor, emb

    def test_backfill_missing_npy_only(self, lib: IdentityLibrary):
        """已有 .npy 跳过,缺失的现场抽。"""
        pid = "ee000000-eeee-4eee-8eee-eeeeeeeeeeee"
        # 第 1 张:不带 emb 写入(模拟老库)
        lib.add_tier_a_sample(pid, _make_crop(seed=1), source="legacy")
        # 第 2 张:带 emb(模拟新库)
        existing_emb = self._make_emb(seed=2)
        lib.add_tier_a_sample(pid, _make_crop(seed=2), source="new",
                                reid_embedding=existing_emb)

        extractor, fake_emb = self._make_extractor(seed=99)
        result = lib.backfill_reid_embeddings(extractor)

        assert result["scanned"] == 2
        assert result["generated"] == 1  # 只补第 1 张
        assert result["skipped"] == 1
        assert result["failed"] == 0

        # 两张都该有 .npy
        npys = sorted((lib.persons_dir / pid / "tier_a").glob("body_*.npy"))
        assert len(npys) == 2
        # 已存在的那张内容不被覆盖
        assert any(
            np.allclose(np.load(str(n)), existing_emb, atol=1e-6) for n in npys
        )
        # 新生成的那张是 fake_emb
        assert any(
            np.allclose(np.load(str(n)), fake_emb, atol=1e-6) for n in npys
        )

    def test_backfill_force_regenerates_all(self, lib: IdentityLibrary):
        """force=True 即便 .npy 已存在也重新生成(切换 ReID 模型场景)。"""
        pid = "ff000000-ffff-4fff-8fff-ffffffffffff"
        existing_emb = self._make_emb(seed=10)
        lib.add_tier_a_sample(pid, _make_crop(), source="seed",
                                reid_embedding=existing_emb)

        extractor, new_emb = self._make_extractor(seed=20)
        result = lib.backfill_reid_embeddings(extractor, force=True)

        assert result["generated"] == 1
        assert result["skipped"] == 0
        # 内容被覆盖
        npy = next((lib.persons_dir / pid / "tier_a").glob("body_*.npy"))
        np.testing.assert_allclose(np.load(str(npy)), new_emb, atol=1e-6)

    def test_backfill_person_ids_filter(self, lib: IdentityLibrary):
        """person_ids 给定时只扫指定 person。"""
        pid1 = "aa000000-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        pid2 = "bb000000-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        lib.add_tier_a_sample(pid1, _make_crop(), source="legacy")
        lib.add_tier_a_sample(pid2, _make_crop(), source="legacy")

        extractor, _ = self._make_extractor()
        result = lib.backfill_reid_embeddings(extractor, person_ids=[pid1])
        assert result["scanned"] == 1
        assert result["generated"] == 1
        # pid2 不该有 .npy
        assert not list((lib.persons_dir / pid2 / "tier_a").glob("body_*.npy"))

    def test_backfill_tier_c_too(self, lib: IdentityLibrary):
        """默认 tiers=("a","c"),tier_c 也回填。"""
        import time as _time
        pid = "cc000000-cccc-4ccc-8ccc-cccccccccccc"
        lib.add_tier_a_sample(pid, _make_crop(), source="seed")
        # tier_c 不带 emb(老库式)
        lib.add_tier_c_sample(pid, _make_crop(seed=50),
                                captured_at=_time.time(), cam_id="cam_A")
        extractor, _ = self._make_extractor()
        result = lib.backfill_reid_embeddings(extractor)
        # tier_a 1 张 + tier_c 1 张
        assert result["scanned"] == 2
        assert result["generated"] == 2

    def test_backfill_extract_failure_counted(self, lib: IdentityLibrary):
        """extract_feature 抛异常时计入 failed,不阻断其它样本。"""
        from unittest.mock import MagicMock
        pid = "dd000000-dddd-4ddd-8ddd-dddddddddddd"
        lib.add_tier_a_sample(pid, _make_crop(seed=1), source="legacy")
        lib.add_tier_a_sample(pid, _make_crop(seed=2), source="legacy")

        # 第 1 次成功,第 2 次抛
        extractor = MagicMock()
        extractor.extract_feature = MagicMock(
            side_effect=[self._make_emb(), RuntimeError("boom")],
        )
        result = lib.backfill_reid_embeddings(extractor)
        assert result["scanned"] == 2
        assert result["generated"] == 1
        assert result["failed"] == 1


# =============================================================================
# get_person_mean_emb / get_person_tier_c_embs (pool_fetch dedup 消费侧)
# =============================================================================


def _make_unit_emb(seed: int, dim: int = 128) -> np.ndarray:
    """构造 L2-normalized 单位 emb."""
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(dim).astype(np.float32)
    return v / np.linalg.norm(v)


def _write_npy(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(path), arr)


class TestGetPersonMeanEmb:
    def test_no_tier_a_dir_returns_none(self, lib: IdentityLibrary):
        """person 没 tier_a 目录 → None"""
        assert lib.get_person_mean_emb("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa") is None

    def test_empty_tier_a_returns_none(self, lib: IdentityLibrary):
        """tier_a 目录存在但无 body_*.npy → None"""
        pid = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        (lib.persons_dir / pid / "tier_a").mkdir(parents=True)
        assert lib.get_person_mean_emb(pid) is None

    def test_single_emb_returns_l2_normalized(self, lib: IdentityLibrary):
        """单张 .npy → mean = 自身, L2 归一化后返回。"""
        pid = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
        emb = _make_unit_emb(seed=1)
        _write_npy(lib.persons_dir / pid / "tier_a" / "body_001.npy", emb)
        out = lib.get_person_mean_emb(pid)
        assert out is not None
        # 已是单位向量, mean=self 归一化后应当跟输入相等 (浮点容差内)
        np.testing.assert_allclose(out, emb, atol=1e-6)
        assert abs(float(np.linalg.norm(out)) - 1.0) < 1e-5

    def test_multiple_embs_mean_then_normalize(self, lib: IdentityLibrary):
        """N 张 → mean 后 L2 归一化, 长度 ≈ 1。"""
        pid = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
        for i in range(4):
            _write_npy(
                lib.persons_dir / pid / "tier_a" / f"body_{i:03d}.npy",
                _make_unit_emb(seed=i + 10),
            )
        out = lib.get_person_mean_emb(pid)
        assert out is not None
        assert abs(float(np.linalg.norm(out)) - 1.0) < 1e-5

    def test_load_failure_skips_file_logs_warning(self, lib: IdentityLibrary, caplog):
        """损坏 .npy 加载失败时跳过该文件 + log warning, 其他正常文件 mean 不受影响。"""
        import logging
        pid = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
        emb = _make_unit_emb(seed=20)
        _write_npy(lib.persons_dir / pid / "tier_a" / "body_001.npy", emb)
        # 写一个损坏文件 (非 .npy 格式)
        bad = lib.persons_dir / pid / "tier_a" / "body_002.npy"
        bad.write_bytes(b"not a valid npy file")
        with caplog.at_level(logging.WARNING):
            out = lib.get_person_mean_emb(pid)
        assert out is not None
        # 应当跳过坏文件, 仍能从 body_001 算出 mean
        np.testing.assert_allclose(out, emb, atol=1e-6)
        # 触发了 warning
        assert any("读 ReID emb 失败" in r.message for r in caplog.records)

    def test_zero_mean_returns_none(self, lib: IdentityLibrary):
        """构造 mean 为零向量的极端 case: 两张相反方向单位向量相互抵消。norm=0 时
        返 None (跟"无可用 emb"等价), 而非零向量 —— 零向量进下游 _cosine 是
        0/0=nan, 不会误命中 (nan>=阈值恒 False) 但会污染 dedup log。调用方
        pool_fetch 的 _build_emb_lookups 已有 None 过滤, 直接跳过该 person。
        """
        pid = "ffffffff-ffff-4fff-8fff-ffffffffffff"
        v = np.zeros(128, dtype=np.float32)
        v[0] = 1.0
        _write_npy(lib.persons_dir / pid / "tier_a" / "body_001.npy", v)
        _write_npy(lib.persons_dir / pid / "tier_a" / "body_002.npy", -v)
        out = lib.get_person_mean_emb(pid)
        assert out is None


class TestGetPersonTierCEmbs:
    def test_no_tier_c_dir_returns_empty(self, lib: IdentityLibrary):
        assert lib.get_person_tier_c_embs("11111111-1111-4111-8111-111111111111") == []

    def test_empty_tier_c_returns_empty(self, lib: IdentityLibrary):
        pid = "22222222-2222-4222-8222-222222222222"
        (lib.persons_dir / pid / "tier_c").mkdir(parents=True)
        assert lib.get_person_tier_c_embs(pid) == []

    def test_multiple_embs_returned_as_list_not_mean(self, lib: IdentityLibrary):
        """tier_c 返 list[ndarray] 逐张, 不 mean (差异化 dedup 用)。"""
        pid = "33333333-3333-4333-8333-333333333333"
        for i in range(3):
            _write_npy(
                lib.persons_dir / pid / "tier_c" / f"body_{i:03d}.npy",
                _make_unit_emb(seed=i + 50),
            )
        out = lib.get_person_tier_c_embs(pid)
        assert isinstance(out, list)
        assert len(out) == 3
        for emb in out:
            assert isinstance(emb, np.ndarray)
            assert emb.shape == (128,)

    def test_load_failure_skips_silently_keeps_rest(self, lib: IdentityLibrary, caplog):
        """损坏 .npy 跳过 + log, 不影响其他文件返回。"""
        import logging
        pid = "44444444-4444-4444-8444-444444444444"
        _write_npy(lib.persons_dir / pid / "tier_c" / "body_001.npy",
                   _make_unit_emb(seed=60))
        (lib.persons_dir / pid / "tier_c" / "body_002.npy").write_bytes(b"bad")
        _write_npy(lib.persons_dir / pid / "tier_c" / "body_003.npy",
                   _make_unit_emb(seed=61))
        with caplog.at_level(logging.WARNING):
            out = lib.get_person_tier_c_embs(pid)
        # 2 张成功 + 1 张被跳过
        assert len(out) == 2
        assert any("读 tier_c ReID emb 失败" in r.message for r in caplog.records)


class TestTierCTrustedFilter:
    """_tier_c_sample_verified (sidecar 三态) + _pick_body_files trusted 只回喂校验通过样本。"""

    def test_sample_verified_three_states(self, tmp_path: Path):
        # 1) 无 sidecar → False
        assert IdentityLibrary._tier_c_sample_verified(tmp_path / "body_1.jpg") is False
        # 2) 有 sidecar 但无 verify_same_person 字段 → False
        p2 = tmp_path / "body_2.jpg"
        p2.with_suffix(".json").write_text(json.dumps({}), encoding="utf-8")
        assert IdentityLibrary._tier_c_sample_verified(p2) is False
        # 3) verify_same_person=True → True
        p3 = tmp_path / "body_3.jpg"
        p3.with_suffix(".json").write_text(json.dumps({"verify_same_person": True}), encoding="utf-8")
        assert IdentityLibrary._tier_c_sample_verified(p3) is True
        # 4) verify_same_person=False → False
        p4 = tmp_path / "body_4.jpg"
        p4.with_suffix(".json").write_text(json.dumps({"verify_same_person": False}), encoding="utf-8")
        assert IdentityLibrary._tier_c_sample_verified(p4) is False

    def test_pick_body_files_trusted_only_picks_verified(self, lib: IdentityLibrary):
        person_dir = lib.persons_dir / "person-x"
        (person_dir / "tier_a").mkdir(parents=True)
        # tier_c 按相机子目录隔离:样本写在 tier_c/cam_X/,选样传 cam_id="cam_X"
        cam_c_dir = person_dir / "tier_c" / "cam_X"
        cam_c_dir.mkdir(parents=True)
        # tier_a 权威参考(_pick 只 glob 文件名, 不读图 → touch 即可)
        (person_dir / "tier_a" / "body_a1.jpg").touch()
        # tier_c 三张, 仅一张 verify_same_person=True
        for name, verify in [("body_c1.jpg", True), ("body_c2.jpg", False), ("body_c3.jpg", None)]:
            (cam_c_dir / name).touch()
            if verify is not None:
                (cam_c_dir / name).with_suffix(".json").write_text(
                    json.dumps({"verify_same_person": verify}), encoding="utf-8"
                )
        a_picked, c_picked = lib._pick_body_files(person_dir, body_n=3, cam_id="cam_X")
        # trusted: 只回喂校验通过的那张, 留 1 槽
        assert [p.name for p in c_picked] == ["body_c1.jpg"]
        assert len(a_picked) >= 1


class TestCacheLockThreadSafety:
    """HIGH 修复回归:_tier_a_phash_cache / _composite_cache / _tier_nd_cache 跨 OS
    线程并发访问加锁后,不再 RuntimeError(dict changed size during iteration)。

    复现:tier_c worker 的 to_thread(tier_c_phash_check 写 inner dict) × 推理线程
    (get_gallery GC 迭代+pop) × API 线程(_invalidate_person_cache pop)并发同 dict。
    invalidate 不断清缓存逼 phash_check 反复重填(产生写),放大竞态。加锁前大概率
    抛 RuntimeError;加锁后串行、零异常。
    """

    def test_concurrent_phash_gallery_invalidate_no_crash(self, lib: IdentityLibrary):
        import threading
        import time as _time

        pid = "22222222-2222-4222-8222-222222222222"
        lib.add_tier_a_samples_batch(
            pid, _make_samples(6, with_face=True), "rs-ts", name="x"
        )
        crop = _make_crop(999)
        errors: list[BaseException] = []
        stop = threading.Event()

        def guard(fn):
            def run():
                try:
                    while not stop.is_set():
                        fn()
                except BaseException as e:  # noqa: BLE001
                    errors.append(e)
            return run

        threads = [
            *[threading.Thread(target=guard(lambda: lib.tier_c_phash_check(pid, crop)))
              for _ in range(4)],
            *[threading.Thread(target=guard(lambda: lib._invalidate_person_cache(pid)))
              for _ in range(2)],
            threading.Thread(target=guard(lambda: lib.get_gallery_composites_for_omni([pid]))),
        ]
        for t in threads:
            t.start()
        _time.sleep(0.4)
        stop.set()
        for t in threads:
            t.join(timeout=5)

        assert not errors, f"并发访问缓存抛异常(加锁应消除): {errors[:3]!r}"


class TestTierCReidCosObserve:
    """tier_c_reid_cos_observe:只观测、不拦截。vs tier_a 质心 + vs tier_c 逐张最大。"""

    @staticmethod
    def _axis(idx: int, dim: int = 128) -> np.ndarray:
        """轴对齐单位向量,便于断言确定的余弦值。"""
        v = np.zeros(dim, dtype=np.float32)
        v[idx] = 1.0
        return v

    def test_none_emb_returns_none_none(self, lib: IdentityLibrary):
        pid = "12121212-1212-4121-8121-121212121212"
        _write_npy(lib.persons_dir / pid / "tier_a" / "body_001.npy", self._axis(0))
        # 即便有参考样本,new_emb=None 也直接 (None, None)
        assert lib.tier_c_reid_cos_observe(pid, None) == (None, None)

    def test_no_tier_c_yields_cos_c_none(self, lib: IdentityLibrary):
        pid = "13131313-1313-4131-8131-131313131313"
        _write_npy(lib.persons_dir / pid / "tier_a" / "body_001.npy", self._axis(0))
        cos_a, cos_c = lib.tier_c_reid_cos_observe(pid, self._axis(0))
        assert cos_a == pytest.approx(1.0, abs=1e-6)  # 与质心(=e0)同向
        assert cos_c is None                          # 无 tier_c 样本

    def test_known_vectors_cos_a_centroid_cos_c_max(self, lib: IdentityLibrary):
        pid = "14141414-1414-4141-8141-141414141414"
        # tier_a 单样本 → 质心 = e0
        _write_npy(lib.persons_dir / pid / "tier_a" / "body_001.npy", self._axis(0))
        # tier_c 两张:e0 / e1
        _write_npy(lib.persons_dir / pid / "tier_c" / "body_001.npy", self._axis(0))
        _write_npy(lib.persons_dir / pid / "tier_c" / "body_002.npy", self._axis(1))
        # query = e1 → cos_a = <e1,e0> = 0;cos_c = max(<e1,e0>, <e1,e1>) = 1
        cos_a, cos_c = lib.tier_c_reid_cos_observe(pid, self._axis(1))
        assert cos_a == pytest.approx(0.0, abs=1e-6)
        assert cos_c == pytest.approx(1.0, abs=1e-6)

    def test_no_tier_a_emb_yields_cos_a_none(self, lib: IdentityLibrary):
        pid = "15151515-1515-4151-8151-151515151515"
        # 无 tier_a .npy → 质心 None;tier_c 有 emb
        _write_npy(lib.persons_dir / pid / "tier_c" / "body_001.npy", self._axis(0))
        cos_a, cos_c = lib.tier_c_reid_cos_observe(pid, self._axis(0))
        assert cos_a is None
        assert cos_c == pytest.approx(1.0, abs=1e-6)


class TestJpgPngBackwardCompat:
    """落盘改 PNG 后, 历史库的 .jpg/.jpeg 仍能被读到, 且新写入 .png 不与老 jpg 撞号。"""

    def test_list_crop_files_mixes_jpg_jpeg_png(self, lib: IdentityLibrary):
        from miloco.perception.engine.identity.library import _list_crop_files

        pid = "c0000000-0000-4000-8000-0000000000c1"
        tier_a = lib.persons_dir / pid / "tier_a"
        tier_a.mkdir(parents=True)
        # 历史库可能是 jpg/jpeg, 新写入是 png
        for name in ("body_001.jpg", "body_002.jpeg", "body_003.png"):
            cv2.imwrite(str(tier_a / name), _make_crop())
        # .npy/.json sidecar 不应被当成图列进来
        (tier_a / "body_001.npy").touch()
        (tier_a / "body_001.json").touch()

        got = sorted(p.name for p in _list_crop_files(tier_a, "body"))
        assert got == ["body_001.jpg", "body_002.jpeg", "body_003.png"]

    def test_new_write_does_not_collide_with_legacy_jpg(self, lib: IdentityLibrary):
        from miloco.perception.engine.identity.library import _list_crop_files

        pid = "c0000000-0000-4000-8000-0000000000c2"
        tier_a = lib.persons_dir / pid / "tier_a"
        tier_a.mkdir(parents=True)
        # 历史遗留两张 jpg(占用 001/002)
        for name in ("body_001.jpg", "body_002.jpg"):
            cv2.imwrite(str(tier_a / name), _make_crop())

        # 新写入应落 body_003.png(不覆盖老 jpg)
        assert lib.add_tier_a_sample(pid, _make_crop(), source="new") is True
        files = sorted(p.name for p in _list_crop_files(tier_a, "body"))
        assert files == ["body_001.jpg", "body_002.jpg", "body_003.png"]

    def test_gallery_and_count_see_legacy_jpg(self, lib: IdentityLibrary):
        pid = "c0000000-0000-4000-8000-0000000000c3"
        tier_a = lib.persons_dir / pid / "tier_a"
        tier_a.mkdir(parents=True)
        cv2.imwrite(str(tier_a / "body_001.jpg"), _make_crop())
        cv2.imwrite(str(tier_a / "face_001.jpg"), _make_crop())

        ref = next(r for r in lib.list_persons() if r.person_id == pid)
        assert ref.num_tier_a_body == 1
        assert ref.has_tier_a is True
        # gallery 选样能挑到老 jpg body
        body_a, _ = lib._pick_body_files(lib.persons_dir / pid, body_n=3, cam_id="cam0")
        assert [p.name for p in body_a] == ["body_001.jpg"]


class TestTierCClear:
    """tier_c 闲时定期清原语:clear_tier_c / tier_c_pool_latest_mtime / list_person_ids。"""

    _PID = "d0000000-0000-4000-8000-0000000000d1"

    def _seed(self, lib: IdentityLibrary, cam: str, n: int, base: int) -> None:
        lib.add_tier_a_sample(self._PID, _make_crop(seed=base), source="seed")
        for i in range(n):
            lib.add_tier_c_sample(
                self._PID, _make_crop(seed=base + 1 + i),
                captured_at=1_700_000_000.0 + base + i,
                reid_embedding=_make_unit_emb(base + i), cam_id=cam,
            )

    def test_clear_removes_cam_pool_and_isolates_others(self, lib: IdentityLibrary):
        self._seed(lib, "camA", 2, base=0)
        self._seed(lib, "camB", 1, base=50)
        from miloco.perception.engine.identity.library import _list_crop_files
        cam_a = lib.persons_dir / self._PID / "tier_c" / "camA"
        cam_b = lib.persons_dir / self._PID / "tier_c" / "camB"
        tier_a = lib.persons_dir / self._PID / "tier_a"
        assert len(_list_crop_files(cam_a, "body")) == 2
        # camA 每张应有同 stem 的 .npy/.json
        assert len(list(cam_a.glob("body_*.npy"))) == 2
        assert len(list(cam_a.glob("body_*.json"))) == 2

        n = lib.clear_tier_c("camA", self._PID)
        assert n == 2
        # camA 整池清空(图 + sidecar + npy)
        assert _list_crop_files(cam_a, "body") == []
        assert list(cam_a.glob("body_*.npy")) == []
        assert list(cam_a.glob("body_*.json")) == []
        # camB 不受影响;tier_a 不动
        assert len(_list_crop_files(cam_b, "body")) == 1
        assert len(_list_crop_files(tier_a, "body")) >= 1

    def test_clear_nonexistent_returns_zero(self, lib: IdentityLibrary):
        self._seed(lib, "camA", 1, base=0)
        assert lib.clear_tier_c("camZ", self._PID) == 0
        assert lib.clear_tier_c("camA", "no-such-person") == 0

    def test_pool_latest_mtime_and_isolation(self, lib: IdentityLibrary):
        assert lib.tier_c_pool_latest_mtime("camA") is None  # 空库
        self._seed(lib, "camA", 2, base=0)
        self._seed(lib, "camB", 1, base=50)
        import time as _t
        m_a = lib.tier_c_pool_latest_mtime("camA")
        m_b = lib.tier_c_pool_latest_mtime("camB")
        assert m_a is not None and m_b is not None
        assert m_a <= _t.time() + 1  # 是真实文件 mtime(秒)
        # 清空 camA 后该相机 mtime 归 None,camB 仍在
        lib.clear_tier_c("camA", self._PID)
        assert lib.tier_c_pool_latest_mtime("camA") is None
        assert lib.tier_c_pool_latest_mtime("camB") is not None

    def test_list_person_ids(self, lib: IdentityLibrary):
        assert lib.list_person_ids() == []
        self._seed(lib, "camA", 1, base=0)
        assert self._PID in lib.list_person_ids()
