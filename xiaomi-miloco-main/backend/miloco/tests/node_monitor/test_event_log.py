
import pytest
from miloco.node_monitor.event_log import NodeEventLog


@pytest.fixture
def tmp_log_path(tmp_path):
    return str(tmp_path / "node_events.log")


class TestEventLogWrite:
    def test_writes_to_file(self, tmp_log_path):
        log = NodeEventLog(tmp_log_path)
        log.emit("engine", "STALLED", "no progress for 30s")
        log.emit("engine", "RECOVERED", "resumed after 30s stall")
        log.shutdown()

        with open(tmp_log_path) as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert "STALLED engine: no progress for 30s" in lines[0]
        assert "RECOVERED engine: resumed after 30s stall" in lines[1]

    def test_format_matches_spec(self, tmp_log_path):
        log = NodeEventLog(tmp_log_path)
        log.emit("processor", "STARTED", "lifecycle READY -> RUNNING")
        log.shutdown()

        with open(tmp_log_path) as f:
            line = f.readline().strip()
        # Format: {timestamp} {event} {node}: {message}
        parts = line.split(" ", 3)
        assert len(parts) == 4  # date, time, rest...


class TestEventLogQueueFull:
    def test_silent_drop_on_full_queue(self, tmp_log_path):
        log = NodeEventLog(tmp_log_path)
        # Fill queue beyond capacity — should not raise
        for i in range(2000):
            log.emit("test", "EVENT", f"msg {i}")
        log.shutdown()


class TestEventLogShutdown:
    def test_shutdown_flushes(self, tmp_log_path):
        log = NodeEventLog(tmp_log_path)
        for i in range(5):
            log.emit("node", "EVENT", f"item {i}")
        log.shutdown()

        with open(tmp_log_path) as f:
            lines = f.readlines()
        assert len(lines) == 5
