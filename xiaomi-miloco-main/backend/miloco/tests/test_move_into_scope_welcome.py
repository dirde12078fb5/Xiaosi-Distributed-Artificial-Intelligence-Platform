# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Tests for welcoming devices that move INTO a managed home.

`MiotProxy._on_device_meta_changed_event` routes every device-meta event to the
meta listener; an hr_change that moves a device from an out-of-scope home into a
managed (whitelisted) home is flagged welcome=True so the meta listener greets
it after the refresh settles. Every other meta event (rename, intra-home room
change, moves not entering scope) is flagged welcome=False (refresh only).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from miloco.miot import client as client_module
from miloco.miot.client import MiotProxy
from miot.types import MIoTDeviceBindEvent


@pytest.fixture
def proxy(monkeypatch):
    """Bare MiotProxy with listeners mocked and is_home_allowed driven by
    ``env.allowed`` (a mutable set of managed home ids)."""
    env = SimpleNamespace(allowed={"H_OK"})
    monkeypatch.setattr(
        client_module,
        "is_home_allowed",
        lambda _kv, home_id: home_id in env.allowed,
    )
    p = MiotProxy.__new__(MiotProxy)
    p._kv_repo = object()
    p._bind_listener = AsyncMock()
    p._meta_listener = AsyncMock()
    env.proxy = p
    return env


def _hr(did: str, new_home, old_home) -> MIoTDeviceBindEvent:
    return MIoTDeviceBindEvent(
        uid="u",
        event="hr_change",
        did=did,
        raw={"did": did, "homeid": new_home, "origin_homeid": old_home},
    )


def _welcome_flag(meta_listener) -> bool:
    """Extract the welcome kwarg the meta listener was called with."""
    meta_listener.on_event.assert_awaited_once()
    _args, kwargs = meta_listener.on_event.await_args
    return kwargs.get("welcome", False)


@pytest.mark.asyncio
async def test_move_into_managed_home_welcomes(proxy):
    # unmanaged H_OLD -> managed H_OK → routed to meta listener with welcome=True.
    await proxy.proxy._on_device_meta_changed_event(_hr("d1", "H_OK", "H_OLD"))
    proxy.proxy._bind_listener.on_event.assert_not_awaited()
    assert _welcome_flag(proxy.proxy._meta_listener) is True


@pytest.mark.asyncio
async def test_room_change_within_managed_home_no_welcome(proxy):
    # Same home (room change only) → welcome=False.
    await proxy.proxy._on_device_meta_changed_event(_hr("d1", "H_OK", "H_OK"))
    assert _welcome_flag(proxy.proxy._meta_listener) is False


@pytest.mark.asyncio
async def test_move_between_managed_homes_no_welcome(proxy):
    # Both homes managed → already in scope, no re-welcome.
    proxy.allowed = {"H_OK", "H_OK2"}
    await proxy.proxy._on_device_meta_changed_event(_hr("d1", "H_OK", "H_OK2"))
    assert _welcome_flag(proxy.proxy._meta_listener) is False


@pytest.mark.asyncio
async def test_move_into_unmanaged_home_no_welcome(proxy):
    # Moved into a home that is NOT managed → welcome=False.
    await proxy.proxy._on_device_meta_changed_event(_hr("d1", "H_OTHER", "H_OLD"))
    assert _welcome_flag(proxy.proxy._meta_listener) is False


@pytest.mark.asyncio
async def test_rename_event_no_welcome(proxy):
    # rename carries no homeid → welcome=False.
    rename = MIoTDeviceBindEvent(uid="u", event="rename", did="d1", raw={"did": "d1"})
    await proxy.proxy._on_device_meta_changed_event(rename)
    assert _welcome_flag(proxy.proxy._meta_listener) is False


@pytest.mark.asyncio
async def test_hr_change_missing_origin_home_no_welcome(proxy):
    # hr_change into a managed home but the payload omits origin_homeid → we
    # cannot tell a genuine move-in from an intra-home change, so welcome=False
    # (a spurious "new device" greeting is worse than a missed one).
    evt = MIoTDeviceBindEvent(
        uid="u", event="hr_change", did="d1", raw={"did": "d1", "homeid": "H_OK"}
    )
    await proxy.proxy._on_device_meta_changed_event(evt)
    assert _welcome_flag(proxy.proxy._meta_listener) is False


@pytest.mark.asyncio
async def test_hr_change_missing_new_home_no_welcome(proxy):
    # Symmetric to the missing-origin case: payload omits homeid (new) → we
    # cannot confirm the device landed in a managed home, so welcome=False.
    # Guards the `new_home is None` half of _is_move_into_scope's guard.
    evt = MIoTDeviceBindEvent(
        uid="u", event="hr_change", did="d1", raw={"did": "d1", "origin_homeid": "H_OLD"}
    )
    await proxy.proxy._on_device_meta_changed_event(evt)
    assert _welcome_flag(proxy.proxy._meta_listener) is False
