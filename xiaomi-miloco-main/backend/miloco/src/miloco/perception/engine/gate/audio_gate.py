"""Gate Layer — Audio Gate (frame-level energy threshold).

Uses frame-level energy detection (30ms frames) to avoid missing
short audio events diluted by surrounding silence in a 3s window.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from miloco.perception.engine.config import GateConfig

_FRAME_MS = 30  # Frame size for energy computation (ms)


def evaluate_audio(audio_clip: NDArray[np.int16], config: GateConfig) -> tuple[bool, float]:
    """Evaluate whether audio has meaningful energy above the noise floor.

    Uses peak frame energy instead of whole-clip RMS to detect short
    audio events within a longer window.

    Returns (active, energy_level).
    """
    if audio_clip.size == 0:
        return False, 0.0

    sample_rate = 16000  # Standard perception pipeline sample rate
    frame_size = int(sample_rate * _FRAME_MS / 1000)
    n_frames = audio_clip.size // frame_size

    if n_frames == 0:
        # Clip shorter than one frame — fall back to whole-clip RMS
        rms = compute_rms(audio_clip)
        normalized = min(1.0, rms / 32768.0)
        return normalized >= config.audio_energy_threshold, normalized

    # Compute per-frame RMS
    trimmed = audio_clip[: n_frames * frame_size].astype(np.float64)
    frames = trimmed.reshape(n_frames, frame_size)
    frame_rms = np.sqrt(np.mean(frames**2, axis=1))
    frame_energies = np.minimum(1.0, frame_rms / 32768.0)

    # Peak frame energy as representative level
    peak_energy = float(np.max(frame_energies))
    return peak_energy >= config.audio_energy_threshold, peak_energy


def compute_rms(samples: NDArray[np.int16]) -> float:
    """Compute Root Mean Square of PCM samples."""
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float64) ** 2)))
