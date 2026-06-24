"""Gallery 人脸样本选样的正脸优先（方案 A）。

`_pick_face_files` 复用注册口径（face crop w/h ∈ [0.70, 0.80) 视为正脸），把一张正脸
排到第一（= composite 最左）；无正脸样本则回退文件名序。判 wh 直接读 face_*.jpg 尺寸
（落盘保形，与注册 _face_wh_ratio 同口径）。
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
from miloco.perception.engine.identity.library import IdentityLibrary
from miloco.perception.engine.identity.registration_filter import (
    DEFAULT_FRONTAL_WH_MAX,
    DEFAULT_FRONTAL_WH_MIN,
)


@pytest.fixture
def lib(tmp_path: Path) -> IdentityLibrary:
    return IdentityLibrary(tmp_path / "identity_lib")


def _write_face(person_dir: Path, idx: int, w: int, h: int) -> Path:
    """在 tier_a 写一张指定 w×h 的 face_<idx>.jpg（内容随意, 只看尺寸）。"""
    d = person_dir / "tier_a"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"face_{idx:03d}.jpg"
    cv2.imwrite(str(p), np.full((h, w, 3), 128, dtype=np.uint8))
    return p


# 正脸带内/外的具体尺寸（h=100 基准）
_FRONTAL_WH = (DEFAULT_FRONTAL_WH_MIN + DEFAULT_FRONTAL_WH_MAX) / 2  # 0.75 → 75×100
_SIDE_WH = DEFAULT_FRONTAL_WH_MIN - 0.10                            # 0.60 → 侧脸
_UP_WH = DEFAULT_FRONTAL_WH_MAX + 0.10                              # 0.90 → 抬头


class TestPickFaceFrontalFirst:
    def test_frontal_moved_to_first(self, lib):
        """face_001 侧脸、face_003 正脸 → 正脸排第 0 位。"""
        pdir = lib.persons_dir / "p1"
        _write_face(pdir, 1, int(_SIDE_WH * 100), 100)     # 侧脸
        _write_face(pdir, 2, int(_SIDE_WH * 100), 100)     # 侧脸
        face_003 = _write_face(pdir, 3, int(_FRONTAL_WH * 100), 100)  # 正脸
        picked = lib._pick_face_files(pdir, face_n=3)
        assert picked[0] == face_003
        assert len(picked) == 3

    def test_frontal_outside_topn_pulled_in(self, lib):
        """正脸是 face_004、face_n=3（本会被 [:3] 截掉）→ 仍被拉进结果且置首。"""
        pdir = lib.persons_dir / "p2"
        for i in (1, 2, 3):
            _write_face(pdir, i, int(_SIDE_WH * 100), 100)  # 侧脸
        face_004 = _write_face(pdir, 4, int(_FRONTAL_WH * 100), 100)  # 正脸
        _write_face(pdir, 5, int(_SIDE_WH * 100), 100)
        picked = lib._pick_face_files(pdir, face_n=3)
        assert picked[0] == face_004
        assert len(picked) == 3
        assert face_004 in picked

    def test_no_frontal_falls_back_to_filename_order(self, lib):
        """全是侧脸/抬头（无正脸带）→ 回退文件名序（== 旧行为）。"""
        pdir = lib.persons_dir / "p3"
        f1 = _write_face(pdir, 1, int(_SIDE_WH * 100), 100)
        f2 = _write_face(pdir, 2, int(_UP_WH * 100), 100)
        f3 = _write_face(pdir, 3, int(_SIDE_WH * 100), 100)
        picked = lib._pick_face_files(pdir, face_n=3)
        assert picked == [f1, f2, f3]

    def test_multiple_frontal_takes_earliest_by_filename(self, lib):
        """多张正脸 → 取文件名序最早那张置首。"""
        pdir = lib.persons_dir / "p4"
        _write_face(pdir, 1, int(_SIDE_WH * 100), 100)
        face_002 = _write_face(pdir, 2, int(_FRONTAL_WH * 100), 100)  # 第一张正脸
        _write_face(pdir, 3, int(_FRONTAL_WH * 100), 100)            # 第二张正脸
        picked = lib._pick_face_files(pdir, face_n=3)
        assert picked[0] == face_002

    def test_boundaries_excluded(self, lib):
        """边界: w/h == MIN 含、== MAX 不含（[MIN, MAX) 半开区间）。"""
        pdir = lib.persons_dir / "p5"
        # face_001 = 上界(不含, 非正脸), face_002 = 下界(含, 正脸)
        _write_face(pdir, 1, int(DEFAULT_FRONTAL_WH_MAX * 100), 100)
        face_002 = _write_face(pdir, 2, int(DEFAULT_FRONTAL_WH_MIN * 100), 100)
        picked = lib._pick_face_files(pdir, face_n=3)
        assert picked[0] == face_002

    def test_respects_face_n_and_empty(self, lib):
        pdir = lib.persons_dir / "p6"
        for i in (1, 2, 3, 4):
            _write_face(pdir, i, int(_SIDE_WH * 100), 100)
        assert len(lib._pick_face_files(pdir, face_n=2)) == 2
        # 空目录 / 无 tier_a
        assert lib._pick_face_files(lib.persons_dir / "nobody", face_n=3) == []

    def test_face_n_zero_returns_empty(self, lib):
        """face_n=0(不要人脸)→ 返回空; 正脸前插不得误返 1 张(与旧 [:0] 切片同义)。"""
        pdir = lib.persons_dir / "p8"
        _write_face(pdir, 1, int(_FRONTAL_WH * 100), 100)  # 有正脸样本也不返
        _write_face(pdir, 2, int(_SIDE_WH * 100), 100)
        assert lib._pick_face_files(pdir, face_n=0) == []

    def test_gc_clears_frontal_and_drift_ref_caches(self, lib):
        """死人 GC 兜底也清 _frontal_face_cache / _drift_ref_cache(与 3 个兄弟缓存对齐)。

        防"改了 _invalidate 这一处、漏了平行兜底 GC"——若将来出现不经 _invalidate 的移除路径,
        这两个缓存的死人条目也能被 get_gallery_composites_for_omni 的 GC 清掉。
        """
        lib._frontal_face_cache["ghost"] = ((), None)
        lib._drift_ref_cache[("ghost", "cam-x")] = (((), ()), (None, 0, "none"))
        # live_set 为空(person_ids=[]) → GC 清掉所有不在册的条目
        lib.get_gallery_composites_for_omni(person_ids=[])
        assert "ghost" not in lib._frontal_face_cache
        assert ("ghost", "cam-x") not in lib._drift_ref_cache

    def test_wh_ratio_helper(self, lib):
        pdir = lib.persons_dir / "p7"
        p = _write_face(pdir, 1, 75, 100)
        assert abs(IdentityLibrary._face_wh_ratio_of(p) - 0.75) < 1e-6
        assert IdentityLibrary._face_wh_ratio_of(pdir / "tier_a" / "nope.jpg") is None

    def test_frontal_pick_memoized(self, lib, monkeypatch):
        """正脸优选按 face 指纹 memo 化: 文件不变的重复调用不再 imread; 文件变化才重算。

        _pick_face_files 在 composite L1 命中前被无条件调用——不缓存就每窗解码全部 face,
        把 imread 重引回热路径(本回归保护这一点)。
        """
        calls = {"n": 0}
        orig = IdentityLibrary._face_wh_ratio_of

        def counting(face_path):
            calls["n"] += 1
            return orig(face_path)

        monkeypatch.setattr(IdentityLibrary, "_face_wh_ratio_of", staticmethod(counting))

        pdir = lib.persons_dir / "pm"
        _write_face(pdir, 1, int(_SIDE_WH * 100), 100)
        _write_face(pdir, 2, int(_FRONTAL_WH * 100), 100)

        lib._pick_face_files(pdir, face_n=3)
        first = calls["n"]
        assert first > 0                      # 首次扫描有 imread
        lib._pick_face_files(pdir, face_n=3)
        assert calls["n"] == first            # 第二次命中缓存, 零额外 imread

        # 新增 face → 指纹变 → 重算(再 imread)
        _write_face(pdir, 3, int(_FRONTAL_WH * 100), 100)
        lib._pick_face_files(pdir, face_n=3)
        assert calls["n"] > first

    def test_no_frontal_also_memoized(self, lib, monkeypatch):
        """没正脸的成员同样 memo 化(缓存 None), 不再每次全量扫描。"""
        calls = {"n": 0}
        orig = IdentityLibrary._face_wh_ratio_of

        def counting(face_path):
            calls["n"] += 1
            return orig(face_path)

        monkeypatch.setattr(IdentityLibrary, "_face_wh_ratio_of", staticmethod(counting))

        pdir = lib.persons_dir / "pn"
        for i in (1, 2, 3):
            _write_face(pdir, i, int(_SIDE_WH * 100), 100)  # 全侧脸, 无正脸
        assert lib._pick_face_files(pdir, face_n=3)  # 回退原序
        first = calls["n"]
        assert first == 3                     # 首次全扫(找不到正脸)
        lib._pick_face_files(pdir, face_n=3)
        assert calls["n"] == first            # 命中缓存(None), 不再全扫
