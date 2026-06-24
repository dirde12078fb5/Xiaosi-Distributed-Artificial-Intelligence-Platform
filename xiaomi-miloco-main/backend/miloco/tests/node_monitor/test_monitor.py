import time

import pytest
from miloco.node_monitor.monitor import NodeMonitor, get_monitor
from miloco.node_monitor.node_state import Lifecycle, NodeKind


@pytest.fixture(autouse=True)
def _reset_monitor():
    NodeMonitor._reset()
    yield
    NodeMonitor._reset()


def _make_monitor() -> NodeMonitor:
    return get_monitor()


class TestRegister:
    def test_register_and_snapshot(self):
        mon = _make_monitor()
        mon.register("cam", NodeKind.SOURCE, watchdog_s=3)
        snap = mon.snapshot()
        assert len(snap) == 1
        assert snap[0]["name"] == "cam"
        assert snap[0]["lifecycle"] == "registered"

    def test_duplicate_register_ignored(self):
        mon = _make_monitor()
        mon.register("cam", NodeKind.SOURCE, watchdog_s=3)
        mon.register("cam", NodeKind.WINDOW, watchdog_s=99)
        assert mon.snapshot_one("cam")["kind"] == "source"


class TestTrackConstruction:
    @pytest.mark.asyncio
    async def test_construction_happy(self):
        mon = _make_monitor()
        mon.register("svc", NodeKind.SERVICE)
        async with mon.track_async("svc", "init"):
            pass
        snap = mon.snapshot_one("svc")
        assert snap["lifecycle"] == "ready"

    @pytest.mark.asyncio
    async def test_construction_failure(self):
        mon = _make_monitor()
        mon.register("svc", NodeKind.SERVICE)
        with pytest.raises(RuntimeError, match="boom"):
            async with mon.track_async("svc", "init"):
                raise RuntimeError("boom")
        snap = mon.snapshot_one("svc")
        assert snap["lifecycle"] == "failed"
        assert "boom" in snap["last_error"]

    def test_construction_sync_happy(self):
        mon = _make_monitor()
        mon.register("col", NodeKind.WINDOW, watchdog_s=5)
        with mon.track("col", "init"):
            pass
        assert mon.snapshot_one("col")["lifecycle"] == "ready"

    def test_construction_sync_failure(self):
        mon = _make_monitor()
        mon.register("col", NodeKind.WINDOW, watchdog_s=5)
        with pytest.raises(ValueError):
            with mon.track("col", "init"):
                raise ValueError("oops")
        assert mon.snapshot_one("col")["lifecycle"] == "failed"


class TestTrackRunning:
    @pytest.mark.asyncio
    async def test_running_success(self):
        mon = _make_monitor()
        mon.register("proc", NodeKind.WINDOW, watchdog_s=10)
        async with mon.track_async("proc", "init"):
            pass

        async with mon.track_async("proc", "run") as h:
            h.add_window_ms(100)

        snap = mon.snapshot_one("proc")
        assert snap["lifecycle"] == "running_end"
        assert snap["success_count"] == 1

    @pytest.mark.asyncio
    async def test_running_failure_does_not_change_lifecycle(self):
        mon = _make_monitor()
        mon.register("proc", NodeKind.WINDOW, watchdog_s=10)
        async with mon.track_async("proc", "init"):
            pass
        # First success transitions READY → RUNNING
        async with mon.track_async("proc", "run"):
            pass
        assert mon.snapshot_one("proc")["lifecycle"] == "running_end"

        with pytest.raises(RuntimeError):
            async with mon.track_async("proc", "run"):
                raise RuntimeError("transient")

        snap = mon.snapshot_one("proc")
        assert snap["lifecycle"] == "running_end"
        assert snap["failure_count"] == 1
        assert "transient" in snap["last_error"]

    def test_running_sync(self):
        mon = _make_monitor()
        mon.register("col", NodeKind.WINDOW, watchdog_s=5)
        with mon.track("col", "init"):
            pass
        with mon.track("col", "run") as h:
            h.add_window_ms(50)
        snap = mon.snapshot_one("col")
        assert snap["lifecycle"] == "running_end"
        assert snap["success_count"] == 1

    @pytest.mark.asyncio
    async def test_failure_path_preserves_input_count(self):
        """rule 模式:_dispatch_event 抛异常时,h.add_input(1) 的累计不能被吞,
        否则 input_qps_60s 永远显示 0 即便 rule 实际在收事件,等同于
        '看不到 rule 收到任何东西',掩盖真实流量。output_n 由 caller 决定何时
        add_output(),抛异常前没调就是 0,保持原有 'add_output = 触发成功' 语义。"""
        mon = _make_monitor()
        mon.register("rule", NodeKind.EVENT, watchdog_s=60)
        async with mon.track_async("rule", "init"):
            pass

        with pytest.raises(RuntimeError):
            async with mon.track_async("rule", "update") as h:
                h.add_input(1)
                raise RuntimeError("dispatch failed")

        snap = mon.snapshot_one("rule")
        assert snap["input_qps_60s"] > 0
        assert snap["fire_qps_60s"] == 0
        assert snap["failure_count"] == 1
        assert "dispatch failed" in snap["last_error"]

    @pytest.mark.asyncio
    async def test_skip_excludes_track_from_rolling(self):
        """skip() 让本次 track 不进 rolling:fps/p95/RTF 都不被空轮询污染,
        但 lifecycle 仍正常转 RUNNING_END(下一次 track 能正常 enter)。"""
        mon = _make_monitor()
        mon.register("proc", NodeKind.WINDOW, watchdog_s=10)
        async with mon.track_async("proc", "init"):
            pass

        # 50 个 "empty 轮询" (skip) + 1 个 "real 工作"
        for _ in range(50):
            async with mon.track_async("proc", "realtime") as h:
                h.skip_rolling()

        async with mon.track_async("proc", "realtime") as h:
            # 真实 batch:模拟 500ms latency + 5000ms window
            h.add_window_ms(5000)
            time.sleep(0.001)  # 模拟一点 latency,让 p95 有 sample

        snap = mon.snapshot_one("proc")
        assert snap["lifecycle"] == "running_end"
        # 不修复前 success_count=51,p95 落到 skip 的 ~0ms;修复后 success_count=1
        assert snap["success_count"] == 1
        assert snap["fps_60s"] > 0
        # rtf 只算真实那次 (latency / 5000ms),不被 skip 稀释成 51 个 latency / 5000ms
        assert snap["rtf_60s"] is not None and snap["rtf_60s"] < 0.01

    @pytest.mark.asyncio
    async def test_skip_does_not_affect_lifecycle_transition(self):
        """skip 不能跳过 lifecycle 转换,否则节点会留在 RUNNING_START 被 watchdog STALL。"""
        mon = _make_monitor()
        mon.register("proc", NodeKind.WINDOW, watchdog_s=10)
        async with mon.track_async("proc", "init"):
            pass
        async with mon.track_async("proc", "realtime") as h:
            h.skip_rolling()
        assert mon.snapshot_one("proc")["lifecycle"] == "running_end"

    @pytest.mark.asyncio
    async def test_stalled_track_finish_clears_stalled_since(self):
        """长 track 触发 STALL 后 track 自然结束:_exit_track 必须清 stalled_since,
        否则 to_dict 会一直报 stalled_since_s,看上去节点永远在 stall。"""
        mon = _make_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=2)
        # warm-up READY
        async with mon.track_async("eng", "init"):
            pass

        state = mon._states["eng"]
        events: list[tuple[str, str, str]] = []
        mon.emit_event = lambda name, etype, msg: events.append((name, etype, msg))

        async with mon.track_async("eng", "run"):
            # 进 track 后,模拟 watchdog 在 track 进行中把 lifecycle 改成 STALLED
            state.lifecycle = Lifecycle.STALLED
            state.stalled_since = time.monotonic() - 5

        snap = mon.snapshot_one("eng")
        assert snap["lifecycle"] == "running_end"
        assert state.stalled_since is None
        assert "stalled_since_s" not in snap
        recovered = [(n, e, m) for n, e, m in events if e == "RECOVERED"]
        assert len(recovered) == 1
        assert "track finished" in recovered[0][2]


class TestTrackHandle:
    @pytest.mark.asyncio
    async def test_add_input_output(self):
        mon = _make_monitor()
        mon.register("rule", NodeKind.EVENT, watchdog_s=60)
        async with mon.track_async("rule", "init"):
            pass

        async with mon.track_async("rule", "update") as h:
            h.add_input(1)
            h.add_output(1)

        snap = mon.snapshot_one("rule")
        assert snap["input_qps_60s"] > 0
        assert snap["fire_qps_60s"] > 0


class TestStageBreakdown:
    @pytest.mark.asyncio
    async def test_single_stage_omits_stages_field(self):
        mon = _make_monitor()
        mon.register("cam", NodeKind.SOURCE, watchdog_s=3)
        async with mon.track_async("cam", "decode_video"):
            pass
        async with mon.track_async("cam", "decode_video"):
            pass

        snap = mon.snapshot_one("cam")
        assert "stages" not in snap

    @pytest.mark.asyncio
    async def test_multi_stage_emits_separate_fps(self):
        mon = _make_monitor()
        mon.register("cam", NodeKind.SOURCE, watchdog_s=3)
        # warm-up: REGISTERED → READY,construction path 不进 stage_rollings
        async with mon.track_async("cam", "init"):
            pass
        # running path tracks: 1 video + 2 audio
        async with mon.track_async("cam", "decode_video"):
            pass
        async with mon.track_async("cam", "decode_audio"):
            pass
        async with mon.track_async("cam", "decode_audio"):
            pass

        snap = mon.snapshot_one("cam")
        assert "stages" in snap
        assert set(snap["stages"].keys()) == {"decode_video", "decode_audio"}
        assert snap["stages"]["decode_video"]["fps_60s"] > 0
        assert snap["stages"]["decode_audio"]["fps_60s"] > snap["stages"]["decode_video"]["fps_60s"]
        # 聚合 = video + audio 总和(都在同一秒 bucket 里,fps 取整后基本相等)
        assert snap["fps_60s"] >= snap["stages"]["decode_video"]["fps_60s"] + snap["stages"]["decode_audio"]["fps_60s"] - 0.01

    @pytest.mark.asyncio
    async def test_stage_kind_specific_fields(self):
        """WINDOW 节点的 stages 应该带 rtf_60s / p95_latency_ms"""
        mon = _make_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=30)
        async with mon.track_async("eng", "init"):  # warm-up
            pass
        async with mon.track_async("eng", "perceive") as h:
            h.add_window_ms(100)
        async with mon.track_async("eng", "on_demand") as h:
            h.add_window_ms(50)

        snap = mon.snapshot_one("eng")
        assert "stages" in snap
        for stage_name in ("perceive", "on_demand"):
            s = snap["stages"][stage_name]
            assert "fps_60s" in s
            assert "rtf_60s" in s
            assert "p95_latency_ms" in s


class TestSafetyI2:
    @pytest.mark.asyncio
    async def test_track_unknown_node_yields_dummy(self):
        """track() on unregistered node yields a handle (and warns once)."""
        mon = _make_monitor()
        async with mon.track_async("nonexistent", "run") as h:
            h.add_input(1)

    @pytest.mark.asyncio
    async def test_business_exception_propagates(self):
        """Business exception passes through even if monitor has issues."""
        mon = _make_monitor()
        mon.register("x", NodeKind.SOURCE, watchdog_s=3)
        async with mon.track_async("x", "init"):
            pass

        with pytest.raises(ValueError, match="biz"):
            async with mon.track_async("x", "run"):
                raise ValueError("biz")


class TestToDictPruning:
    def test_source_omits_rtf(self):
        mon = _make_monitor()
        mon.register("cam", NodeKind.SOURCE, watchdog_s=3)
        d = mon.snapshot_one("cam")
        assert "rtf_60s" not in d
        assert "input_qps_60s" not in d

    def test_event_omits_fps_rtf(self):
        mon = _make_monitor()
        mon.register("rule", NodeKind.EVENT, watchdog_s=60)
        d = mon.snapshot_one("rule")
        assert "fps_60s" not in d
        assert "rtf_60s" not in d
        assert "input_qps_60s" in d

    def test_service_omits_all_metrics(self):
        mon = _make_monitor()
        mon.register("svc", NodeKind.SERVICE)
        d = mon.snapshot_one("svc")
        assert "fps_60s" not in d
        assert "rtf_60s" not in d
        assert "success_count" not in d
        assert "input_qps_60s" not in d


class TestRollingFailureRate:
    def test_failure_rate_all_failures(self):
        from miloco.node_monitor.node_state import RollingCounter

        rc = RollingCounter()
        now = time.monotonic()
        for _ in range(10):
            rc.record_failure(now=now)
        assert rc.failure_rate() == 1.0

    def test_failure_rate_mixed(self):
        from miloco.node_monitor.node_state import RollingCounter

        rc = RollingCounter()
        now = time.monotonic()
        for _ in range(3):
            rc.record_failure(now=now)
        for _ in range(7):
            rc.record_success(latency_ms=1, now=now)
        assert rc.failure_rate() == pytest.approx(0.3)

    def test_failure_rate_none_when_empty(self):
        from miloco.node_monitor.node_state import RollingCounter

        rc = RollingCounter()
        assert rc.failure_rate() is None

    def test_failure_rate_zero(self):
        from miloco.node_monitor.node_state import RollingCounter

        rc = RollingCounter()
        now = time.monotonic()
        for _ in range(5):
            rc.record_success(latency_ms=1, now=now)
        assert rc.failure_rate() == 0.0


class TestSetLifecycle:
    def test_set_lifecycle_direct(self):
        mon = _make_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=30)
        mon.set_lifecycle("eng", Lifecycle.READY)
        assert mon.snapshot_one("eng")["lifecycle"] == "ready"

    def test_set_lifecycle_unknown_ignored(self):
        mon = _make_monitor()
        mon.set_lifecycle("nope", Lifecycle.READY)

    def test_set_detail(self):
        mon = _make_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=30)
        mon.set_detail("eng", gate_ms=12.3, identity_ms=5.1)
        d = mon.snapshot_one("eng")
        assert d["detail"]["gate_ms"] == 12.3
