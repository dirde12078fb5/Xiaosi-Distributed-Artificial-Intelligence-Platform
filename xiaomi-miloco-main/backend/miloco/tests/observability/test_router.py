import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from miloco.observability.aggregate import aggregate_cycle
from miloco.observability.metrics_client import MetricsClient
from miloco.observability.metrics_db import connect, init_schema
from miloco.observability.router import router
from miloco.observability.types import (
    DecodeTrace,
    DeviceTraceRecord,
    GateTrace,
)


@pytest.fixture
def app_with_db(tmp_path):
    db = tmp_path / "obs.db"
    conn = connect(db)
    init_schema(conn)
    conn.close()
    client = MetricsClient(db_path=db)
    app = FastAPI()
    app.include_router(router)
    app.state.metrics_client = client
    app.state.obs_db_path = db
    return app, db, client


async def test_get_trace_returns_cycle_and_devices(app_with_db):
    app, _db, client = app_with_db
    await client.start()
    try:
        meta = dict(
            trace_id="c-2", timestamp=200,
            in_delay_ms=0, out_delay_ms=0,
            decode_ms=0, collect_ms=0, convert_ms=0, log_ms=0,
            cycle_total_ms=10, pipeline_total_ms=5,
            window_duration_ms=3000,
            window_first_frame_recv_ms=None, stream_lag_ms=None,
        )
        devices = [DeviceTraceRecord(
            device_trace_id="dt-2", cycle_id="c-2", timestamp=200,
            device_id="d2", room_name="r2",
            decode=DecodeTrace(1.0, 1.0, 10, 10),
            gate=GateTrace(1.0, 0.5, 0.5, True, False, False),
        )]
        client.publish_trace(aggregate_cycle(devices, meta), devices)
        await client.flush()

        with TestClient(app) as tc:
            r = tc.get("/api/trace/c-2")
        assert r.status_code == 200
        data = r.json()
        assert data["cycle"]["trace_id"] == "c-2"
        assert len(data["devices"]) == 1
        assert data["devices"][0]["device_id"] == "d2"
    finally:
        await client.stop()


async def test_list_traces_filters(app_with_db):
    app, _db, client = app_with_db
    await client.start()
    try:
        for i, tid in enumerate(["x-1", "x-2", "x-3"]):
            meta = dict(
                trace_id=tid, timestamp=1000 + i,
                in_delay_ms=0, out_delay_ms=0,
                decode_ms=0, collect_ms=0, convert_ms=0, log_ms=0,
                cycle_total_ms=10, pipeline_total_ms=5,
                window_duration_ms=3000,
                window_first_frame_recv_ms=None, stream_lag_ms=None,
            )
            devs = [DeviceTraceRecord(
                device_trace_id=f"dt-{i}", cycle_id=tid, timestamp=1000 + i,
                device_id="d", room_name="r",
                decode=DecodeTrace(1, 1, 1, 1),
                gate=GateTrace(0, 0, 0, False, False, True),
            )]
            client.publish_trace(aggregate_cycle(devs, meta), devs)
        await client.flush()

        with TestClient(app) as tc:
            r = tc.get("/api/traces?limit=2")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 2
        assert rows[0]["trace_id"] == "x-3"
    finally:
        await client.stop()
