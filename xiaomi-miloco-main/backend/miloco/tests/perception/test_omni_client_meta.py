from miloco.perception.engine.omni.omni_client import OmniCallMeta, extract_usage


def test_omni_call_meta_dataclass_fields():
    meta = OmniCallMeta(
        latency_ms=100.0,
        retry_count=2,
        input_tokens=500,
        output_tokens=200,
        cached_tokens=100,
        audio_tokens=50,
        video_tokens=50,
        error_code=None,
    )
    assert meta.latency_ms == 100.0
    assert meta.retry_count == 2
    assert meta.input_tokens == 500
    assert meta.error_code is None


def test_omni_call_meta_defaults_minimal():
    meta = OmniCallMeta(latency_ms=50.0)
    assert meta.retry_count == 0
    assert meta.input_tokens is None
    assert meta.error_code is None


def test_from_raw_response_extracts_usage():
    raw = {
        "usage": {
            "prompt_tokens": 1234,
            "completion_tokens": 256,
            "prompt_tokens_details": {
                "cached_tokens": 100,
                "audio_tokens": 0,
                "video_tokens": 50,
            },
        }
    }
    meta = OmniCallMeta.from_raw(raw, latency_ms=80.0, retry_count=1)
    assert meta.latency_ms == 80.0
    assert meta.retry_count == 1
    assert meta.input_tokens == 1234
    assert meta.output_tokens == 256
    assert meta.cached_tokens == 100
    assert meta.video_tokens == 50


def test_from_raw_handles_missing_usage():
    meta = OmniCallMeta.from_raw({}, latency_ms=10.0)
    assert meta.input_tokens is None
    assert meta.output_tokens is None


def test_extract_usage_still_works():
    raw = {"usage": {"prompt_tokens": 100, "completion_tokens": 20}}
    u = extract_usage(raw)
    assert u["input_tokens"] == 100
    assert u["output_tokens"] == 20
