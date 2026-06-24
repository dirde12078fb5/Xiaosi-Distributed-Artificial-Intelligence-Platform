"""get_reid_extractor 兜底路径单测(本 MR 修复: 相对→绝对模型路径 + session 加载校验)。

不全量构造 PerceptionEngine, 以未绑定方法 + fake self 直接驱动 get_reid_extractor,
monkeypatch HumanReID 控制加载结果。验证两点回归:
  1. 兜底用解析后的**绝对**路径(而非 HumanReID 默认相对 "models/..."), 与活动 tracker 同口径;
  2. 加载失败(session is None)时返 None、且不缓存坏实例(否则后续 extract_feature 会全报
     "模型未初始化")。
"""
from __future__ import annotations

from types import SimpleNamespace

from miloco.perception.engine.api import PerceptionEngine

_HUMAN_REID = "miloco.perception.engine.identity.tracker.human_reid.HumanReID"


def _fake_engine(model_dir: str) -> SimpleNamespace:
    # get_reid_extractor 仅访问这三个属性 + 回写 _fallback_human_reid
    return SimpleNamespace(
        _deep_sort_trackers={},
        _fallback_human_reid=None,
        _config=SimpleNamespace(
            identity=SimpleNamespace(perception_model_dir=model_dir),
        ),
    )


def test_fallback_uses_resolved_abs_path_and_caches(monkeypatch):
    captured = {}

    class _FakeHumanReID:
        def __init__(self, model_path, use_gpu=False):
            captured["model_path"] = model_path
            self.session = object()  # 模拟加载成功

    monkeypatch.setattr(_HUMAN_REID, _FakeHumanReID)
    eng = _fake_engine("/models")

    inst = PerceptionEngine.get_reid_extractor(eng)

    # 解析成 model_dir/文件名 的绝对路径, 不是 HumanReID 默认相对 "models/..."
    assert captured["model_path"] == "/models/human_body_reid_v2.onnx"
    # 成功实例被返回并缓存
    assert inst is not None
    assert eng._fallback_human_reid is inst


def test_fallback_returns_none_and_not_cached_when_load_fails(monkeypatch):
    class _FakeHumanReID:
        def __init__(self, model_path, use_gpu=False):
            self.session = None  # 模拟 make_session 失败被 init() 静默吞

    monkeypatch.setattr(_HUMAN_REID, _FakeHumanReID)
    eng = _fake_engine("/models")

    inst = PerceptionEngine.get_reid_extractor(eng)

    # 加载失败 → 返 None、不缓存坏实例
    assert inst is None
    assert eng._fallback_human_reid is None
