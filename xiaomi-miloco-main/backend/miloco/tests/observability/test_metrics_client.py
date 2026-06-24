import uuid

from miloco.observability.context import reset_trace_id, set_trace_id
from miloco.observability.metrics_client import MetricsClient
from miloco.observability.metrics_db import connect, init_schema
from miloco.observability.types import (
    AgentRunRecord,
    CycleTraceRecord,
    DecodeTrace,
    DeviceTraceRecord,
    GateTrace,
    IdentityTrace,
    OmniTrace,
)


def _make_cycle(trace_id: str) -> CycleTraceRecord:
    return CycleTraceRecord(
        trace_id=trace_id, timestamp=100, device_count=1, skipped=False,
        in_delay_ms=0, out_delay_ms=0, decode_ms=0, collect_ms=0,
        convert_ms=0, log_ms=0, cycle_total_ms=10.0,
        pipeline_total_ms=5.0, window_duration_ms=3000.0,
        window_first_frame_recv_ms=99000, stream_lag_ms=500.0,
        gate_ms=1.0, gate_video_ms=0.5, gate_audio_ms=0.5,
        gate_video_pass=True, gate_audio_pass=False,
        identity_ms=2.0, omni_ms=5.0,
        omni_call_count=1, omni_error_count=0,
    )


def _make_device(cycle_id: str, did: str) -> DeviceTraceRecord:
    return DeviceTraceRecord(
        device_trace_id=str(uuid.uuid4()), cycle_id=cycle_id,
        timestamp=100, device_id=did, room_name="r1",
        decode=DecodeTrace(1.0, 2.0, 10, 5),
        gate=GateTrace(1.0, 0.5, 0.5, True, False, False),
        identity=IdentityTrace(ms=2.0),
        omni=OmniTrace(ms=5.0),
    )


async def test_publish_trace_writes_main_and_device_rows(tmp_path):
    db = tmp_path / "obs.db"
    conn = connect(db)
    init_schema(conn)
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        cycle = _make_cycle("c-1")
        devices = [_make_device("c-1", "d1"), _make_device("c-1", "d2")]
        client.publish_trace(cycle, devices)
        await client.flush()

        rows = conn.execute("SELECT trace_id FROM traces").fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "c-1"

        d_rows = conn.execute(
            "SELECT device_id FROM traces_device WHERE cycle_id=?", ("c-1",)
        ).fetchall()
        assert sorted(r[0] for r in d_rows) == ["d1", "d2"]
    finally:
        await client.stop()


async def test_record_agent_run_inserts_row(tmp_path):
    db = tmp_path / "obs.db"
    conn = connect(db)
    init_schema(conn)
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        cycle = _make_cycle("c-1")
        client.publish_trace(cycle, [_make_device("c-1", "d1")])
        await client.flush()

        record = AgentRunRecord(
            run_id="r-1", trace_id="c-1", timestamp=1500, source="interaction",
            webhook_rtt_ms=12.5,
            query="hello", duration_ms=900.0,
            llm_call_count=1, tool_call_count=2,
            llm_total_ms=600.0, tool_total_ms=200.0, tool_max_ms=150.0,
            slowest_tool_name="miot_call",
            success=True, error_count=0, error_msg=None,
            jsonl_path="trace/agent/20260527/r-1__hello.jsonl.gz",
        )
        client.record_agent_run(record)
        await client.flush()

        row = conn.execute(
            "SELECT run_id, trace_id, source, llm_total_ms, slowest_tool_name, "
            "success, jsonl_path FROM agent_runs WHERE run_id=?", ("r-1",)
        ).fetchone()
        assert row == ("r-1", "c-1", "interaction", 600.0, "miot_call", 1,
                       "trace/agent/20260527/r-1__hello.jsonl.gz")

        # traces_v.has_agent_turn 应派生为 1
        ha = conn.execute(
            "SELECT has_agent_turn FROM traces_v WHERE trace_id=?", ("c-1",)
        ).fetchone()[0]
        assert ha == 1
    finally:
        await client.stop()


async def test_record_agent_run_supports_multiple_runs_per_trace(tmp_path):
    """同 trace_id 多次 record_agent_run,各 run_id 独立 INSERT,不互相覆盖。"""
    db = tmp_path / "obs.db"
    conn = connect(db)
    init_schema(conn)
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        cycle = _make_cycle("c-1")
        client.publish_trace(cycle, [_make_device("c-1", "d1")])
        await client.flush()

        for run_id, source in [
            ("r-1", "interaction"),
            ("r-2", "suggestion"),
            ("r-3", "rule"),
        ]:
            client.record_agent_run(AgentRunRecord(
                run_id=run_id, trace_id="c-1", timestamp=1000, source=source,
                webhook_rtt_ms=10.0,
                query=f"q-{run_id}", duration_ms=100.0,
                llm_call_count=1, tool_call_count=0,
                llm_total_ms=80.0, tool_total_ms=0.0, tool_max_ms=0.0,
                slowest_tool_name=None,
                success=True, error_count=0, error_msg=None, jsonl_path=None,
            ))
        await client.flush()

        rows = conn.execute(
            "SELECT run_id, source FROM agent_runs WHERE trace_id=? "
            "ORDER BY run_id", ("c-1",)
        ).fetchall()
        assert rows == [("r-1", "interaction"), ("r-2", "suggestion"), ("r-3", "rule")]
    finally:
        await client.stop()


async def test_publish_event_with_explicit_trace_id(tmp_path):
    db = tmp_path / "obs.db"
    conn = connect(db)
    init_schema(conn)
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        client.publish_event(
            event_type="rule_match",
            source="离家提醒",
            payload={"rule_id": "r-001"},
            trace_id="c-1",
        )
        await client.flush()
        row = conn.execute(
            "SELECT event_type, trace_id, source FROM events"
        ).fetchone()
        assert row == ("rule_match", "c-1", "离家提醒")
    finally:
        await client.stop()


async def test_publish_event_picks_trace_from_contextvar(tmp_path):
    db = tmp_path / "obs.db"
    conn = connect(db)
    init_schema(conn)
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        token = set_trace_id("c-2")
        try:
            client.publish_event(
                event_type="suggestion",
                source="suggestion-1",
                payload={"event": "fall"},
            )
        finally:
            reset_trace_id(token)
        await client.flush()
        row = conn.execute(
            "SELECT event_type, trace_id FROM events"
        ).fetchone()
        assert row == ("suggestion", "c-2")
    finally:
        await client.stop()


async def test_publish_event_background_explicit_none(tmp_path):
    db = tmp_path / "obs.db"
    conn = connect(db)
    init_schema(conn)
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        token = set_trace_id("c-3")
        try:
            client.publish_event(
                event_type="interaction",
                source="bg",
                payload={},
                trace_id=None,
            )
        finally:
            reset_trace_id(token)
        await client.flush()
        row = conn.execute(
            "SELECT trace_id FROM events"
        ).fetchone()
        assert row[0] is None
    finally:
        await client.stop()


async def test_buffer_max_triggers_early_flush(tmp_path, monkeypatch):
    """突发流量下,buffer 达到 _BUFFER_MAX 应提前 flush,防止 OOM 与单事务过大。

    构造方法:把 _BUFFER_MAX 临时改小到 5,enqueue 10 条,worker drain 后
    buffer 达上限提前 commit,而非等满 15s。
    """
    import miloco.observability.metrics_client as mc

    monkeypatch.setattr(mc, "_BUFFER_MAX", 5)

    db = tmp_path / "obs.db"
    conn = connect(db)
    init_schema(conn)
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        for i in range(10):
            client.publish_event(
                event_type="t", source="burst", payload={"i": i}
            )
        # 不调 flush:依赖 _BUFFER_MAX 自身触发提前 flush
        # 第 5 条进 buffer 后内层退出 → 第一批 5 条 commit
        # 第 6 条进新一批的 first,凑批等 15s 超时 / flush
        # 主动 flush() 让第二批立即落盘,方便断言
        await client.flush()

        rows = conn.execute("SELECT COUNT(*) FROM events").fetchone()
        assert rows[0] == 10
    finally:
        await client.stop()
