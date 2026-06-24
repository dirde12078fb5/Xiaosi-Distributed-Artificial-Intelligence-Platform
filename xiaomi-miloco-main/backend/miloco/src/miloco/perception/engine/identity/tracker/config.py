"""Tracker configuration（DeepSORT）。

历史背景：曾被精简为占位（旧 fast/ReID 字段都删了）因为新主路径走轻量 SortTracker
不需要 ReID。v1.2 主动注册改造重新启用 DeepSORT（MultiObjectTracker + HumanReID）+
陌生人池去重复用 DeepSORT 已算出的 ReID embedding，于是把 fast 模式相关字段加回。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrackerConfig:
    """MultiObjectTracker 用的配置。

    新轻量 SortTracker 用 ``miloco.perception.engine.identity.sort.SortConfig``。
    本类专给重启用的 DeepSORT 主路径（v1.2 主动注册改造）用。
    """

    # 基本档位与生命周期
    mode: str = "fast"                       # "normal" / "fast"（fast=静止 track 跳过 ReID 推理）
    max_age: int = 60                        # 帧；MultiObjectTracker 内部按帧数算 mark_missed

    # 关联（DeepSORT 标准）
    human_n_init: int = 1                    # 对齐 SortConfig.n_init=1（1 fps 主流程下不能太严）
    max_cosine_distance: float = 0.2
    max_iou_distance: float = 0.7
    human_init_confidence: float = 0.5
    human_max_lost_frames: int = 60
    max_human_targets: int = 8

    # fast 模式参数（tracker.py _is_track_static / _get_reid_interval / _extract_features_fast 用）
    static_displacement_ratio: float = 0.05  # 中心位移 / bbox 对角线 < 0.05 视为静止
    static_min_abs_px: float = 10.0          # 同时绝对位移 < 10 px
    human_reid_skip_windows: int = 4         # 静止人 N 个 window 抽一次 ReID
    window_len_sec: float = 1.0
    window_fps: int = 1
