"""``IdentityLibrary.add_face_only_sample`` 契约单测。

该方法绕过 ``add_tier_a_sample`` 的"必须传 body_crop"约束, 为 web 端"用户只勾 face"
批量注册路径写一张 ``face_*.jpg`` + sidecar。原是 router._write_face_only(反插 library
私有 _next_index / _write_sidecar), 已收编为 library public 方法。此测试锁住该契约。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from miloco.perception.engine.identity.library import IdentityLibrary

_PID = "22222222-2222-4222-8222-222222222222"


def _face_crop(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 255, size=(64, 64, 3), dtype=np.uint8)


@pytest.fixture
def lib(tmp_path: Path) -> IdentityLibrary:
    return IdentityLibrary(tmp_path / "identity_lib")


class TestFilenameWhitelist:
    """read_tier_sample 的文件名白名单:落盘 jpg→png 后必须放行 png(及历史 jpg/jpeg),仍挡穿越。"""

    def test_accepts_png_jpg_jpeg_rejects_traversal(self):
        from miloco.person.router import _FILENAME_SAFE

        for ok in ("body_001.png", "face_001.png", "body_1700000000000.png",
                   "body_001.jpg", "face_002.jpeg"):
            assert _FILENAME_SAFE.match(ok), f"应放行 {ok}"
        for bad in ("../etc/passwd", "body_001.gif", "body_001.png.exe",
                    "x_001.png", "body_001.json", "body_001.npy"):
            assert not _FILENAME_SAFE.match(bad), f"应拒绝 {bad}"


class TestWriteFaceOnly:
    def test_happy_path_writes_image_and_sidecar(self, lib: IdentityLibrary):
        # ``_next_index`` 从 1 起编(空列表 max=0,返回 max+1=1),与 library
        # body 路径(``add_tier_a_sample``)对齐。
        ok = lib.add_face_only_sample(_PID, _face_crop(0), source="user_upload")
        assert ok is True
        tier_a = lib.persons_dir / _PID / "tier_a"
        assert (tier_a / "face_001.png").exists()
        sidecar = json.loads((tier_a / "face_001.json").read_text(encoding="utf-8"))
        assert sidecar["kind"] == "face"
        assert sidecar["tier"] == "a"
        assert sidecar["source"] == "user_upload"

    def test_index_increments_across_writes(self, lib: IdentityLibrary):
        for i in range(3):
            assert lib.add_face_only_sample(_PID, _face_crop(i), source="t") is True
        tier_a = lib.persons_dir / _PID / "tier_a"
        names = sorted(p.name for p in tier_a.glob("face_*.png"))
        assert names == ["face_001.png", "face_002.png", "face_003.png"]

    def test_capacity_limit_blocks_write(self, lib: IdentityLibrary):
        cap = lib.tier_a_max // 2
        for i in range(cap):
            assert lib.add_face_only_sample(_PID, _face_crop(i), source="t") is True
        assert lib.add_face_only_sample(_PID, _face_crop(cap), source="t") is False
        tier_a = lib.persons_dir / _PID / "tier_a"
        assert len(list(tier_a.glob("face_*.png"))) == cap

    def test_does_not_write_phantom_body(self, lib: IdentityLibrary):
        """关键差异点:用户只勾 face 的场景不应写出冗余 body_* 图。"""
        lib.add_face_only_sample(_PID, _face_crop(0), source="t")
        tier_a = lib.persons_dir / _PID / "tier_a"
        assert list(tier_a.glob("body_*.png")) == []
        assert list(tier_a.glob("body_*.jpg")) == []
