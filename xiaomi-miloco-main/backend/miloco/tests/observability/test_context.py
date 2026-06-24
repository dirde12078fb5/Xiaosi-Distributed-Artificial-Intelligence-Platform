import asyncio

from miloco.observability.context import (
    get_trace_id,
    reset_trace_id,
    set_trace_id,
)


def test_default_trace_id_is_none():
    assert get_trace_id() is None


def test_set_and_get():
    token = set_trace_id("trace-abc")
    try:
        assert get_trace_id() == "trace-abc"
    finally:
        reset_trace_id(token)
    assert get_trace_id() is None


def test_concurrent_tasks_have_independent_trace_id():
    async def task(value: str) -> str:
        token = set_trace_id(value)
        try:
            await asyncio.sleep(0)
            return get_trace_id() or ""
        finally:
            reset_trace_id(token)

    async def driver() -> tuple[str, str]:
        a, b = await asyncio.gather(task("trace-a"), task("trace-b"))
        return a, b

    a, b = asyncio.run(driver())
    assert (a, b) == ("trace-a", "trace-b")
