import numpy as np
from miloco.perception.collect.collector import _pack_batch_latency_aggregates
from miloco.perception.schema import (
    DecodedAudioFrame,
    DecodedVideoFrame,
    DeviceData,
    PerceptionBatch,
)
from miloco.perception.types import PerceptionDevice


def _make_device(did: str, recv_unix_ms_seq: list[int]) -> DeviceData:
    dd = DeviceData(meta=PerceptionDevice(did=did, name=did, device_type="camera"))
    for r in recv_unix_ms_seq:
        dd.video.append(DecodedVideoFrame(
            frame=np.zeros((10, 10, 3), dtype=np.uint8),
            stream_ts=0, recv_unix_ms=r,
        ))
    dd.window_start_unix_ms = 100_000
    dd.window_end_unix_ms = 103_000
    return dd


def test_window_first_frame_recv_ms_aggregated_from_min():
    batch = PerceptionBatch()
    batch.devices = {
        "a": _make_device("a", [99_000, 99_500, 100_200]),
        "b": _make_device("b", [99_800, 100_100]),
    }
    _pack_batch_latency_aggregates(batch)
    assert batch.window_first_frame_recv_ms == 99_000


def test_window_first_frame_recv_ms_none_when_no_recv_unix():
    batch = PerceptionBatch()
    batch.devices = {"a": _make_device("a", [0, 0])}
    _pack_batch_latency_aggregates(batch)
    assert batch.window_first_frame_recv_ms is None


def test_window_first_frame_recv_ms_audio_also_counts():
    batch = PerceptionBatch()
    dd = DeviceData(meta=PerceptionDevice(did="a", name="a", device_type="speaker"))
    dd.audio.append(DecodedAudioFrame(
        frame=np.zeros(100, dtype=np.int16),
        stream_ts=0, recv_unix_ms=98_500,
    ))
    dd.window_start_unix_ms = 100_000
    dd.window_end_unix_ms = 103_000
    batch.devices = {"a": dd}
    _pack_batch_latency_aggregates(batch)
    assert batch.window_first_frame_recv_ms == 98_500
