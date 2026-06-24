"""speech_vad.evaluate_speech 单测——含模型可用 / 缺失（优雅降级）两路。"""

from __future__ import annotations

import numpy as np
from miloco.perception.engine.config import GateConfig
from miloco.perception.engine.gate import speech_vad
from miloco.perception.engine.gate.speech_vad import evaluate_speech


class TestEvaluateSpeechDegrade:
    def test_disabled_returns_true(self):
        """关开关 → 不跑 VAD，恒判有人声（退回纯能量 gate 行为）。"""
        cfg = GateConfig(speech_vad_enabled=False)
        has, prob = evaluate_speech(np.zeros(16000, dtype=np.int16), cfg)
        assert has is True
        assert prob == 0.0

    def test_model_missing_returns_true(self, monkeypatch):
        """模型加载不到 → 优雅降级判有人声，绝不因 VAD 不可用吞掉真实语音。"""
        monkeypatch.setattr(speech_vad, "_get_session", lambda: None)
        cfg = GateConfig(speech_vad_enabled=True)
        has, prob = evaluate_speech(np.zeros(16000, dtype=np.int16), cfg)
        assert has is True

    def test_too_short_returns_false(self, monkeypatch):
        """音频不足一帧（512）→ 判无人声。"""
        monkeypatch.setattr(speech_vad, "_get_session", lambda: object())
        cfg = GateConfig(speech_vad_enabled=True)
        has, prob = evaluate_speech(np.zeros(100, dtype=np.int16), cfg)
        assert has is False
