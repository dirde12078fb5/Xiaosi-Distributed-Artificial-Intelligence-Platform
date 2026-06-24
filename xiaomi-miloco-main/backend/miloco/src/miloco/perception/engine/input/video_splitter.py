"""Data Input Layer — Video Splitter."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from miloco.perception.engine.config import InputConfig
from miloco.perception.engine.types import InputSlice
from miloco.perception.types import PerceptionDevice
from miloco.perception.utils import snapshot_from_arrays, snapshot_from_video


def split_video(file_path: str, room_name: str, config: InputConfig | None = None) -> InputSlice:
    """Split a video file into frames (BGR) + audio (PCM int16) using ffmpeg."""
    cfg = config or InputConfig()
    device = PerceptionDevice(did=room_name, name=room_name, device_type="camera", room_name=room_name)
    return snapshot_from_video(file_path, device, target_fps=cfg.fps)


def create_input_slice(
    room_name: str,
    frames: list[NDArray[np.uint8]],
    audio_clip: NDArray[np.int16],
    start_timestamp: float | None = None,
    end_timestamp: float | None = None,
) -> InputSlice:
    """Create an InputSlice from pre-loaded data (for testing / non-ffmpeg paths)."""
    device = PerceptionDevice(did=room_name, name=room_name, device_type="camera", room_name=room_name)
    return snapshot_from_arrays(
        device,
        frames=frames,
        audio=audio_clip,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )
