from miloco.observability.aggregate import aggregate_cycle
from miloco.observability.types import (
    DecodeTrace,
    DeviceTraceRecord,
    GateTrace,
    IdentityTrace,
    OmniTrace,
)


def _make_device(did: str, gate_pass: bool = True, with_omni: bool = True) -> DeviceTraceRecord:
    return DeviceTraceRecord(
        device_trace_id=f"dt-{did}", cycle_id="c-1", timestamp=100,
        device_id=did, room_name="r1",
        decode=DecodeTrace(video_avg_ms=1.0, audio_avg_ms=2.0,
                           video_frame_count=10, audio_frame_count=5),
        gate=GateTrace(
            ms=1.0, video_ms=0.5, audio_ms=0.5,
            video_pass=gate_pass, audio_pass=gate_pass,
            skipped=not gate_pass,
        ),
        identity=IdentityTrace(ms=2.0) if gate_pass else None,
        omni=OmniTrace(ms=100.0, error_code=None) if (gate_pass and with_omni) else None,
    )


def _make_meta():
    return dict(
        trace_id="c-1", timestamp=100,
        in_delay_ms=0, out_delay_ms=0,
        decode_ms=0, collect_ms=0, convert_ms=0, log_ms=0,
        cycle_total_ms=0, pipeline_total_ms=0, window_duration_ms=0,
        window_first_frame_recv_ms=None, stream_lag_ms=None,
    )


def test_sum_aggregation():
    devices = [_make_device("d1"), _make_device("d2")]
    cycle = aggregate_cycle(devices, _make_meta())
    assert cycle.gate_ms == 2.0
    assert cycle.gate_video_ms == 1.0
    assert cycle.identity_ms == 4.0
    assert cycle.omni_ms == 200.0
    assert cycle.device_count == 2
    # cycle 级二值:batch 一次 omni 调用 → 1
    assert cycle.omni_call_count == 1


def test_or_aggregation_video_pass():
    devices = [_make_device("d1", gate_pass=True),
               _make_device("d2", gate_pass=False)]
    cycle = aggregate_cycle(devices, _make_meta())
    assert cycle.gate_video_pass is True
    assert cycle.gate_audio_pass is True


def test_and_aggregation_skipped():
    devices = [_make_device("d1", gate_pass=False),
               _make_device("d2", gate_pass=False)]
    cycle = aggregate_cycle(devices, _make_meta())
    assert cycle.skipped is True


def test_skipped_false_when_any_passed():
    devices = [_make_device("d1", gate_pass=True),
               _make_device("d2", gate_pass=False)]
    cycle = aggregate_cycle(devices, _make_meta())
    assert cycle.skipped is False


def _make_failed_device(did: str) -> DeviceTraceRecord:
    return DeviceTraceRecord(
        device_trace_id=f"dt-{did}", cycle_id="c-1", timestamp=100,
        device_id=did, room_name="r1",
        decode=DecodeTrace(1.0, 2.0, 10, 5),
        gate=GateTrace(1.0, 0.5, 0.5, True, True, False),
        identity=IdentityTrace(ms=2.0),
        omni=OmniTrace(ms=100.0, error_code="HTTP_500"),
    )


def test_omni_error_count_is_cycle_level_binary_any_fail():
    """任一 device 失败 → cycle 级 omni_error_count = 1。"""
    cycle = aggregate_cycle(
        [_make_device("d1"), _make_failed_device("d2")], _make_meta(),
    )
    assert cycle.omni_error_count == 1


def test_omni_error_count_is_cycle_level_binary_all_fail():
    """3 个 device 全失败 → cycle 级仍是 1,不是 3(避免 N 倍虚高)。"""
    cycle = aggregate_cycle(
        [_make_failed_device(f"d{i}") for i in range(3)], _make_meta(),
    )
    assert cycle.omni_error_count == 1
    assert cycle.omni_call_count == 1


def test_omni_call_count_zero_when_all_gate_skipped():
    devices = [_make_device("d1", gate_pass=False),
               _make_device("d2", gate_pass=False)]
    cycle = aggregate_cycle(devices, _make_meta())
    assert cycle.omni_call_count == 0
    assert cycle.omni_error_count == 0




# =============================================================================
# Section 7.5 E4 — gate_hold_pass 聚合 (any)
# =============================================================================


def _gate(video=False, audio=False, hold=False) -> GateTrace:
    return GateTrace(
        ms=0, video_ms=0, audio_ms=0,
        video_pass=video, audio_pass=audio,
        skipped=not (video or audio or hold),
        hold_pass=hold,
    )


def _device_with_gate(did: str, gate: GateTrace) -> DeviceTraceRecord:
    return DeviceTraceRecord(
        device_trace_id=f"dt-{did}",
        cycle_id="c-1",
        timestamp=0,
        device_id=did,
        room_name="客厅",
        decode=DecodeTrace(video_avg_ms=0, audio_avg_ms=0, video_frame_count=0, audio_frame_count=0),
        gate=gate,
    )


class TestAggregateHoldPass:
    """E4 — gate_hold_pass 任一 device hold 即 cycle 为 hold。"""

    def test_any_device_hold_makes_cycle_hold(self):
        recs = [
            _device_with_gate("A", _gate(hold=True)),
            _device_with_gate("B", _gate(audio=True)),
        ]
        cycle = aggregate_cycle(recs, _make_meta())
        assert cycle.gate_hold_pass is True

    def test_all_no_hold_cycle_no_hold(self):
        recs = [
            _device_with_gate("A", _gate(video=True)),
            _device_with_gate("B", _gate(audio=True)),
        ]
        cycle = aggregate_cycle(recs, _make_meta())
        assert cycle.gate_hold_pass is False
