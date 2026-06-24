"""PerceptionEngine tier_c 闲时定期清判定链单测。

用 ``__new__`` 造轻量 stub(绕开重 __init__),只注入 tick 触碰的属性,
覆盖:默认无条件清 / 时间窗 / 幂等 / (require_absence 模式)mtime 静默 / gate 静默 / live 检测 各分支。
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

import numpy as np
import pytest
from miloco.perception.engine import api as api_mod
from miloco.perception.engine.api import PerceptionEngine
from miloco.perception.engine.config import TierCClearConfig


@dataclass
class _Det:
    class_id: int
    confidence: float


class _FakeDetector:
    def __init__(self, dets):
        self._dets = dets

    def detect(self, frame):
        return self._dets


class _FakeSvc:
    def __init__(self, dets):
        self._detector = _FakeDetector(dets)


class _FakeLib:
    """记录 clear 调用 + 可控 mtime / person 列表。"""

    def __init__(self, latest_mtime, person_ids=("p1",)):
        self._latest = latest_mtime
        self._pids = list(person_ids)
        self.cleared: list[tuple[str, str]] = []

    def tier_c_pool_latest_mtime(self, cam_id):
        return self._latest

    def list_person_ids(self):
        return list(self._pids)

    def clear_tier_c(self, cam_id, person_id):
        self.cleared.append((cam_id, person_id))
        return 1


def _make_engine(lib, *, frame, dets, cfg=None, gate_ts=None):
    eng = PerceptionEngine.__new__(PerceptionEngine)
    eng._identity_lib = lib
    eng._tracking_services = {"camA": _FakeSvc(dets)}
    eng._gate_last_visual_pass_ts = gate_ts or {}
    eng._tierc_last_clear_date = {}
    eng._tierc_frame_provider = (lambda did: frame)

    class _Cfg:
        identity_engine = type("IE", (), {"tierc_clear": cfg or TierCClearConfig()})()

    eng._config = _Cfg()
    return eng


def _force_hour(monkeypatch, hour: int):
    fixed = _dt.datetime(2026, 6, 15, hour, 30, 0)

    class _FakeDT(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(api_mod, "datetime", _FakeDT)


_FRAME = np.zeros((64, 64, 3), dtype=np.uint8)
_NO_PERSON: list = []
_PERSON = [_Det(class_id=0, confidence=0.9)]   # CLASS_HUMAN=0


@pytest.mark.asyncio
async def test_default_unconditional_clears(monkeypatch):
    """默认 require_absence=False: 窗内到点直接清, 不判在场。"""
    _force_hour(monkeypatch, 3)  # 窗内
    lib = _FakeLib(latest_mtime=1.0)
    cfg = TierCClearConfig()
    eng = _make_engine(lib, frame=_FRAME, dets=_NO_PERSON, cfg=cfg)
    await eng._tierc_clear_tick(cfg)
    assert lib.cleared == [("camA", "p1")]
    assert eng._tierc_last_clear_date["camA"] == "2026-06-15"


@pytest.mark.asyncio
async def test_unconditional_clears_despite_person(monkeypatch):
    """默认模式: 即便有人在场 / gate 刚 pass / 池刚写入(三项 funnel 条件全不满足),仍照清。"""
    import time
    _force_hour(monkeypatch, 3)
    lib = _FakeLib(latest_mtime=time.time())  # 刚写入 → 非静默
    cfg = TierCClearConfig()  # require_absence 默认 False
    eng = _make_engine(lib, frame=_FRAME, dets=_PERSON, cfg=cfg,
                       gate_ts={"camA": time.monotonic()})  # gate 刚 pass + 检测到人
    await eng._tierc_clear_tick(cfg)
    assert lib.cleared == [("camA", "p1")]


@pytest.mark.asyncio
async def test_skip_out_of_window(monkeypatch):
    _force_hour(monkeypatch, 12)  # 窗外
    lib = _FakeLib(latest_mtime=1.0)
    cfg = TierCClearConfig()
    eng = _make_engine(lib, frame=_FRAME, dets=_NO_PERSON, cfg=cfg)
    await eng._tierc_clear_tick(cfg)
    assert lib.cleared == []


@pytest.mark.asyncio
async def test_skip_pool_not_quiet(monkeypatch):
    _force_hour(monkeypatch, 3)
    import time
    lib = _FakeLib(latest_mtime=time.time())  # 刚写入 → 非静默
    cfg = TierCClearConfig(require_absence=True)
    eng = _make_engine(lib, frame=_FRAME, dets=_NO_PERSON, cfg=cfg)
    await eng._tierc_clear_tick(cfg)
    assert lib.cleared == []


@pytest.mark.asyncio
async def test_skip_gate_not_quiet(monkeypatch):
    _force_hour(monkeypatch, 3)
    import time
    lib = _FakeLib(latest_mtime=1.0)
    cfg = TierCClearConfig(require_absence=True)
    eng = _make_engine(lib, frame=_FRAME, dets=_NO_PERSON, cfg=cfg,
                       gate_ts={"camA": time.monotonic()})  # 刚 pass → 非静默
    await eng._tierc_clear_tick(cfg)
    assert lib.cleared == []


@pytest.mark.asyncio
async def test_skip_person_detected(monkeypatch):
    _force_hour(monkeypatch, 3)
    lib = _FakeLib(latest_mtime=1.0)
    cfg = TierCClearConfig(require_absence=True)
    eng = _make_engine(lib, frame=_FRAME, dets=_PERSON, cfg=cfg)  # 检测到人
    await eng._tierc_clear_tick(cfg)
    assert lib.cleared == []


@pytest.mark.asyncio
async def test_low_conf_person_not_blocking(monkeypatch):
    """检测到人但 conf < 阈值 → 视作无人, 照清。"""
    _force_hour(monkeypatch, 3)
    lib = _FakeLib(latest_mtime=1.0)
    cfg = TierCClearConfig(require_absence=True, detect_person_conf=0.8)
    eng = _make_engine(lib, frame=_FRAME, dets=[_Det(0, 0.6)], cfg=cfg)
    await eng._tierc_clear_tick(cfg)
    assert lib.cleared == [("camA", "p1")]


@pytest.mark.asyncio
async def test_idempotent_same_night(monkeypatch):
    _force_hour(monkeypatch, 3)
    lib = _FakeLib(latest_mtime=1.0)
    cfg = TierCClearConfig()
    eng = _make_engine(lib, frame=_FRAME, dets=_NO_PERSON, cfg=cfg)
    await eng._tierc_clear_tick(cfg)
    await eng._tierc_clear_tick(cfg)  # 同晚第二次
    assert lib.cleared == [("camA", "p1")]  # 只清一次


@pytest.mark.asyncio
async def test_empty_pool_marks_done_no_clear(monkeypatch):
    """池为空(mtime None)→ 标记完成、不清、不跑检测。"""
    _force_hour(monkeypatch, 3)
    lib = _FakeLib(latest_mtime=None)
    cfg = TierCClearConfig()
    eng = _make_engine(lib, frame=_FRAME, dets=_PERSON, cfg=cfg)  # 即便有人也不该清(无可清)
    await eng._tierc_clear_tick(cfg)
    assert lib.cleared == []
    assert eng._tierc_last_clear_date["camA"] == "2026-06-15"


@pytest.mark.asyncio
async def test_no_frame_conservative_no_clear(monkeypatch):
    """取帧失败(frame=None)→ 保守视作有人, 不清。"""
    _force_hour(monkeypatch, 3)
    lib = _FakeLib(latest_mtime=1.0)
    cfg = TierCClearConfig(require_absence=True)
    eng = _make_engine(lib, frame=None, dets=_NO_PERSON, cfg=cfg)
    await eng._tierc_clear_tick(cfg)
    assert lib.cleared == []


@pytest.mark.asyncio
@pytest.mark.parametrize("hour,should_clear", [(23, True), (1, True), (5, False), (12, False)])
async def test_cross_midnight_window(monkeypatch, hour, should_clear):
    """跨午夜窗 23-2: 23/1 点在窗内清, 5/12 点窗外不清。"""
    _force_hour(monkeypatch, hour)
    lib = _FakeLib(latest_mtime=1.0)
    cfg = TierCClearConfig(window_start_hour=23, window_end_hour=2)
    eng = _make_engine(lib, frame=_FRAME, dets=_NO_PERSON, cfg=cfg)
    await eng._tierc_clear_tick(cfg)
    assert (lib.cleared == [("camA", "p1")]) is should_clear
