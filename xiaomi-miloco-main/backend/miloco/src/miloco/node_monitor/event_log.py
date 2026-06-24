from __future__ import annotations

import logging
import queue
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

_SENTINEL = object()

EVENT_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
EVENT_LOG_BACKUP_COUNT = 20


class NodeEventLog:
    """Writer thread + queue for node event audit logging.

    All public methods are safe to call from any thread.
    Disk I/O is isolated in the writer thread.
    """

    def __init__(self, log_path: str):
        self._queue: queue.Queue = queue.Queue(maxsize=1024)

        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger(f"node_events.{id(self)}")
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        handler = RotatingFileHandler(
            str(path),
            maxBytes=EVENT_LOG_MAX_BYTES,
            backupCount=EVENT_LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)

        self._thread = threading.Thread(
            target=self._writer_loop, name="node-event-writer", daemon=True
        )
        self._thread.start()

    def emit(self, node: str, event_type: str, message: str) -> None:
        # Naive local time, consistent with the rest of the backend logs.
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} {event_type} {node}: {message}"
        try:
            self._queue.put_nowait(line)
        except queue.Full:
            pass

    def shutdown(self) -> None:
        self._queue.put(_SENTINEL)
        self._thread.join(timeout=5)

    def _writer_loop(self) -> None:
        while True:
            item = self._queue.get()
            if item is _SENTINEL:
                break
            try:
                self._logger.info(item)
            except Exception:
                pass
