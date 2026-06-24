"""Utility functions for creating DeviceSnapshot from various sources."""

import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from miloco.perception.types import (
    AudioFrame,
    AudioStream,
    DeviceSnapshot,
    PerceptionDevice,
    VideoFrame,
    VideoStream,
)


def snapshot_from_video(
    file_path: str,
    device: PerceptionDevice,
    *,
    target_fps: float | None = None,
) -> DeviceSnapshot:
    """Create a DeviceSnapshot from a local video file.

    Extracts BGR frames via OpenCV and audio via ffmpeg.
    Useful for testing downstream tasks with local video files.

    Args:
        file_path: Path to video file.
        device: Device metadata to attach.
        target_fps: If set, subsample frames to this fps. None = use source fps.
    """
    import cv2

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {file_path}")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {file_path}")

    try:
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_frames / source_fps if source_fps > 0 else 0

        # Determine sampling interval
        effective_fps = target_fps if target_fps and target_fps < source_fps else source_fps
        sample_interval = max(1, int(source_fps / effective_fps)) if effective_fps > 0 else 1

        video_frames: list[VideoFrame] = []
        frame_w, frame_h = 0, 0

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_interval == 0:
                ts_ms = (frame_idx / source_fps * 1000) if source_fps > 0 else 0.0
                video_frames.append(VideoFrame(data=frame.astype(np.uint8), timestamp=ts_ms))
                if not frame_w:
                    frame_h, frame_w = frame.shape[:2]
            frame_idx += 1
    finally:
        cap.release()

    # Extract audio
    audio_samples = _extract_audio_pcm(str(path))

    now = time.time() * 1000
    start_ts = now - duration_sec * 1000
    end_ts = now

    video_stream: VideoStream | None = None
    if video_frames:
        video_stream = VideoStream(frames=video_frames, width=frame_w, height=frame_h)

    audio_stream: AudioStream | None = None
    if len(audio_samples) > 0:
        audio_stream = AudioStream(
            frames=[AudioFrame(data=audio_samples, timestamp=start_ts)],
            sample_rate=16000,
        )

    return DeviceSnapshot(
        device=device,
        start_timestamp=start_ts,
        end_timestamp=end_ts,
        video=video_stream,
        audio=audio_stream,
    )


def snapshot_from_arrays(
    device: PerceptionDevice,
    *,
    frames: list[NDArray[np.uint8]] | None = None,
    audio: NDArray[np.int16] | None = None,
    sample_rate: int = 16000,
    start_timestamp: float | None = None,
    end_timestamp: float | None = None,
) -> DeviceSnapshot:
    """Create a DeviceSnapshot from raw numpy arrays.

    Convenience factory for testing and non-ffmpeg data paths.
    """
    now = time.time() * 1000
    st = start_timestamp if start_timestamp is not None else now - 3000
    et = end_timestamp if end_timestamp is not None else now

    video_stream: VideoStream | None = None
    if frames:
        n = len(frames)
        video_frames = [
            VideoFrame(data=img, timestamp=(st + (et - st) * i / n if n > 1 else st)) for i, img in enumerate(frames)
        ]
        frame_h, frame_w = frames[0].shape[:2]
        video_stream = VideoStream(frames=video_frames, width=frame_w, height=frame_h)

    audio_stream: AudioStream | None = None
    if audio is not None and len(audio) > 0:
        audio_stream = AudioStream(
            frames=[AudioFrame(data=audio, timestamp=st)],
            sample_rate=sample_rate,
        )

    return DeviceSnapshot(
        device=device,
        start_timestamp=st,
        end_timestamp=et,
        video=video_stream,
        audio=audio_stream,
    )


def _extract_audio_pcm(file_path: str, sample_rate: int = 16000) -> NDArray[np.int16]:
    """Extract audio from video as 16kHz mono 16-bit PCM using ffmpeg."""
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=True) as tmp:
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    file_path,
                    "-vn",
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    str(sample_rate),
                    "-ac",
                    "1",
                    "-f",
                    "s16le",
                    tmp.name,
                    "-y",
                ],
                capture_output=True,
                check=True,
                timeout=30,
            )
            raw_bytes = Path(tmp.name).read_bytes()
            if len(raw_bytes) == 0:
                return np.array([], dtype=np.int16)
            return np.frombuffer(raw_bytes, dtype=np.int16)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return np.array([], dtype=np.int16)
