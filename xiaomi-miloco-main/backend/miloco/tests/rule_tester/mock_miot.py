"""Mock MiotProxy for the rule tester.

The real MiotProxy talks to Xiaomi MIoT cloud and requires login. The tester
needs only the three methods used by the V3 actions registry handlers
(``miot.set_property`` / ``miot.call_action``); we stub them out and record
each call so the UI can show what the rule "would have" done.

This is a development tool and lives outside the production code path.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MockMiotCall:
    """One recorded MIoT call."""

    method: str          # "set_device_properties" / "call_device_action" / "get_device_properties"
    payload: Any         # the params object(s) the runner sent
    result: Any          # what the mock returned
    ts_ms: int


class MockMiotProxy:
    """Stand-in for ``miloco.miot.client.MiotProxy``.

    All write operations succeed (``code == 0``); reads return ``None`` for
    ``value`` so the runner's device-dispatch handlers see "value differs, dispatch".
    Each call is appended to :attr:`history` (capped) for the UI.
    """

    HISTORY_CAP = 200

    def __init__(self) -> None:
        self.history: deque[MockMiotCall] = deque(maxlen=self.HISTORY_CAP)

    # ---- methods used by miot.set_property / miot.call_action handlers ----

    async def set_device_properties(self, params: list) -> list:
        results = [{"code": 0, "did": p.did, "siid": p.siid, "piid": p.piid} for p in params]
        self._record("set_device_properties", [_dump(p) for p in params], results)
        return results

    async def call_device_action(self, param) -> dict:
        result = {"code": 0, "did": param.did, "siid": param.siid, "aiid": param.aiid}
        self._record("call_device_action", _dump(param), result)
        return result

    async def get_device_properties(self, params: list) -> list:
        # Return code=0 with value=None so idempotent paths (if any) treat the
        # current state as "unset" and proceed to dispatch.
        results = [
            {"code": 0, "did": p.did, "siid": p.siid, "piid": p.piid, "value": None}
            for p in params
        ]
        self._record("get_device_properties", [_dump(p) for p in params], results)
        return results

    # ---- introspection ----

    def recent(self, n: int = 50) -> list[dict]:
        items = list(self.history)[-n:]
        return [asdict(c) for c in items]

    def clear(self) -> None:
        self.history.clear()

    # ---- internal ----

    def _record(self, method: str, payload: Any, result: Any) -> None:
        import time

        call = MockMiotCall(
            method=method,
            payload=payload,
            result=result,
            ts_ms=int(time.time() * 1000),
        )
        self.history.append(call)
        logger.info("MockMiotProxy.%s payload=%s -> %s", method, payload, result)


def _dump(obj: Any) -> Any:
    """Best-effort serialize a pydantic / dataclass / dict to plain dict."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj
