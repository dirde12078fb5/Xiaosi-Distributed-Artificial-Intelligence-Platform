"""Tests for Gate Layer — Audio Gate."""

import numpy as np
from miloco.perception.engine.config import GateConfig
from miloco.perception.engine.gate.audio_gate import compute_rms, evaluate_audio


class TestComputeRms:
    def test_empty_samples(self):
        assert compute_rms(np.array([], dtype=np.int16)) == 0.0

    def test_known_signal(self):
        samples = np.array([100, -100, 100, -100], dtype=np.int16)
        assert compute_rms(samples) == 100.0


class TestEvaluateAudio:
    config = GateConfig()

    def test_silence(self):
        silence = np.zeros(16000, dtype=np.int16)
        active, energy = evaluate_audio(silence, self.config)
        assert not active
        assert energy == 0.0

    def test_loud_audio(self):
        loud = np.array(
            [int(np.sin(i * 0.1) * 10000) for i in range(16000)],
            dtype=np.int16,
        )
        active, energy = evaluate_audio(loud, self.config)
        assert active
        assert energy > 0.1

    def test_empty_buffer(self):
        active, energy = evaluate_audio(np.array([], dtype=np.int16), self.config)
        assert not active
        assert energy == 0.0
