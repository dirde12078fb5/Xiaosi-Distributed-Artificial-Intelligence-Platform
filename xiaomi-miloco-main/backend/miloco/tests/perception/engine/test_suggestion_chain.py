"""事件链 assign_id_and_update_link 的链接 / 文案 / 紧急度维护逻辑测试。

去重链接已从"模型填 prev_id"改为"代码按 event 句向量语义匹配"（停注入历史后模型
不再填 prev_id）：本轮 event 与已有链 event 余弦 ≥ SUGG_SIM_THRESHOLD 即判为同一桩
持续事件。为不依赖真实 bge 模型、保持确定性，这里用 FakeEmbedder 把 event 按预设分组
映射到正交单位向量——同组 cos=1（必链），异组 cos=0（必不链）。

重点仍覆盖"心跳不漂移、升级才更新"：模型在链接轮自作主张写新文本时（同一持续事件的
措辞漂移），链条规范描述不应被刷掉（曾出现"揉眼睛"被刷成"操作电脑"的 drift bug）。
"""
from __future__ import annotations

import numpy as np
from miloco.perception.engine.api import PerceptionEngine
from miloco.perception.types import Suggestion


class _FakeEmbedder:
    """把 event 文本按预设分组映射到正交单位向量。

    同组 → 同向量（cos=1，≥阈值，必链）；异组 / 未登记 → 互相正交（cos=0，必不链）。
    """

    def __init__(self, groups: dict[str, str] | None = None):
        self._group = groups or {}
        self._basis: dict[str, np.ndarray] = {}

    def embed(self, text: str) -> np.ndarray:
        g = self._group.get(text, text)  # 未登记的 event 自成一组
        if g not in self._basis:
            v = np.zeros(32, dtype=np.float32)
            v[len(self._basis)] = 1.0
            self._basis[g] = v
        return self._basis[g]


def _engine(embedder=None) -> PerceptionEngine:
    """绕过重 __init__，只准备 assign_id_and_update_link 依赖的字段。

    默认不带 embedder（走精确文本匹配兜底）；传 FakeEmbedder 走语义匹配。
    """
    eng = object.__new__(PerceptionEngine)
    eng._sugg_table = {}
    eng._next_sugg_id = {}
    eng._embedder = embedder
    return eng


def _sugg(event, action="act", urgency="low") -> Suggestion:
    return Suggestion(event=event, action=action, urgency=urgency)


# 一组"同一持续事件的措辞漂移"——喂给 FakeEmbedder 视为同组（语义相同）
_DRIFT_GROUP = {
    "揉眼睛": "tired",
    "Ada在工位前操作电脑": "tired",
    "靠近刀具": "knife",
    "挥舞刀具": "knife",
}


def test_new_chain_reports_and_stores():
    eng = _engine(_FakeEmbedder())
    s = _sugg("揉眼睛", urgency="low")
    linked = eng.assign_id_and_update_link("room", s, now=100.0)
    assert linked is False  # 新链 → 上报
    assert s.id == 1
    assert eng._sugg_table["room"][1]["event"] == "揉眼睛"


def test_heartbeat_same_event_suppressed():
    """同一事件再次出现（语义命中已有链）→ 心跳，抑制上报。"""
    eng = _engine(_FakeEmbedder())
    eng.assign_id_and_update_link("room", _sugg("揉眼睛", urgency="low"), now=100.0)
    s = _sugg("揉眼睛", urgency="low")
    linked = eng.assign_id_and_update_link("room", s, now=110.0)
    assert linked is True  # 心跳 → 抑制上报
    assert s.id == 1
    assert len(eng._sugg_table["room"]) == 1  # 没开新链


def test_heartbeat_drifted_text_does_not_overwrite():
    """drift bug 回归：同紧急度、语义同链但模型写了漂移文本 → 链条描述保持不变。"""
    eng = _engine(_FakeEmbedder(_DRIFT_GROUP))
    eng.assign_id_and_update_link("room", _sugg("揉眼睛", urgency="low"), now=100.0)
    # 同一持续事件、措辞漂移（FakeEmbedder 判为同组 → 语义命中链）
    s = _sugg("Ada在工位前操作电脑", urgency="low")
    linked = eng.assign_id_and_update_link("room", s, now=110.0)
    assert linked is True
    assert eng._sugg_table["room"][1]["event"] == "揉眼睛"  # 未被刷掉
    assert s.event == "揉眼睛"  # 下游也拿到规范描述


def test_escalation_within_cooldown_updates_text_but_suppressed():
    """事态升级但仍在冷却内：刷新描述 + urgency（记录峰值），但不复报（没过 high 冷却）。

    新语义：升级本身不再强制复报；复报只看「距上次上报是否过了当前 urgency 的冷却」。
    """
    eng = _engine(_FakeEmbedder(_DRIFT_GROUP))
    eng.assign_id_and_update_link("room", _sugg("靠近刀具", urgency="low"), now=100.0)
    s = _sugg("挥舞刀具", urgency="high")  # 同组 → 语义命中链；升级到 high
    linked = eng.assign_id_and_update_link("room", s, now=110.0)  # 距首报仅 10s < 60s
    assert linked is True  # 没过 high 冷却(60s) → 抑制
    entry = eng._sugg_table["room"][1]
    assert entry["event"] == "挥舞刀具"      # 升级时更新描述
    assert entry["urgency"] == "high"


def test_escalation_to_high_rereports_after_high_cooldown():
    """升级到 high 后采用更短的 high 冷却(60s)：过了 60s 即复报，让 agent 重新惊动。"""
    eng = _engine(_FakeEmbedder(_DRIFT_GROUP))
    eng.assign_id_and_update_link("room", _sugg("靠近刀具", urgency="low"), now=100.0)  # 首报 low
    # 升级到 high，但距首报仅 10s < 60s → 抑制
    assert eng.assign_id_and_update_link("room", _sugg("挥舞刀具", urgency="high"), now=110.0) is True
    # 距上次上报(t=100) 已过 high 冷却 60s → 复报
    s = _sugg("挥舞刀具", urgency="high")
    assert eng.assign_id_and_update_link("room", s, now=161.0) is False  # 61s ≥ 60s
    assert s.urgency == "high"


def test_persistent_event_rereports_after_cooldown():
    """同一持续事件按 urgency 的冷却节奏周期复报：low=300s，冷却内抑制、过了才再上报。"""
    eng = _engine(_FakeEmbedder())
    assert eng.assign_id_and_update_link("room", _sugg("冰箱门敞开", urgency="low"), now=0.0) is False  # 首报
    # 冷却内的心跳全部抑制
    assert eng.assign_id_and_update_link("room", _sugg("冰箱门敞开", urgency="low"), now=100.0) is True
    assert eng.assign_id_and_update_link("room", _sugg("冰箱门敞开", urgency="low"), now=299.0) is True
    # 过了 low 冷却 300s → 复报一次
    assert eng.assign_id_and_update_link("room", _sugg("冰箱门敞开", urgency="low"), now=300.0) is False
    # 复报后重新进入冷却
    assert eng.assign_id_and_update_link("room", _sugg("冰箱门敞开", urgency="low"), now=400.0) is True


def test_downgrade_ignored_keeps_peak_urgency():
    """urgency 单调不降级：链接轮报更低 urgency → 忽略，沿用历史峰值，仍当心跳抑制。"""
    eng = _engine(_FakeEmbedder(_DRIFT_GROUP))
    eng.assign_id_and_update_link("room", _sugg("挥舞刀具", urgency="high"), now=100.0)
    s = _sugg("靠近刀具", urgency="low")  # 同组 → 命中链；urgency 更低
    linked = eng.assign_id_and_update_link("room", s, now=110.0)
    assert linked is True                        # 降级仍是心跳 → 抑制
    entry = eng._sugg_table["room"][1]
    assert entry["urgency"] == "high"            # 未被降到 low（单调不降级）
    assert s.urgency == "high"                   # 对外 urgency 对齐链条值


def test_dissimilar_event_opens_new_chain():
    """语义不同的事件 → 开新链并上报。"""
    eng = _engine(_FakeEmbedder())
    eng.assign_id_and_update_link("room", _sugg("男子在工位处喝水", urgency="low"), now=100.0)
    s = _sugg("玻璃破碎", urgency="high")  # 异组 → 不链
    linked = eng.assign_id_and_update_link("room", s, now=103.0)
    assert linked is False             # 不同事件 → 开新链
    assert s.id == 2
    assert len(eng._sugg_table["room"]) == 2


def test_empty_event_is_dropped():
    """event 为空 → 丢弃，不开空链、不上报（停注入历史后模型基本不会再产空 event，留作兜底）。"""
    eng = _engine(_FakeEmbedder())
    s = _sugg("", action="", urgency="low")
    linked = eng.assign_id_and_update_link("room", s, now=100.0)
    assert linked is True                        # 抑制上报
    assert eng._sugg_table.get("room", {}) == {}  # 没有开新链


def test_fallback_exact_match_when_no_embedder():
    """embedder 不可用时降级为精确文本匹配：同文本归并、不同文本开新链。"""
    eng = _engine(embedder=None)
    eng.assign_id_and_update_link("room", _sugg("男子在工位处喝水", urgency="low"), now=100.0)
    # 完全相同文本 → 精确匹配命中
    same = _sugg("男子在工位处喝水", urgency="low")
    assert eng.assign_id_and_update_link("room", same, now=103.0) is True
    assert same.id == 1
    assert len(eng._sugg_table["room"]) == 1
    # 不同文本 → 开新链
    other = _sugg("男子在工位处打哈欠", urgency="low")
    assert eng.assign_id_and_update_link("room", other, now=106.0) is False
    assert other.id == 2
    assert len(eng._sugg_table["room"]) == 2
