import pytest
from miloco.observability.aggregate import aggregate_cycle
from miloco.observability.context import (
    reset_trace_id,
    set_trace_id,
)
from miloco.observability.metrics_client import MetricsClient
from miloco.observability.metrics_db import connect, init_schema
from miloco.observability.types import (
    DecodeTrace,
    DeviceTraceRecord,
    GateTrace,
    IdentityTrace,
    OmniTrace,
)


async def test_end_to_end_publish_via_aggregate(tmp_path):
    db = tmp_path / "obs.db"
    conn = connect(db)
    init_schema(conn)
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        token = set_trace_id("c-int-1")
        try:
            devices = [
                DeviceTraceRecord(
                    device_trace_id="dt-a", cycle_id="c-int-1", timestamp=100,
                    device_id="did-a", room_name="客厅",
                    decode=DecodeTrace(1.0, 2.0, 30, 15),
                    gate=GateTrace(2.0, 1.0, 1.0, True, False, False),
                    identity=IdentityTrace(ms=3.0),
                    omni=OmniTrace(ms=100.0),
                ),
                DeviceTraceRecord(
                    device_trace_id="dt-b", cycle_id="c-int-1", timestamp=100,
                    device_id="did-b", room_name="卧室",
                    decode=DecodeTrace(1.0, 2.0, 30, 0),
                    gate=GateTrace(1.0, 1.0, 0.0, True, True, False),
                    identity=IdentityTrace(ms=2.0),
                    omni=OmniTrace(ms=80.0, error_code="HTTP_500"),
                ),
            ]
            meta = dict(
                trace_id="c-int-1", timestamp=100,
                in_delay_ms=10.0, out_delay_ms=20.0,
                decode_ms=1.5, collect_ms=2.0, convert_ms=3.0, log_ms=4.0,
                cycle_total_ms=200.0, pipeline_total_ms=180.0,
                window_duration_ms=3000.0,
                window_first_frame_recv_ms=99000, stream_lag_ms=500.0,
            )
            cycle = aggregate_cycle(devices, meta)
            client.publish_trace(cycle, devices)
            client.publish_event(
                event_type="rule_match", source="离家提醒",
                payload={"rule_id": "r1"},
            )
            await client.flush()

            row = conn.execute(
                "SELECT trace_id, gate_ms, gate_video_pass, omni_error_count, "
                "       has_agent_turn FROM traces_v"
            ).fetchone()
            assert row[0] == "c-int-1"
            assert row[1] == 3.0
            assert row[2] == 1
            assert row[3] == 1
            assert row[4] == 0

            d_rows = conn.execute(
                "SELECT device_id, omni_error_code "
                "FROM traces_device WHERE cycle_id=? ORDER BY device_id",
                ("c-int-1",),
            ).fetchall()
            assert d_rows == [("did-a", None), ("did-b", "HTTP_500")]

            e_row = conn.execute(
                "SELECT event_type, trace_id, source FROM events"
            ).fetchone()
            assert e_row == ("rule_match", "c-int-1", "离家提醒")

            v_row = conn.execute(
                "SELECT rtf, rtf_pipeline, gate_passed FROM traces_v"
            ).fetchone()
            assert v_row[0] == pytest.approx(200.0 / 3000.0, abs=1e-3)
            assert v_row[1] == pytest.approx(180.0 / 3000.0, abs=1e-3)
            assert v_row[2] == 1
        finally:
            reset_trace_id(token)
    finally:
        await client.stop()
