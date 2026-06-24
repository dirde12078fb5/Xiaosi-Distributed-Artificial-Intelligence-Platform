# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Tests for ``run_agent_turn`` — the synchronous投递+等待 wrapper used by the
dispatcher drainer.

Contract under test:
  * On a webhook dict reply, ``(runId, status, rtt_ms)`` is passed through;
    missing ``runId`` → None, missing ``status`` → "error".
  * The caller-supplied message / sessionKey / lane / traceId / timeoutMs land
    in the webhook payload verbatim.
  * HTTP timeout = ``wait_timeout_ms/1000 + _HTTP_BUFFER_S`` (must exceed the
    platform wait so HTTP never aborts a turn that is still running).
  * Transport failures are NOT swallowed — the exception propagates to the
    drainer, which decides whether to skip.
"""

from unittest.mock import AsyncMock, patch

import pytest
from miloco.middleware.exceptions import AgentWebhookException
from miloco.utils.agent_client import _HTTP_BUFFER_S, run_agent_turn

_WAIT_MS = 30_000


async def test_run_agent_turn_returns_runid_status_rtt():
    with patch(
        "miloco.utils.agent_client.call_agent_webhook",
        new=AsyncMock(return_value={"runId": "run-1", "status": "ok"}),
    ):
        run_id, status, rtt_ms = await run_agent_turn(
            "hello",
            session_key="agent:main:miloco",
            lane="miloco-interactive",
            trace_id="trace-abc",
            wait_timeout_ms=_WAIT_MS,
        )
    assert run_id == "run-1"
    assert status == "ok"
    assert rtt_ms >= 0


async def test_run_agent_turn_defaults_when_fields_missing():
    # No runId, no status → (None, "error").
    with patch(
        "miloco.utils.agent_client.call_agent_webhook",
        new=AsyncMock(return_value={}),
    ):
        run_id, status, _ = await run_agent_turn(
            "hi",
            session_key="s",
            lane="l",
            trace_id="t",
            wait_timeout_ms=_WAIT_MS,
        )
    assert run_id is None
    assert status == "error"


async def test_run_agent_turn_passes_params_and_timeout():
    captured: dict = {}

    async def fake(action, payload=None, *, timeout=30.0):
        captured["action"] = action
        captured["payload"] = payload or {}
        captured["timeout"] = timeout
        return {"runId": "r-1", "status": "ok"}

    with patch("miloco.utils.agent_client.call_agent_webhook", new=fake):
        await run_agent_turn(
            "hi",
            session_key="agent:main:miloco-rule",
            lane="miloco-rule",
            trace_id="trace-xyz",
            wait_timeout_ms=_WAIT_MS,
        )

    assert captured["action"] == "agent"
    p = captured["payload"]
    assert p["message"] == "hi"
    assert p["sessionKey"] == "agent:main:miloco-rule"
    assert p["lane"] == "miloco-rule"
    assert p["traceId"] == "trace-xyz"
    assert p["timeoutMs"] == _WAIT_MS
    # HTTP timeout must sit above the platform wait by exactly the buffer.
    assert captured["timeout"] == _WAIT_MS / 1000 + _HTTP_BUFFER_S


async def test_run_agent_turn_propagates_webhook_exception():
    with patch(
        "miloco.utils.agent_client.call_agent_webhook",
        new=AsyncMock(side_effect=AgentWebhookException("boom")),
    ):
        with pytest.raises(AgentWebhookException):
            await run_agent_turn(
                "hi",
                session_key="s",
                lane="l",
                trace_id="t",
                wait_timeout_ms=_WAIT_MS,
            )
