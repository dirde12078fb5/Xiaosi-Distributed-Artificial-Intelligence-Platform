# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""home_profile 配置常量"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecayConfig:
    half_life: int
    floor: float
    expirable: bool


PROMOTE = {
    "min_evidence": 3,
    "min_span_days": 2,
    # 仅 confidence 满格(1.0，即 user_told 或已完全确认)才走快速通道，
    # 否则一律要求「≥3 次证据且跨度 ≥2 天」，避免单日高置信观察被秒提升。
    "min_confidence": 1.0,
    "expire_days": 30,
}

DECAY: dict[str, DecayConfig] = {
    "member_health": DecayConfig(365, 0.6, False),
    "member_persona": DecayConfig(365, 0.4, False),
    "family": DecayConfig(365, 0.3, False),
    "space": DecayConfig(365, 0.3, False),  # 户型/朝向近乎永久，不过期
    "device": DecayConfig(365, 0.2, True),  # 设备会更换，可过期
    "member_routine": DecayConfig(180, 0.0, True),
    "member_entertain": DecayConfig(180, 0.0, True),
    "member_preference": DecayConfig(365, 0.2, True),  # 偏好比行为习惯稳定
}

DEFAULT_DECAY = DecayConfig(180, 0.0, True)

SOURCE_BONUS = {"user_told": 2.0, "observed": 1.0}

# 用户明示的知识不应被静默衰减/过期：recency 下限抬高 + 豁免过期清理
USER_TOLD_FLOOR = 0.3

LIMITS = {
    "max_evidence_log": 10,
    "max_profile_tokens": 2000,
    "max_candidates": 500,
    "max_profile_entries": 300,
    "max_last_seen_days": 365,
}
