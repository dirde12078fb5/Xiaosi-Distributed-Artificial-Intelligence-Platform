"""home_profile_loader.py — 进程内直读 canonical profile.md 注入 omni system prompt。

canonical 路径 ``$MILOCO_HOME/home-profile/profile.md`` 由 backend commit 时重写；
此处只读不渲染，缺失即注入空内容（不报错、不触发 render）。
"""

from __future__ import annotations

import logging

from miloco.home_profile.store import profile_md_path

logger = logging.getLogger(__name__)


def get_home_profile_prefix() -> str:
    """返回家庭背景信息（Home Profile）字符串，注入到 system prompt L1 层。"""
    profile_file = profile_md_path()
    if not profile_file.exists():
        return ""

    try:
        content = profile_file.read_text("utf-8")
    except Exception:
        logger.warning("读取家庭档案失败: %s", profile_file, exc_info=True)
        return ""

    body = content.strip()
    if not body:
        return ""
    return body
