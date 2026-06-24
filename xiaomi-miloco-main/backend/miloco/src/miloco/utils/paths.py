"""Shared path helpers rooted at ``$MILOCO_HOME``.

``MILOCO_HOME`` is the single user-scoped root for all Miloco state:
``config.json``, logs, DB, supervisor sockets, perception cache, certs, etc.
Default is ``~/.openclaw/miloco``; override via the ``MILOCO_HOME`` env var.

This module intentionally has no dependency on the Pydantic settings module
so that early-boot code (logging setup, config discovery) can import it
without triggering ``get_settings()``.
"""

from __future__ import annotations

import os
from pathlib import Path

_DEFAULT_MILOCO_HOME = Path.home() / ".openclaw" / "miloco"


def miloco_home() -> Path:
    """Return the resolved ``$MILOCO_HOME`` directory.

    - Reads the ``MILOCO_HOME`` environment variable each call (not cached),
      so tests using ``monkeypatch.setenv`` see fresh values immediately.
    - ``~`` is expanded via :meth:`Path.expanduser`.
    - Falls back to ``~/.openclaw/miloco`` when the env var is unset.
    """
    if env := os.environ.get("MILOCO_HOME"):
        return Path(env).expanduser()
    return _DEFAULT_MILOCO_HOME


def config_file() -> Path:
    """Return ``$MILOCO_HOME/config.json`` (shared nested config file)."""
    return miloco_home() / "config.json"
