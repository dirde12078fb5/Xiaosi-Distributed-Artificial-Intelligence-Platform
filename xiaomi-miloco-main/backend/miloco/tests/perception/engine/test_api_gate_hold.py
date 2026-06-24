"""Section 7.4 D 矩阵 — PerceptionEngine 持 gate hold 状态 + reset_session。"""


from miloco.perception.engine.api import PerceptionEngine
from miloco.perception.engine.config import PerceptionConfig


def _make_engine() -> PerceptionEngine:
    """直接构造引擎实例,不依赖 omni / 模型外部资源。"""
    return PerceptionEngine(PerceptionConfig())


def test_D1_init_empty_dicts():
    eng = _make_engine()
    assert eng._gate_last_visual_pass_ts == {}
    assert eng._gate_last_audio_pass_ts == {}


def test_D2_reset_session_clears():
    eng = _make_engine()
    eng._gate_last_visual_pass_ts["camA"] = 100.0
    eng._gate_last_audio_pass_ts["camA"] = 100.0
    eng.reset_session()
    assert eng._gate_last_visual_pass_ts == {}
    assert eng._gate_last_audio_pass_ts == {}


# D3/D4 跨调用 hold + 多 device 隔离已由 test_pipeline.py::TestGateHoldPipelineIntegration
# C1/C2 等价覆盖(同 run_batch_pipeline 路径,realtime_perceive 只是薄包装)。
# api 层独立单元在 D1/D2 已验证持状态 / reset_session 清。
