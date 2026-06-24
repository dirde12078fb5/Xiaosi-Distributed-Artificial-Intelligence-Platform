# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""导出 settings 访问入口与资源文件常量。

使用方式：

    from miloco.config import get_settings
    host = get_settings().server.url
"""

from pathlib import Path

from miloco.config.settings import get_settings, register_reset_hook, reset_settings

SETTINGS_YAML: Path = Path(__file__).parent / "settings.yaml"
SETTINGS_SCHEMA: Path = Path(__file__).parent / "settings.schema.json"

__all__ = [
    "SETTINGS_SCHEMA",
    "SETTINGS_YAML",
    "get_settings",
    "register_reset_hook",
    "reset_settings",
]
