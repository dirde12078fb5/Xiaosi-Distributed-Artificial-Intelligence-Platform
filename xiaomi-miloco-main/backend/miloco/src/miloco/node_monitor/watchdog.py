from __future__ import annotations

import sys
import threading
import time

from miloco.node_monitor.node_state import Lifecycle

TICK_INTERVAL = 60.0
WATCHDOG_SELF_THRESHOLD = 180.0
FAILURE_RATE_THRESHOLD = 0.8
FAILURE_RATE_MIN_SAMPLES = 5

if __name__ != "__main__":
    from miloco.node_monitor.monitor import NodeMonitor


class WatchdogTask:
    """Daemon thread that scans nodes for stall detection every TICK_INTERVAL."""

    def __init__(self, monitor: NodeMonitor):
        self._monitor = monitor
        self._stop_event = threading.Event()
        self._shutdown_mode = False
        self._thread: threading.Thread | None = None
        self._last_tick: float = 0.0
        self._failing_nodes: set[str] = set()

    def start(self) -> None:
        self._last_tick = time.monotonic()
        self._thread = threading.Thread(
            target=self._run, name="node-watchdog", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def enter_shutdown(self) -> None:
        self._shutdown_mode = True

    def _run(self) -> None:
        mon = self._monitor
        while not self._stop_event.wait(timeout=TICK_INTERVAL):
            now = time.monotonic()

            # Self-monitoring fallback
            if now - self._last_tick > WATCHDOG_SELF_THRESHOLD:
                _stderr(
                    f"[watchdog] self-stall detected: "
                    f"{now - self._last_tick:.1f}s since last tick"
                )
            self._last_tick = now

            try:
                self._tick(mon, now)
            except Exception as e:
                _stderr(f"[watchdog] tick error: {e}")

    def _tick(self, mon: NodeMonitor, now: float) -> None:
        for state in mon.iter_states():
            if state.watchdog_s <= 0:
                continue

            lc = state.lifecycle
            ref = state.last_progress_at or state.started_at or state.registered_at
            idle = now - ref

            # Stall detection — 只在 RUNNING_START (track 进行中) 判 STALLED
            # RUNNING_END 表示两次 track 之间的自然空闲,不触发告警
            # (避免业务稀疏触发 → 误判 STALL → /health 503)
            # 恢复(STALLED → RUNNING_END/RUNNING_START)由 _exit_track / _enter_track 处理
            if lc == Lifecycle.RUNNING_START:
                if idle > state.watchdog_s:
                    if not self._shutdown_mode:
                        state.lifecycle = Lifecycle.STALLED
                        state.stalled_since = now
                        mon.emit_event(
                            state.name,
                            "STALLED",
                            f"track stuck for {idle:.0f}s (threshold {state.watchdog_s}s)",
                        )

            # Failure rate detection (event only, no lifecycle change)
            if lc in (Lifecycle.RUNNING_START, Lifecycle.RUNNING_END, Lifecycle.STALLED):
                state.rolling.trim(now)
                for rc in state.stage_rollings.values():
                    rc.trim(now)
                rate = state.rolling.failure_rate()
                if rate is not None and rate >= FAILURE_RATE_THRESHOLD:
                    if state.rolling.total_count() >= FAILURE_RATE_MIN_SAMPLES:
                        if state.name not in self._failing_nodes:
                            self._failing_nodes.add(state.name)
                            mon.emit_event(
                                state.name,
                                "FAILING",
                                f"failure rate {rate:.0%} over 60s "
                                f"(threshold {FAILURE_RATE_THRESHOLD:.0%})",
                            )
                else:
                    if state.name in self._failing_nodes:
                        self._failing_nodes.discard(state.name)
                        mon.emit_event(
                            state.name,
                            "FAILURE_RECOVERED",
                            f"failure rate dropped to {rate:.0%}" if rate is not None else "no recent failures",
                        )


def _stderr(msg: str) -> None:
    try:
        print(msg, file=sys.stderr, flush=True)
    except Exception:
        pass
