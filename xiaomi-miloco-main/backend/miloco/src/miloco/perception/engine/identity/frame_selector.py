"""Edge Layer — Frame Selector.

DEPRECATED: omni 主链路不再做帧筛选。仅 ``run_stream_test.py`` 暂时保留引用，
待按新管线重写后将一并删除。
"""

from __future__ import annotations

import warnings

from miloco.perception.engine.config import IdentityConfig
from miloco.perception.engine.types import FrameResolution, MotionState, TrackingBoxInfo

warnings.warn(
    "frame_selector is deprecated; the omni pipeline no longer selects frames locally.",
    DeprecationWarning,
    stacklevel=2,
)


def select_frames(
    total_frames: int,
    scene_motion: MotionState,
    all_box_info: list[list[TrackingBoxInfo]],
    config: IdentityConfig,
) -> list[tuple[int, FrameResolution]]:
    """Select frames to crop targets from.

    Static:  1 frame (best bbox area) for cropping.
    Dynamic: up to 3 frames from detected frames for cropping.
             If <=3 detected frames, send all; otherwise evenly sample 3.

    The panoramic image (first frame, short-edge 512) is always sent
    by prompt_builder independently.
    """
    detected = _frames_with_detections(all_box_info)

    if scene_motion == MotionState.STATIC:
        if detected:
            best = _find_best_frame(total_frames, all_box_info)
            return [(best, FrameResolution(config.static_frame_resolution))]
        return [(0, FrameResolution(config.static_frame_resolution))]

    # Dynamic
    if not detected:
        return [(0, FrameResolution(config.dynamic_frame_resolution))]

    indices = _sample_up_to_three(detected)
    return [(i, FrameResolution(config.dynamic_frame_resolution)) for i in indices]


def _frames_with_detections(all_box_info: list[list[TrackingBoxInfo]]) -> list[int]:
    """Collect sorted, deduplicated frame indices that have any bbox."""
    indices: set[int] = set()
    for obj_boxes in all_box_info:
        for b in obj_boxes:
            if b.boxes:
                indices.add(b.frame_index)
    return sorted(indices)


def _sample_up_to_three(candidates: list[int]) -> list[int]:
    """If <=3, return all. Otherwise evenly sample 3 (first, middle, last)."""
    if len(candidates) <= 3:
        return list(candidates)
    return [candidates[0], candidates[len(candidates) // 2], candidates[-1]]


def _find_best_frame(total_frames: int, all_box_info: list[list[TrackingBoxInfo]]) -> int:
    best_index = 0
    best_area = 0

    for frame_idx in range(total_frames):
        total_area = 0
        for obj_boxes in all_box_info:
            for b in obj_boxes:
                if b.frame_index == frame_idx:
                    bbox = b.boxes.get("human_body") or b.boxes.get("pet_body") or b.boxes.get("human_face")
                    if bbox:
                        total_area += bbox[2] * bbox[3]
        if total_area > best_area:
            best_area = total_area
            best_index = frame_idx

    return best_index
