"""Unified initialization for both CLI and server environments."""

import datetime
import logging
import logging.config
import os
import sys

from miloco.config import get_settings
from miloco.utils.agent_config import ensure_backend_token
from miloco.utils.uvicorn import get_uvicorn_log_config

logger = logging.getLogger(__name__)


BOOT_FROM = None


def _redirect_stdio_to_file(log_path: str) -> None:
    """Replace process fd 1 & 2 with an append fd to log_path.

    After this call every write to stdout/stderr — including output from
    native C libraries that bypass Python's logging (e.g., ONNX Runtime) —
    flows into log_path. Python loggers configured with a StreamHandler on
    sys.stderr share the same fd, so there is a single writer to the file.
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    fd = os.open(log_path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.dup2(fd, 1)
        os.dup2(fd, 2)
    finally:
        os.close(fd)
    # Rebind sys.stdout/stderr so Python StreamHandlers see the new fd.
    sys.stdout = os.fdopen(1, "w", buffering=1)
    sys.stderr = os.fdopen(2, "w", buffering=1)


def bootstrap(target: str = "server", debug: bool = False) -> None:
    """Bootstrap: logging + shared token.

    Args:
        target: "cli" or "server"
        debug: when True, force console logging even in daemon mode.
    """
    global BOOT_FROM
    if BOOT_FROM:
        return
    BOOT_FROM = target

    # Ensure backend token exists & is published to $MILOCO_HOME/config.json.
    ensure_backend_token()

    settings = get_settings()

    # Daemon mode (stdout not a tty) → redirect stdio to a per-boot file so
    # native C stderr (ORT warnings, etc.) is captured alongside Python logger
    # output. Foreground/dev (tty) leaves stdio on the terminal — no file.
    if (
        target == "server"
        and not sys.stdout.isatty()
        and "debugpy" not in sys.modules
        and not os.environ.get("MILOCO_SUPERVISED")
    ):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(
            str(settings.directories.log_dir),
            f"{settings.app.service_name}_{timestamp}.log",
        )
        _redirect_stdio_to_file(log_path)

    log_config = get_uvicorn_log_config(
        enable_console_logging=True if debug else None,
    )
    logging.config.dictConfig(log_config)
