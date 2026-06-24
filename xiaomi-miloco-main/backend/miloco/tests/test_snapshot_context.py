# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""snapshot_context — ContextVar 旁路 clip 字节收集器单测.

覆盖:
- scope 内 push_clip_bytes 进 sink(kind 区分 mp4/m4a)
- scope 外 push 静默 no-op
- 无 device_ctx push 静默 no-op
- 多 device 分组
- asyncio task 隔离(子 task 复制父 ContextVar 当前值,但不影响父)
"""

from __future__ import annotations

import asyncio

import pytest
from miloco.observability.context import (
    DeviceContext,
    reset_device_context,
    set_device_context,
)
from miloco.perception.snapshot_context import (
    ClipKind,
    push_clip_bytes,
    snapshot_collector_scope,
)


def test_no_scope_is_noop():
    """无 active scope → push 静默 no-op,不抛."""
    token = set_device_context(DeviceContext(device_trace_id="t", device_id="cam_a", room_name="r"))
    try:
        push_clip_bytes(b"some-bytes", "mp4")  # 不应抛
    finally:
        reset_device_context(token)


def test_no_device_context_is_noop():
    """有 scope 但无 device_ctx(未 set)→ no-op,sink 保持空."""
    sink: dict[str, tuple[bytes, ClipKind]] = {}
    with snapshot_collector_scope(sink):
        push_clip_bytes(b"some-bytes", "mp4")  # device_ctx 未 set
    assert sink == {}


def test_scope_collects_per_device_with_kind():
    """scope 内 push 按 device_id 分组写入 sink,带 kind 标."""
    sink: dict[str, tuple[bytes, ClipKind]] = {}
    with snapshot_collector_scope(sink):
        t1 = set_device_context(DeviceContext(device_trace_id="t1", device_id="cam_a", room_name="r"))
        try:
            push_clip_bytes(b"clip-A", "mp4")  # 视频路径
        finally:
            reset_device_context(t1)

        t2 = set_device_context(DeviceContext(device_trace_id="t2", device_id="cam_b", room_name="r"))
        try:
            push_clip_bytes(b"clip-B", "m4a")  # audio-only 路径
        finally:
            reset_device_context(t2)

    assert set(sink.keys()) == {"cam_a", "cam_b"}
    assert sink["cam_a"] == (b"clip-A", "mp4")
    assert sink["cam_b"] == (b"clip-B", "m4a")


def test_scope_exit_resets():
    """scope 退出后,push 再次 no-op."""
    sink: dict[str, tuple[bytes, ClipKind]] = {}
    with snapshot_collector_scope(sink):
        pass
    # scope 已退出
    t = set_device_context(DeviceContext(device_trace_id="t", device_id="cam_a", room_name="r"))
    try:
        push_clip_bytes(b"after-scope", "mp4")  # no-op
    finally:
        reset_device_context(t)
    # sink 没被填(scope 内本来就没 push)
    assert sink == {}


@pytest.mark.asyncio
async def test_async_task_isolation():
    """子 task 复制父 ContextVar 当前值,但子 task 修改不影响父 (PEP 567).

    这里测的是:外层无 scope,子 task 开 scope 后 push 进入子 task 自己的 sink,
    外层仍是 no-op.
    """
    parent_sink: dict[str, tuple[bytes, ClipKind]] = {}

    async def child():
        child_sink: dict[str, tuple[bytes, ClipKind]] = {}
        with snapshot_collector_scope(child_sink):
            t = set_device_context(DeviceContext(device_trace_id="t", device_id="cam_c", room_name="r"))
            try:
                push_clip_bytes(b"clip-child", "mp4")
            finally:
                reset_device_context(t)
        return child_sink

    result = await asyncio.create_task(child())
    assert result == {"cam_c": (b"clip-child", "mp4")}
    # 父 sink 不变
    assert parent_sink == {}
