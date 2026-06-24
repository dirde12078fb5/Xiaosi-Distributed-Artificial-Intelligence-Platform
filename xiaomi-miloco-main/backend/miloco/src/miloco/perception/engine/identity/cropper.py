"""Edge Layer — Cropper (bbox + padding → crop image).

DEPRECATED: omni 主链路不再使用本地 crop。仅 ``run_stream_test.py`` 暂时保留引用，
待按新管线重写后将一并删除。
"""

from __future__ import annotations

import warnings

import numpy as np
from numpy.typing import NDArray

from miloco.perception.engine.config import IdentityConfig
from miloco.perception.engine.types import CropImage, FrameResolution, TrackingBoxInfo

warnings.warn(
    "cropper is deprecated; the omni pipeline no longer pre-crops targets.",
    DeprecationWarning,
    stacklevel=2,
)


def crop_targets(
    frame: NDArray[np.uint8],
    frame_index: int,
    targets: list[dict],
    resolution: FrameResolution,
    config: IdentityConfig,
) -> list[CropImage]:
    """Crop target regions from a frame based on bounding boxes."""
    h, w = frame.shape[:2]
    if h == 0 or w == 0:
        return []

    crops: list[CropImage] = []

    for target in targets:
        box_entry: TrackingBoxInfo | None = None
        for b in target["box_info"]:
            if b.frame_index == frame_index:
                box_entry = b
                break

        if box_entry is None:
            continue

        bbox = box_entry.boxes.get("human_body") or box_entry.boxes.get("pet_body") or box_entry.boxes.get("human_face")
        if bbox is None:
            continue

        bx, by, bw, bh = bbox
        pad_x = round(bw * config.crop_padding_ratio)
        pad_y = round(bh * config.crop_padding_ratio)

        left = max(0, bx - pad_x)
        top = max(0, by - pad_y)
        right = min(w, bx + bw + pad_x)
        bottom = min(h, by + bh + pad_y)

        if right <= left or bottom <= top:
            continue

        cropped = frame[top:bottom, left:right].copy()
        crops.append(CropImage(track_id=target["track_id"], image=cropped, resolution=resolution))

    return crops
