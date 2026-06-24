"""Tests for decode-latency-related additions in perception.schema.

Covers:
* ``DecodedVideoFrame`` / ``DecodedAudioFrame`` carry ``recv_unix_ms``,
  ``decoded_unix_ms`` and ``decode_latency_ms`` (``decoded - recv``).
* ``DeviceData`` packs per-window decode averages (video / audio /
  combined).
* ``PerceptionBatch`` carries batch-level decode aggregates so the
  processor does not walk per-device frames.
* ``PerceptionLatency.decode_ms`` and its ``to_dict()`` serialization.
"""

from __future__ import annotations

import numpy as np
from miloco.perception.schema import (
    DecodedAudioFrame,
    DecodedVideoFrame,
    DeviceData,
    PerceptionBatch,
    PerceptionLatency,
)
from miloco.perception.types import PerceptionDevice


def _make_video_frame(**overrides) -> DecodedVideoFrame:
    base = dict(
        frame=np.zeros((2, 2, 3), dtype=np.uint8),
        stream_ts=1000,
        wall_ms=1100,
        unix_ms=1100 + 1_700_000_000_000,
    )
    base.update(overrides)
    return DecodedVideoFrame(**base)


def _make_audio_frame(**overrides) -> DecodedAudioFrame:
    base = dict(
        frame=np.zeros(320, dtype=np.int16),
        stream_ts=1000,
        wall_ms=1100,
        unix_ms=1100 + 1_700_000_000_000,
    )
    base.update(overrides)
    return DecodedAudioFrame(**base)


def _make_device(did: str = "cam1") -> PerceptionDevice:
    return PerceptionDevice(
        did=did,
        name=did,
        device_type="camera",
        room_id="r",
        room_name="r",
        online=True,
    )


class TestDecodedFrameDefaults:
    def test_video_frame_fields_default_zero(self):
        frame = _make_video_frame()
        assert frame.recv_unix_ms == 0
        assert frame.decoded_unix_ms == 0
        assert frame.decode_latency_ms == 0.0

    def test_audio_frame_fields_default_zero(self):
        frame = _make_audio_frame()
        assert frame.recv_unix_ms == 0
        assert frame.decoded_unix_ms == 0
        assert frame.decode_latency_ms == 0.0

    def test_frames_carry_custom_timestamps_and_latency(self):
        video = _make_video_frame(
            recv_unix_ms=1_700_000_001_000,
            decoded_unix_ms=1_700_000_001_050,
            decode_latency_ms=42.3,
        )
        audio = _make_audio_frame(
            recv_unix_ms=1_700_000_002_000,
            decoded_unix_ms=1_700_000_002_008,
            decode_latency_ms=7.5,
        )
        assert video.recv_unix_ms == 1_700_000_001_000
        assert video.decoded_unix_ms == 1_700_000_001_050
        assert video.decode_latency_ms == 42.3
        assert audio.recv_unix_ms == 1_700_000_002_000
        assert audio.decoded_unix_ms == 1_700_000_002_008
        assert audio.decode_latency_ms == 7.5


class TestDeviceDataDefaults:
    def test_decode_aggregates_default_zero(self):
        dd = DeviceData(meta=_make_device())
        assert dd.decode_avg_ms == 0.0
        assert dd.decode_video_avg_ms == 0.0
        assert dd.decode_audio_avg_ms == 0.0


class TestPerceptionBatchDefaults:
    def test_batch_level_aggregates_default_zero(self):
        batch = PerceptionBatch()
        assert batch.decode_avg_ms == 0.0
        assert batch.decode_video_avg_ms == 0.0
        assert batch.decode_audio_avg_ms == 0.0
        assert batch.video_frame_count == 0
        assert batch.audio_frame_count == 0


class TestPerceptionLatencyDecodeMs:
    def test_default_decode_is_zero(self):
        latency = PerceptionLatency()
        assert latency.decode_ms == 0.0

    def test_to_dict_includes_decode_rounded(self):
        latency = PerceptionLatency(decode_ms=12.3456)
        d = latency.to_dict()
        assert d["decode_ms"] == 12.3

    def test_to_dict_emits_decode_before_collect(self):
        """decode_ms precedes collect_ms to mirror the physical chain."""
        latency = PerceptionLatency(decode_ms=2.0, collect_ms=3.0)
        keys = list(latency.to_dict().keys())
        assert keys.index("decode_ms") < keys.index("collect_ms")

    def test_to_dict_preserves_other_fields(self):
        latency = PerceptionLatency(
            decode_ms=5.0,
            collect_ms=3.0,
            cycle_total_ms=20.0,
            window_duration_ms=1000.0,
        )
        d = latency.to_dict()
        for key in (
            "in_delay_ms",
            "out_delay_ms",
            "decode_ms",
            "collect_ms",
            "log_ms",
            "cycle_total_ms",
            "convert_ms",
            "gate_ms",
            "identity_ms",
            "omni_ms",
            "pipeline_total_ms",
            "window_duration_ms",
            "rtf",
            "rtf_pipeline",
        ):
            assert key in d

    def test_timing_detail_decode_sub_fields_roundtrip(self):
        latency = PerceptionLatency(
            timing_detail={"decode_video_ms": 8.75, "decode_audio_ms": 3.25}
        )
        d = latency.to_dict()
        assert d["timing_detail"]["decode_video_ms"] == 8.8
        assert d["timing_detail"]["decode_audio_ms"] == 3.2

    def test_docstring_mentions_decode_stage(self):
        doc = (PerceptionLatency.__doc__ or "").lower()
        assert "decode" in doc
