import time

import pytest
from miloco.node_monitor.monitor import NodeMonitor, get_monitor
from miloco.node_monitor.node_state import Lifecycle, NodeKind
from miloco.node_monitor.watchdog import WatchdogTask


@pytest.fixture(autouse=True)
def _reset_monitor():
    NodeMonitor._reset()
    yield
    NodeMonitor._reset()


class TestWatchdogStallDetection:
    def test_stall_when_no_progress(self):
        mon = get_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=2)
        state = mon._states["eng"]
        state.lifecycle = Lifecycle.RUNNING_START
        state.last_progress_at = time.monotonic() - 5

        wd = WatchdogTask(mon)
        wd._tick(mon, time.monotonic())

        assert state.lifecycle == Lifecycle.STALLED
        assert state.stalled_since is not None

    def test_watchdog_does_not_recover_stalled(self):
        """watchdog 不做 STALLED → RUNNING 自愈;recovery 交给 _exit_track / _enter_track."""
        mon = get_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=2)
        state = mon._states["eng"]
        state.lifecycle = Lifecycle.STALLED
        state.stalled_since = time.monotonic() - 3
        state.last_progress_at = time.monotonic()

        wd = WatchdogTask(mon)
        wd._tick(mon, time.monotonic())

        assert state.lifecycle == Lifecycle.STALLED
        assert state.stalled_since is not None

    def test_skips_registered_nodes(self):
        mon = get_monitor()
        mon.register("svc", NodeKind.SERVICE, watchdog_s=5)
        state = mon._states["svc"]

        wd = WatchdogTask(mon)
        wd._tick(mon, time.monotonic() + 100)

        assert state.lifecycle == Lifecycle.REGISTERED

    def test_skips_ready_nodes(self):
        mon = get_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=2)
        state = mon._states["eng"]
        state.lifecycle = Lifecycle.READY
        state.last_progress_at = time.monotonic() - 10

        wd = WatchdogTask(mon)
        wd._tick(mon, time.monotonic())

        assert state.lifecycle == Lifecycle.READY
        assert state.stalled_since is None

    def test_skips_zero_watchdog(self):
        mon = get_monitor()
        mon.register("svc", NodeKind.SERVICE, watchdog_s=0)
        state = mon._states["svc"]
        state.lifecycle = Lifecycle.READY

        wd = WatchdogTask(mon)
        wd._tick(mon, time.monotonic() + 100)

        assert state.lifecycle == Lifecycle.READY

    def test_shutdown_mode_skips_stall(self):
        mon = get_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=2)
        state = mon._states["eng"]
        state.lifecycle = Lifecycle.RUNNING_START
        state.last_progress_at = time.monotonic() - 10

        wd = WatchdogTask(mon)
        wd.enter_shutdown()
        wd._tick(mon, time.monotonic())

        assert state.lifecycle == Lifecycle.RUNNING_START


class TestWatchdogFailureRate:
    def test_emits_failing_when_rate_high(self):
        mon = get_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=10)
        state = mon._states["eng"]
        state.lifecycle = Lifecycle.RUNNING_START
        now = time.monotonic()
        state.last_progress_at = now

        for _ in range(10):
            state.rolling.record_failure(now=now)

        wd = WatchdogTask(mon)
        events = []
        mon.emit_event = lambda name, etype, msg: events.append((name, etype, msg))
        wd._tick(mon, now)

        failing_events = [(n, e, m) for n, e, m in events if e == "FAILING"]
        assert len(failing_events) == 1
        assert "eng" == failing_events[0][0]
        assert "80%" in failing_events[0][2]

    def test_no_duplicate_failing_events(self):
        mon = get_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=10)
        state = mon._states["eng"]
        state.lifecycle = Lifecycle.RUNNING_START
        now = time.monotonic()
        state.last_progress_at = now

        for _ in range(10):
            state.rolling.record_failure(now=now)

        wd = WatchdogTask(mon)
        events = []
        mon.emit_event = lambda name, etype, msg: events.append((name, etype, msg))
        wd._tick(mon, now)
        wd._tick(mon, now + 1)

        failing_events = [(n, e, m) for n, e, m in events if e == "FAILING"]
        assert len(failing_events) == 1

    def test_emits_failure_recovered(self):
        mon = get_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=10)
        state = mon._states["eng"]
        state.lifecycle = Lifecycle.RUNNING_START
        now = time.monotonic()
        state.last_progress_at = now

        for _ in range(10):
            state.rolling.record_failure(now=now)

        wd = WatchdogTask(mon)
        events = []
        mon.emit_event = lambda name, etype, msg: events.append((name, etype, msg))
        wd._tick(mon, now)

        # Add successes to bring rate below threshold
        for _ in range(50):
            state.rolling.record_success(latency_ms=10, now=now + 1)

        wd._tick(mon, now + 1)

        recovered = [(n, e, m) for n, e, m in events if e == "FAILURE_RECOVERED"]
        assert len(recovered) == 1

    def test_ignores_below_min_samples(self):
        mon = get_monitor()
        mon.register("eng", NodeKind.WINDOW, watchdog_s=10)
        state = mon._states["eng"]
        state.lifecycle = Lifecycle.RUNNING_START
        now = time.monotonic()
        state.last_progress_at = now

        # Only 3 failures — below FAILURE_RATE_MIN_SAMPLES (5)
        for _ in range(3):
            state.rolling.record_failure(now=now)

        wd = WatchdogTask(mon)
        events = []
        mon.emit_event = lambda name, etype, msg: events.append((name, etype, msg))
        wd._tick(mon, now)

        failing_events = [(n, e, m) for n, e, m in events if e == "FAILING"]
        assert len(failing_events) == 0


class TestWatchdogThread:
    def test_start_stop(self):
        mon = get_monitor()
        wd = WatchdogTask(mon)
        wd.start()
        time.sleep(0.1)
        assert wd._thread.is_alive()
        wd.stop()
        assert not wd._thread.is_alive()
