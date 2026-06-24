"""Tests for MultimodalCollector._pack_batch_latency_aggregates.

Batch-level decode aggregates are packed at collection time — the
collector walks each DeviceData once and produces frame-count-weighted
means so the pipeline processor only has to read fields off the batch.
"""

from __future__ import annotations

import numpy as np
import pytest
from miloco.perception.collect.collector import _pack_batch_latency_aggregates
from miloco.perception.schema import (
    DecodedAudioFrame,
    DecodedVideoFrame,
    DeviceData,
    PerceptionBatch,
)
from miloco.perception.types import PerceptionDevice


def _dev(did: str) -> PerceptionDevice:
    return PerceptionDevice(
        did=did,
        name=did,
        device_type="camera",
        room_id="r",
        room_name="r",
        online=True,
    )


def _video(**overrides) -> DecodedVideoFrame:
    base = dict(
        frame=np.zeros((2, 2, 3), dtype=np.uint8),
        stream_ts=0,
    )
    base.update(overrides)
    return DecodedVideoFrame(**base)


def _audio(**overrides) -> DecodedAudioFrame:
    base = dict(
        frame=np.zeros(320, dtype=np.int16),
        stream_ts=0,
    )
    base.update(overrides)
    return DecodedAudioFrame(**base)


def _make_device_data(
    did: str,
    *,
    video: list[DecodedVideoFrame] | None = None,
    audio: list[DecodedAudioFrame] | None = None,
    decode_video_avg_ms: float = 0.0,
    decode_audio_avg_ms: float = 0.0,
) -> DeviceData:
    """Build a DeviceData that mirrors what the camera adapter would produce.

    The per-device decode_*_avg_ms values are what
    _pack_batch_latency_aggregates expands into batch-level weighted
    means — these are the fields it reads, not the per-frame latencies.
    """
    return DeviceData(
        meta=_dev(did),
        video=video or [],
        audio=audio or [],
        decode_video_avg_ms=decode_video_avg_ms,
        decode_audio_avg_ms=decode_audio_avg_ms,
    )


class TestEmptyBatch:
    def test_empty_batch_leaves_all_aggregates_zero(self):
        batch = PerceptionBatch()
        _pack_batch_latency_aggregates(batch)
        assert batch.video_frame_count == 0
        assert batch.audio_frame_count == 0
        assert batch.decode_avg_ms == 0.0
        assert batch.decode_video_avg_ms == 0.0
        assert batch.decode_audio_avg_ms == 0.0


class TestSingleDevice:
    def test_video_only_device(self):
        dd = _make_device_data(
            "cam1",
            video=[_video(), _video(), _video()],  # 3 frames
            decode_video_avg_ms=20.0,
        )
        batch = PerceptionBatch(devices={"cam1": dd})
        _pack_batch_latency_aggregates(batch)

        assert batch.video_frame_count == 3
        assert batch.audio_frame_count == 0
        # Single device → batch mean equals the device mean.
        assert batch.decode_video_avg_ms == pytest.approx(20.0)
        assert batch.decode_avg_ms == pytest.approx(20.0)
        assert batch.decode_audio_avg_ms == 0.0

    def test_audio_only_device(self):
        dd = _make_device_data(
            "cam1",
            audio=[_audio(), _audio()],  # 2 frames
            decode_audio_avg_ms=8.0,
        )
        batch = PerceptionBatch(devices={"cam1": dd})
        _pack_batch_latency_aggregates(batch)

        assert batch.video_frame_count == 0
        assert batch.audio_frame_count == 2
        assert batch.decode_audio_avg_ms == pytest.approx(8.0)
        assert batch.decode_video_avg_ms == 0.0
        assert batch.decode_avg_ms == pytest.approx(8.0)


class TestMultiDeviceWeighting:
    def test_two_devices_frame_count_weighted(self):
        # cam1: 3 video frames @ decode=20
        cam1 = _make_device_data(
            "cam1",
            video=[_video(), _video(), _video()],
            decode_video_avg_ms=20.0,
        )
        # cam2: 1 video frame @ decode=60
        cam2 = _make_device_data(
            "cam2",
            video=[_video()],
            decode_video_avg_ms=60.0,
        )
        batch = PerceptionBatch(devices={"cam1": cam1, "cam2": cam2})
        _pack_batch_latency_aggregates(batch)

        assert batch.video_frame_count == 4
        assert batch.audio_frame_count == 0
        # Weighted: (20*3 + 60*1) / 4 = 120 / 4 = 30
        assert batch.decode_video_avg_ms == pytest.approx(30.0)
        assert batch.decode_avg_ms == pytest.approx(30.0)

    def test_mixed_modalities_weighted_by_total_frame_count(self):
        # cam1: 3 video @ decode=30, 0 audio
        # cam2: 0 video,             1 audio @ decode=90
        cam1 = _make_device_data(
            "cam1",
            video=[_video(), _video(), _video()],
            decode_video_avg_ms=30.0,
        )
        cam2 = _make_device_data(
            "cam2",
            audio=[_audio()],
            decode_audio_avg_ms=90.0,
        )
        batch = PerceptionBatch(devices={"cam1": cam1, "cam2": cam2})
        _pack_batch_latency_aggregates(batch)

        assert batch.video_frame_count == 3
        assert batch.audio_frame_count == 1
        # Per-modality means preserved.
        assert batch.decode_video_avg_ms == pytest.approx(30.0)
        assert batch.decode_audio_avg_ms == pytest.approx(90.0)
        # Combined: (30*3 + 90*1)/4 = 45
        assert batch.decode_avg_ms == pytest.approx(45.0)

    def test_per_device_means_not_simple_averaged(self):
        """If we averaged the two device means, mixed frame counts skew it.
        The aggregate must weight by frame count, not by device count.
        """
        # cam1: 1 video @ 100ms — heavy one frame
        # cam2: 9 video @ 10ms — many light frames
        cam1 = _make_device_data(
            "cam1",
            video=[_video()],
            decode_video_avg_ms=100.0,
        )
        cam2 = _make_device_data(
            "cam2",
            video=[_video() for _ in range(9)],
            decode_video_avg_ms=10.0,
        )
        batch = PerceptionBatch(devices={"cam1": cam1, "cam2": cam2})
        _pack_batch_latency_aggregates(batch)

        # Device-count average would be (100 + 10) / 2 = 55 — WRONG.
        # Frame-count average is (100*1 + 10*9) / 10 = 190 / 10 = 19.
        assert batch.decode_avg_ms == pytest.approx(19.0)
