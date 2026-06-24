"""cycle 协程内透传 trace_id / per-device 元数据用的 ContextVar。"""
from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass

_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_trace_id() -> str | None:
    return _trace_id.get()


def set_trace_id(value: str) -> Token[str | None]:
    return _trace_id.set(value)


def reset_trace_id(token: Token[str | None]) -> None:
    _trace_id.reset(token)


@dataclass(frozen=True)
class DeviceContext:
    device_trace_id: str
    device_id: str
    room_name: str


_device_ctx: ContextVar[DeviceContext | None] = ContextVar("device_ctx", default=None)


def get_device_context() -> DeviceContext | None:
    return _device_ctx.get()


def set_device_context(ctx: DeviceContext) -> Token[DeviceContext | None]:
    return _device_ctx.set(ctx)


def reset_device_context(token: Token[DeviceContext | None]) -> None:
    _device_ctx.reset(token)
