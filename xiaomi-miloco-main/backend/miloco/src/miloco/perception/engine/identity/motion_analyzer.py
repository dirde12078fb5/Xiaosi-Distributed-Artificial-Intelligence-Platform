"""Edge Layer — Motion Analyzer (static/dynamic classification).

DEPRECATED: 旧 motion_analyzer 已停用，omni 主链路不再使用 motion 分类。
仅 ``run_stream_test.py`` 暂时保留引用，待按新管线重写后将一并删除。
"""

from __future__ import annotations

import math
import warnings

from miloco.perception.engine.config import IdentityConfig
from miloco.perception.engine.types import (
    IdentityTarget,
    MotionState,
    ObjectType,
    TrackedObject,
    TrackingBoxInfo,
)

warnings.warn(
    "motion_analyzer is deprecated; the omni pipeline no longer uses motion classification.",
    DeprecationWarning,
    stacklevel=2,
)


def analyze_motion(objects: list[TrackedObject], config: IdentityConfig) -> tuple[list[IdentityTarget], MotionState]:
    """Analyze motion state of tracked objects. Returns (targets, scene_motion)."""
    has_dynamic = any(
        _classify_motion(obj.box_info, config.static_displacement_threshold) == MotionState.DYNAMIC
        for obj in objects
    )
    scene_motion = MotionState.DYNAMIC if has_dynamic else MotionState.STATIC
    targets = [_to_edge_target(obj) for obj in objects]
    return targets, scene_motion


def _to_edge_target(obj: TrackedObject) -> IdentityTarget:
    # IdentityTarget V2 已移除 face_id / motion_state；这里把旧 face_id 沿用为 person_id 以兼容遗留调用方
    needs_verify = (
        obj.type in (ObjectType.HUMAN, ObjectType.HUMAN_BODY, ObjectType.HUMAN_FACE)
        or obj.face_id.startswith("new_face_")
        or obj.face_id == "none"
    )
    return IdentityTarget(
        type=obj.type,
        person_id=obj.face_id,
        track_id=obj.track_id,
        needs_omni_verify=needs_verify,
        box_info=obj.box_info,
    )


def _classify_motion(box_info: list[TrackingBoxInfo], threshold: float) -> MotionState:
    """Classify motion using displacement relative to bbox size.

    Computes the ratio of center-point displacement to the bbox diagonal
    for consecutive frames. This is resolution-independent and also
    invariant to how far the target is from the camera.

    The threshold is interpreted as a percentage (e.g. 0.05 = 5% of bbox size).
    """
    if len(box_info) < 2:
        return MotionState.STATIC

    entries = []  # (center_x, center_y, diagonal)
    for b in box_info:
        bbox = b.boxes.get("human_body") or b.boxes.get("pet_body") or b.boxes.get("human_face")
        if bbox:
            cx = bbox[0] + bbox[2] / 2
            cy = bbox[1] + bbox[3] / 2
            diag = math.sqrt(bbox[2] ** 2 + bbox[3] ** 2)
            entries.append((cx, cy, diag))

    if len(entries) < 2:
        return MotionState.STATIC

    max_ratio = 0.0
    for i in range(1, len(entries)):
        dx = entries[i][0] - entries[i - 1][0]
        dy = entries[i][1] - entries[i - 1][1]
        disp = math.sqrt(dx * dx + dy * dy)
        avg_diag = (entries[i][2] + entries[i - 1][2]) / 2
        if avg_diag > 0:
            max_ratio = max(max_ratio, disp / avg_diag)

    return MotionState.DYNAMIC if max_ratio >= threshold else MotionState.STATIC
