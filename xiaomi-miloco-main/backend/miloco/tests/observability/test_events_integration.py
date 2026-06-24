from miloco.observability.context import reset_trace_id, set_trace_id
from miloco.observability.metrics_client import MetricsClient
from miloco.observability.metrics_db import connect


async def test_publish_event_in_cycle_auto_picks_trace_id(tmp_path):
    db = tmp_path / "obs.db"
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        token = set_trace_id("cycle-evt")
        try:
            client.publish_event("rule_match", "rule-1", {"reason": "x"})
            client.publish_event("suggestion", "fall", {"action": "ask"})
            client.publish_event("interaction", "user", {"content": "嗨"})
        finally:
            reset_trace_id(token)
        await client.flush()

        conn = connect(db)
        try:
            rows = conn.execute(
                "SELECT event_type, trace_id FROM events ORDER BY event_type"
            ).fetchall()
        finally:
            conn.close()
        assert rows == [
            ("interaction", "cycle-evt"),
            ("rule_match", "cycle-evt"),
            ("suggestion", "cycle-evt"),
        ]
    finally:
        await client.stop()


async def test_publish_event_background_when_no_contextvar(tmp_path):
    db = tmp_path / "obs.db"
    client = MetricsClient(db_path=db)
    await client.start()
    try:
        client.publish_event("rule_match", "bg-rule", {})
        await client.flush()
        conn = connect(db)
        try:
            row = conn.execute("SELECT trace_id FROM events").fetchone()
        finally:
            conn.close()
        assert row[0] is None
    finally:
        await client.stop()
