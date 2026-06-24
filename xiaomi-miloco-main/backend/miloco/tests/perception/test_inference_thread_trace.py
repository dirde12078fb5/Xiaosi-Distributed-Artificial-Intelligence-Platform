import asyncio

from miloco.observability.context import (
    get_trace_id,
    reset_trace_id,
    set_trace_id,
)
from miloco.perception.client import _run_with_trace_id


async def test_run_with_trace_id_sets_contextvar_inside_new_loop():
    """主线程 trace_id 通过显式参数透传到 inference 线程内的新 loop。"""

    captured: list[str | None] = []

    async def fake_impl():
        # 模拟 omni / publish_event 在 inference 线程内拿 ContextVar
        captured.append(get_trace_id())

    # 主线程视角下设了 trace,模拟 processor.process_realtime
    token = set_trace_id("outer-trace")
    try:
        outer_trace = get_trace_id()
        # 在子线程的新 event loop 里跑 — asyncio.run 创建新 loop,丢 ContextVar
        await asyncio.to_thread(
            lambda: asyncio.run(_run_with_trace_id(outer_trace, fake_impl()))
        )
    finally:
        reset_trace_id(token)

    assert captured == ["outer-trace"]


async def test_run_with_trace_id_noop_when_none():
    captured: list[str | None] = []

    async def fake_impl():
        captured.append(get_trace_id())

    await _run_with_trace_id(None, fake_impl())
    assert captured == [None]
