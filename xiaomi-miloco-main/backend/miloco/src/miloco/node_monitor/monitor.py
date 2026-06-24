from __future__ import annotations

import sys
import threading
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from miloco.node_monitor.event_log import NodeEventLog
from miloco.node_monitor.node_state import (
    Lifecycle,
    NodeKind,
    NodeName,
    NodeState,
    RollingCounter,
)


class TrackHandle:
    """Yielded by track_async()/track(). Accumulates per-invocation metrics."""

    __slots__ = ("_state", "_window_ms", "_input_n", "_output_n", "_skip_rolling")

    def __init__(self, state: NodeState | None = None):
        self._state = state
        self._window_ms: float = 0.0
        self._input_n: int = 0
        self._output_n: int = 0
        self._skip_rolling: bool = False

    def add_input(self, n: int = 1) -> None:
        self._input_n += n

    def add_output(self, n: int = 1) -> None:
        self._output_n += n

    def add_window_ms(self, ms: float) -> None:
        self._window_ms += ms

    def skip_rolling(self) -> None:
        """标记本次 track 不计入 60s 滚动指标 (success/failure/latency/window/input/output);
        **lifecycle 仍正常转 RUNNING_END**。用于 early-return 路径,避免 empty batch
        等无效轮询污染 fps/p95/RTF。

        Flag 生命周期 = 单次 track 调用 (TrackHandle 每次 track_async/track 都新建,
        下次进入自动拿到 _skip_rolling=False 的新 handle,无需重置)。"""
        self._skip_rolling = True


class NodeMonitor:
    """Process-global singleton registry for all monitored nodes."""

    _instance: NodeMonitor | None = None
    _init_lock = threading.Lock()

    def __init__(self) -> None:
        self._states: dict[str, NodeState] = {}
        self._event_log: NodeEventLog | None = None
        self._warned_missing: set[str] = set()

    @classmethod
    def get_instance(cls) -> NodeMonitor:
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def _reset(cls) -> None:
        """For testing only."""
        cls._instance = None

    # ── setup ──────────────────────────────────────────────────────────

    def set_event_log(self, event_log: NodeEventLog) -> None:
        self._event_log = event_log

    def register(self, name: NodeName | str, kind: NodeKind, watchdog_s: float = 0) -> None:
        # 用 enum.value 而非 enum 本身存,避免 f"{state.name}" 拼出 "NodeName.X" 形式的丑输出。
        # (str, Enum) 在 Python 3.12 下 __format__ 仍返回 repr;.value 是纯字符串。
        name = name.value if isinstance(name, NodeName) else name
        if name in self._states:
            return
        self._states[name] = NodeState(name, kind, watchdog_s)

    def _warn_missing(self, method: str, name: str) -> None:
        if name in self._warned_missing:
            return
        self._warned_missing.add(name)
        _stderr(f"[node_monitor] {method}: node {name!r} not registered")

    # ── track (async) ──────────────────────────────────────────────────

    @asynccontextmanager
    async def track_async(self, name: NodeName | str, stage: str = "default") -> AsyncIterator[TrackHandle]:
        state = self._states.get(name)
        if state is None:
            self._warn_missing("track_async", name)
            yield TrackHandle()
            return

        handle = TrackHandle(state)
        entered_lifecycle = state.lifecycle
        t0 = time.monotonic()

        try:
            self._enter_track(state, entered_lifecycle, stage)
        except Exception:
            _stderr(f"[node_monitor] _enter_track failed for {name}")
            yield handle
            return

        exc_to_raise: BaseException | None = None
        try:
            yield handle
        except BaseException as e:
            exc_to_raise = e

        try:
            self._exit_track(state, entered_lifecycle, handle, t0, exc_to_raise, stage)
        except Exception:
            _stderr(f"[node_monitor] _exit_track failed for {name}")

        if exc_to_raise is not None:
            raise exc_to_raise

    # ── track (sync) ───────────────────────────────────────────────────

    @contextmanager
    def track(self, name: NodeName | str, stage: str = "default") -> Iterator[TrackHandle]:
        state = self._states.get(name)
        if state is None:
            self._warn_missing("track", name)
            yield TrackHandle()
            return

        handle = TrackHandle(state)
        entered_lifecycle = state.lifecycle
        t0 = time.monotonic()

        try:
            self._enter_track(state, entered_lifecycle, stage)
        except Exception:
            _stderr(f"[node_monitor] _enter_track failed for {name}")
            yield handle
            return

        exc_to_raise: BaseException | None = None
        try:
            yield handle
        except BaseException as e:
            exc_to_raise = e

        try:
            self._exit_track(state, entered_lifecycle, handle, t0, exc_to_raise, stage)
        except Exception:
            _stderr(f"[node_monitor] _exit_track failed for {name}")

        if exc_to_raise is not None:
            raise exc_to_raise

    # ── shared enter/exit logic ────────────────────────────────────────

    def _enter_track(self, state: NodeState, lifecycle: Lifecycle, stage: str) -> None:
        now = time.monotonic()
        if lifecycle == Lifecycle.REGISTERED:
            state.started_at = now
            state.lifecycle = Lifecycle.STARTING
            self.emit_event(state.name, "STARTING", f"stage={stage}")
            return

        if lifecycle in (Lifecycle.READY, Lifecycle.RUNNING_START, Lifecycle.RUNNING_END, Lifecycle.STALLED):
            state.last_progress_at = now
            state.lifecycle = Lifecycle.RUNNING_START
            if lifecycle == Lifecycle.READY:
                self.emit_event(state.name, "RUNNING_START", "first running track started")
            elif lifecycle == Lifecycle.STALLED:
                stall_dur = (now - state.stalled_since) if state.stalled_since else 0
                state.stalled_since = None
                self.emit_event(state.name, "RECOVERED", f"resumed after {stall_dur:.0f}s stall")

    def _exit_track(
        self,
        state: NodeState,
        entered_lifecycle: Lifecycle,
        handle: TrackHandle,
        t0: float,
        exc: BaseException | None,
        stage: str,
    ) -> None:
        now = time.monotonic()
        elapsed_ms = (now - t0) * 1000

        if entered_lifecycle == Lifecycle.REGISTERED:
            # Construction path
            if exc is None:
                state.lifecycle = Lifecycle.READY
                self.emit_event(state.name, "READY", "construction succeeded")
            else:
                state.lifecycle = Lifecycle.FAILED
                state.last_error = repr(exc)
                self.emit_event(state.name, "FAILED", f"construction error: {state.last_error}")
            return

        # Running path: enter 时已转 RUNNING_START,exit 一律转 RUNNING_END
        if entered_lifecycle not in (Lifecycle.READY, Lifecycle.RUNNING_START, Lifecycle.RUNNING_END, Lifecycle.STALLED):
            return

        state.lifecycle = Lifecycle.RUNNING_END
        state.last_progress_at = now

        if state.stalled_since is not None:
            stall_dur = now - state.stalled_since
            state.stalled_since = None
            self.emit_event(
                state.name,
                "RECOVERED",
                f"resumed after {stall_dur:.0f}s stall (track finished)",
            )

        # skip_rolling 路径:lifecycle 已正常转 RUNNING_END,但本次 track 不进
        # success/failure/latency/window/input/output 等 60s 滚动指标。
        if handle._skip_rolling:
            return

        stage_rc = state.stage_rollings.setdefault(stage, RollingCounter())

        if handle._input_n:
            state.rolling.record_input(handle._input_n, now=now)
            stage_rc.record_input(handle._input_n, now=now)
        if handle._output_n:
            state.rolling.record_output(handle._output_n, now=now)
            stage_rc.record_output(handle._output_n, now=now)

        if exc is not None:
            state.last_error = repr(exc)
            state.rolling.record_failure(now=now)
            stage_rc.record_failure(now=now)
            return

        state.rolling.record_success(
            latency_ms=elapsed_ms,
            window_ms=handle._window_ms,
            now=now,
        )
        stage_rc.record_success(
            latency_ms=elapsed_ms,
            window_ms=handle._window_ms,
            now=now,
        )

    # ── direct setters ─────────────────────────────────────────────────

    def set_lifecycle(self, name: NodeName | str, life: Lifecycle, error: str | None = None) -> None:
        state = self._states.get(name)
        if state is None:
            self._warn_missing("set_lifecycle", name)
            return
        old = state.lifecycle
        # 转 STARTING 时,只允许从 dormant 状态出发;已在运行/启动中的节点不打断
        if life == Lifecycle.STARTING and not old.is_dormant:
            return
        state.lifecycle = life
        if error:
            state.last_error = error
        if old != life:
            msg = f"{old.value} -> {life.value}"
            if error:
                msg += f" error={error}"
            self.emit_event(state.name, life.value.upper(), msg)

    def set_detail(self, name: NodeName | str, **fields) -> None:
        state = self._states.get(name)
        if state is None:
            self._warn_missing("set_detail", name)
            return
        state.detail.update(fields)

    # ── queries ────────────────────────────────────────────────────────

    def snapshot(self) -> list[dict]:
        return [s.to_dict() for s in self._states.values()]

    def snapshot_one(self, name: str) -> dict | None:
        state = self._states.get(name)
        if state is None:
            return None
        return state.to_dict()

    def get_state(self, name: NodeName | str) -> NodeState | None:
        """Return the NodeState object directly (no serialization)."""
        return self._states.get(name.value if isinstance(name, NodeName) else name)

    def iter_states(self) -> list[NodeState]:
        return list(self._states.values())

    # ── event log ──────────────────────────────────────────────────────

    def emit_event(self, name: str, event_type: str, message: str) -> None:
        if self._event_log is not None:
            try:
                self._event_log.emit(name, event_type, message)
            except Exception:
                pass


def get_monitor() -> NodeMonitor:
    return NodeMonitor.get_instance()


def _stderr(msg: str) -> None:
    try:
        print(msg, file=sys.stderr, flush=True)
    except Exception:
        pass
