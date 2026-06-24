import pytest
from miloco.perception.schema import PerceptionLatency


def test_rtf_e2e_includes_in_delay():
    lat = PerceptionLatency(
        in_delay_ms=200.0,
        cycle_total_ms=1000.0,
        window_duration_ms=3000.0,
    )
    assert lat.rtf_e2e == pytest.approx(1200.0 / 3000.0, abs=1e-3)


def test_rtf_stream_e2e_includes_stream_lag():
    lat = PerceptionLatency(
        in_delay_ms=200.0,
        stream_lag_ms=500.0,
        cycle_total_ms=1000.0,
        window_duration_ms=3000.0,
    )
    assert lat.rtf_stream_e2e == pytest.approx(1700.0 / 3000.0, abs=1e-3)


def test_rtf_omni_only_omni_over_window():
    lat = PerceptionLatency(
        omni_ms=600.0,
        window_duration_ms=3000.0,
    )
    assert lat.rtf_omni == pytest.approx(0.2, abs=1e-3)


def test_to_dict_includes_new_fields():
    lat = PerceptionLatency(
        in_delay_ms=200.0, stream_lag_ms=500.0,
        cycle_total_ms=1000.0, window_duration_ms=3000.0,
        omni_ms=600.0,
    )
    d = lat.to_dict()
    assert "stream_lag_ms" in d
    assert "rtf_e2e" in d
    assert "rtf_stream_e2e" in d
    assert "rtf_omni" in d


def test_rtf_zero_when_window_zero():
    lat = PerceptionLatency(cycle_total_ms=100.0)
    assert lat.rtf_e2e == 0.0
    assert lat.rtf_stream_e2e == 0.0
    assert lat.rtf_omni == 0.0


def test_aggregate_stage_ms_omni_max_gate_sum():
    """并发后 omni 取 max(墙钟一路)、gate/identity 仍 sum;避免 [perf] omni(Σ)>total 误导。"""
    from miloco.perception.processor import _aggregate_stage_ms

    timing = {
        "客厅/gate_camA_ms": 10.0,
        "客厅/gate_camB_ms": 6.0,
        "客厅/gate_video_camA_ms": 999.0,   # 子模态,不计入 gate 总
        "客厅/identity_camA_ms": 20.0,
        "客厅/identity_camB_ms": 30.0,
        "客厅/omni_camA_ms": 15494.0,
        "客厅/omni_camB_ms": 4202.0,
        "_device_trace_id_camA": "x",        # _ 前缀跳过
    }
    gate, identity, omni = _aggregate_stage_ms(timing)
    assert gate == 16.0           # sum(10+6),子模态 999 不计
    assert identity == 50.0       # sum(20+30)
    assert omni == 15494.0        # max(15494,4202),不是 19696(Σ)
