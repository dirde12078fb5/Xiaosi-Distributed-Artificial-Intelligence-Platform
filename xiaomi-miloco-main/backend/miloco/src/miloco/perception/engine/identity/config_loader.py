"""Identity engine 配置加载入口。

config 分层：

    ``default_config.yaml``（模块级默认值，本目录）
        ↑ 被 ``settings.yaml::perception.engine.identity_engine`` override（可选）
        ↑ 被运行时调用方传入的 override dict override（可选）

最终通过 ``identity_engine_config_from_dict``（``engine/config.py``）转成
``IdentityEngineConfig`` 嵌套 dataclass 树。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from miloco.perception.engine.config import (
    IdentityEngineConfig,
    identity_engine_config_from_dict,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "default_config.yaml"


def load_identity_engine_config(
    override: dict[str, Any] | None = None,
    *,
    config_path: Path | None = None,
) -> IdentityEngineConfig:
    """加载 identity 默认配置，并允许 override dict 覆盖部分字段。

    Args:
        override:    可选的覆盖配置（典型来源：``settings.yaml`` 中
                     ``perception.engine.identity_engine`` 块）。深合并到默认值。
        config_path: 可选的默认配置 yaml 路径；None 时用 ``default_config.yaml``
                     （本模块同目录）。测试场景可指向其他文件。

    Returns:
        ``IdentityEngineConfig`` 嵌套 dataclass 树。
    """
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.exists():
        logger.warning(
            "Identity default config not found at %s; falling back to dataclass defaults",
            path,
        )
        config_dict: dict[str, Any] = {}
    else:
        with open(path, encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}
        if not isinstance(config_dict, dict):
            raise ValueError(
                f"{path} must deserialize to a mapping, got {type(config_dict)!r}"
            )

    if override:
        config_dict = _deep_merge(config_dict, override)

    return identity_engine_config_from_dict(config_dict)


def resolve_library_root() -> Path:
    """``library_root`` 的 single source of truth：加载 ``default_config.yaml``
    → 合并 ``settings.yaml::perception.engine.identity_engine`` override
    → 相对路径锚定到 ``settings.directories.workspace_dir`` → 绝对路径。

    所有需要构造 ``IdentityLibrary`` 的位置（router 的 ``_get_identity_library``、
    engine 工厂的 ``build_identity_engine``）都应通过本函数取路径，确保多端
    解析结果一致；任何一端绕开本函数（如直接读 ``GalleryConfigDC()`` 默认值）
    都会让 settings.yaml override 失效，导致两侧路径分裂、写读不在同一目录。
    """
    from miloco.config import get_settings

    settings = get_settings()
    engine_cfg = settings.perception.engine
    cfg = load_identity_engine_config(override=engine_cfg.get("identity_engine"))
    rel = Path(cfg.gallery.library_root)
    if rel.is_absolute():
        return rel
    return settings.directories.workspace_dir / rel


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """递归把 ``override`` 合到 ``base`` 之上（不修改入参）。

    - dict × dict → 递归合并
    - 其他场景 → ``override`` 整段替换 ``base``
    """
    result: dict[str, Any] = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result
