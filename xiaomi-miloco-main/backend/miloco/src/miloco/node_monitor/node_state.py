from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class Lifecycle(str, Enum):
    REGISTERED = "registered"
    STARTING = "starting"
    READY = "ready"
    RUNNING_START = "running_start"  # 在 track_async/track 体内,正在执行
    RUNNING_END = "running_end"      # 两次 track 之间,刚完成
    STALLED = "stalled"
    STOPPED = "stopped"
    FAILED = "failed"
    PREREQ_MISSING = "prereq_missing"  # 前置条件未满足(非故障)

    # ── 状态分类 ──────────────────────────────────────────────────────

    @property
    def is_dormant(self) -> bool:
        """非运行态，应尝试启动 (register/init 流程用)。"""
        return self in _DORMANT

    @property
    def is_unhealthy(self) -> bool:
        """健康检查判定为不健康 (/health 503)。"""
        return self in _UNHEALTHY


_DORMANT = frozenset({
    Lifecycle.REGISTERED,
    Lifecycle.STOPPED,
    Lifecycle.FAILED,
    Lifecycle.PREREQ_MISSING,
})

_UNHEALTHY = frozenset({
    Lifecycle.FAILED,
    Lifecycle.STALLED,
})


class NodeKind(str, Enum):
    SOURCE = "source"
    WINDOW = "window"
    EVENT = "event"
    SERVICE = "service"


class NodeName(str, Enum):
    CAMERA = "camera"
    COLLECTOR = "collector"
    PROCESSOR = "processor"
    ENGINE = "engine"
    RULE = "rule"
    MIOT_PROXY = "miot_proxy"
    RULE_SERVICE = "rule_service"
    PERCEPTION_SERVICE = "perception_service"
    TERMINATE_EVALUATOR = "terminate_evaluator"


ROLLING_WINDOW_S = 60


@dataclass
class _Bucket:
    ts: int  # epoch second (monotonic, floored)
    success: int = 0
    failure: int = 0
    latency_ms: list[float] = field(default_factory=list)
    window_ms_sum: float = 0.0
    input_count: int = 0
    output_count: int = 0


class RollingCounter:
    """60-bucket deque, one second per bucket."""

    def __init__(self, window_s: int = ROLLING_WINDOW_S):
        self._window_s = window_s
        self._buckets: deque[_Bucket] = deque()

    def _current_bucket(self, now: float) -> _Bucket:
        epoch = int(now)
        if self._buckets and self._buckets[-1].ts == epoch:
            return self._buckets[-1]
        b = _Bucket(ts=epoch)
        self._buckets.append(b)
        return b

    def trim(self, now: float) -> None:
        cutoff = int(now) - self._window_s
        while self._buckets and self._buckets[0].ts < cutoff:
            self._buckets.popleft()

    def record_success(
        self, latency_ms: float, window_ms: float = 0.0, now: float | None = None
    ) -> None:
        t = now if now is not None else time.monotonic()
        b = self._current_bucket(t)
        b.success += 1
        b.latency_ms.append(latency_ms)
        b.window_ms_sum += window_ms

    def record_failure(self, now: float | None = None) -> None:
        t = now if now is not None else time.monotonic()
        b = self._current_bucket(t)
        b.failure += 1

    def record_input(self, n: int = 1, now: float | None = None) -> None:
        t = now if now is not None else time.monotonic()
        b = self._current_bucket(t)
        b.input_count += n

    def record_output(self, n: int = 1, now: float | None = None) -> None:
        t = now if now is not None else time.monotonic()
        b = self._current_bucket(t)
        b.output_count += n

    def fps(self) -> float:
        self.trim(time.monotonic())
        total = sum(b.success for b in self._buckets)
        return total / self._window_s if self._window_s else 0.0

    def rtf(self) -> float | None:
        self.trim(time.monotonic())
        total_latency = sum(sum(b.latency_ms) for b in self._buckets)
        total_window = sum(b.window_ms_sum for b in self._buckets)
        if total_window <= 0:
            return None
        return total_latency / total_window

    def p95_latency_ms(self) -> float | None:
        self.trim(time.monotonic())
        all_lat: list[float] = []
        for b in self._buckets:
            all_lat.extend(b.latency_ms)
        if not all_lat:
            return None
        all_lat.sort()
        idx = int(math.ceil(len(all_lat) * 0.95)) - 1
        return all_lat[max(idx, 0)]

    def input_qps(self) -> float:
        self.trim(time.monotonic())
        total = sum(b.input_count for b in self._buckets)
        return total / self._window_s if self._window_s else 0.0

    def fire_qps(self) -> float:
        self.trim(time.monotonic())
        total = sum(b.output_count for b in self._buckets)
        return total / self._window_s if self._window_s else 0.0

    def success_count(self) -> int:
        self.trim(time.monotonic())
        return sum(b.success for b in self._buckets)

    def failure_count(self) -> int:
        self.trim(time.monotonic())
        return sum(b.failure for b in self._buckets)

    def total_count(self) -> int:
        self.trim(time.monotonic())
        return sum(b.success + b.failure for b in self._buckets)

    def failure_rate(self) -> float | None:
        self.trim(time.monotonic())
        total_s = sum(b.success for b in self._buckets)
        total_f = sum(b.failure for b in self._buckets)
        total = total_s + total_f
        if total == 0:
            return None
        return total_f / total


class NodeState:
    """Per-node runtime state. Lock-free: GIL guarantees single-attribute
    assignment atomicity; 60s rolling metrics tolerate sub-ms cross-field skew
    in to_dict snapshots."""

    def __init__(self, name: str, kind: NodeKind, watchdog_s: float = 0):
        self.name = name
        self.kind = kind
        self.lifecycle = Lifecycle.REGISTERED
        self.watchdog_s = watchdog_s
        self.registered_at = time.monotonic()
        self.started_at: float | None = None
        self.last_progress_at: float | None = None
        self.last_error: str | None = None
        self.stalled_since: float | None = None
        self.detail: dict = {}
        self.rolling = RollingCounter()
        # Per-stage RollingCounter,track_async/track 传的 stage 为 key。
        # 单 stage 节点不在 to_dict 输出 stages 字段(避免冗余);多 stage 节点自动展开。
        self.stage_rollings: dict[str, RollingCounter] = {}

    def _kind_metrics(self, rc: RollingCounter) -> dict:
        """Render kind-specific metrics from a RollingCounter."""
        m: dict = {}
        if self.kind in (NodeKind.SOURCE, NodeKind.WINDOW):
            m["fps_60s"] = round(rc.fps(), 2)
        if self.kind == NodeKind.WINDOW:
            rtf = rc.rtf()
            m["rtf_60s"] = round(rtf, 3) if rtf is not None else None
            p95 = rc.p95_latency_ms()
            m["p95_latency_ms"] = round(p95, 1) if p95 is not None else None
        if self.kind == NodeKind.EVENT:
            m["input_qps_60s"] = round(rc.input_qps(), 2)
            m["fire_qps_60s"] = round(rc.fire_qps(), 2)
        return m

    def to_dict(self) -> dict:
        now = time.monotonic()
        self.rolling.trim(now)
        d: dict = {
            "name": self.name,
            "kind": self.kind.value,
            "lifecycle": self.lifecycle.value,
        }

        ref = self.last_progress_at or self.started_at or self.registered_at
        d["idle_s"] = round(now - ref, 1)

        if self.kind == NodeKind.SERVICE:
            if self.last_error:
                d["last_error"] = self.last_error
            return d

        # success_count / failure_count 改成 60s 滚动语义,跟 fps_60s 同窗口,
        # 避免累积量造成的字段值持续膨胀和"重启清零跳变"困扰。
        d["success_count"] = self.rolling.success_count()
        d["failure_count"] = self.rolling.failure_count()
        d.update(self._kind_metrics(self.rolling))

        if self.last_error:
            d["last_error"] = self.last_error

        if self.detail:
            d["detail"] = dict(self.detail)

        if len(self.stage_rollings) > 1:
            d["stages"] = {
                stage: self._kind_metrics(rc)
                for stage, rc in self.stage_rollings.items()
            }

        if self.stalled_since is not None:
            d["stalled_since_s"] = round(now - self.stalled_since, 1)

        return d
