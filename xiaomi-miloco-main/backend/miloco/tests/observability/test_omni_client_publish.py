"""验 omni_client 调用完成时调 publish_omni_log,debug-only。"""
from __future__ import annotations

import gzip
import json
from unittest.mock import AsyncMock, MagicMock, patch

from miloco.observability import omni_log
from miloco.observability.context import (
    DeviceContext,
    reset_device_context,
    set_device_context,
)
from miloco.perception.engine.omni.omni_client import call_omni


async def _fake_post(url, headers, json):
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={
        "choices": [{"message": {"content": "hello world"}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 5},
    })
    return resp


async def test_call_omni_emits_redacted_log_when_debug_on(tmp_path, monkeypatch):
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    (tmp_path / ".debug_observability").write_text("")
    from miloco.observability import debug
    debug._reset_cache_for_tests()
    omni_log.reset_buffer_for_tests()

    from miloco.perception.engine.config import OmniConfig
    cfg = OmniConfig(
        api_key="test-key",
        base_url="https://mock",
        model="mock-model",
        max_completion_tokens=100,
        temperature=0.0,
        top_p=1.0,
        timeout=10.0,
        stream=False,
    )

    payload = {
        "system_prompt": "system",
        "user_content": "user",
        "audio_base64": "BASE64",
    }

    token = set_device_context(DeviceContext(
        device_trace_id="dt-1", device_id="did-1", room_name="客厅",
    ))
    try:
        with patch("httpx.AsyncClient") as cm:
            cm.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=_fake_post
            )
            with patch("miloco.perception.engine.omni.omni_client.fire_record"):
                await call_omni(payload, cfg, type="realtime")
    finally:
        reset_device_context(token)

    omni_log.flush()
    log_dir = tmp_path / "trace" / "omni"
    files = list(log_dir.glob("*.jsonl.gz"))
    assert len(files) == 1
    with gzip.open(files[0], "rt", encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["device_trace_id"] == "dt-1"
    assert rec["device_id"] == "did-1"
    assert rec["room_name"] == "客厅"
    assert rec["response"] == "hello world"
    assert rec["usage"]["input_tokens"] == 100
    assert rec["usage"]["output_tokens"] == 5
    # multimodal block 已脱敏
    for msg in rec["messages"]:
        if isinstance(msg.get("content"), list):
            for blk in msg["content"]:
                if blk.get("type") == "input_image":
                    assert blk == {"type": "input_image", "_redacted": True}


async def test_call_omni_no_log_when_debug_off(tmp_path, monkeypatch):
    monkeypatch.setenv("MILOCO_HOME", str(tmp_path))
    from miloco.observability import debug
    debug._reset_cache_for_tests()
    omni_log.reset_buffer_for_tests()

    from miloco.perception.engine.config import OmniConfig
    cfg = OmniConfig(
        api_key="test-key", base_url="https://mock", model="mock-model",
        max_completion_tokens=100, temperature=0.0, top_p=1.0,
        timeout=10.0, stream=False,
    )

    token = set_device_context(DeviceContext(
        device_trace_id="dt-1", device_id="did-1", room_name="客厅",
    ))
    try:
        with patch("httpx.AsyncClient") as cm:
            cm.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=_fake_post
            )
            with patch("miloco.perception.engine.omni.omni_client.fire_record"):
                await call_omni({"system_prompt": "s", "user_content": "u"}, cfg)
    finally:
        reset_device_context(token)

    omni_log.flush()
    assert not (tmp_path / "trace" / "omni").exists() or not list(
        (tmp_path / "trace" / "omni").glob("*.jsonl.gz")
    )
