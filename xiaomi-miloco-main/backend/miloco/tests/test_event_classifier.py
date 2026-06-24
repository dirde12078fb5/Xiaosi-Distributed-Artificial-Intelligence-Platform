# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Unit tests for event_classifier(D3-T4)."""

from miloco.perception.event_classifier import classify
from miloco.perception.types import (
    CaptionEntry,
    MatchedRule,
    RealtimePerceptionResult,
    Speech,
    Suggestion,
)


def _result(
    *,
    captions: list[CaptionEntry] = None,
    rules: list[MatchedRule] = None,
    speeches: list[Speech] = None,
    suggestions: list[Suggestion] = None,
) -> RealtimePerceptionResult:
    return RealtimePerceptionResult(
        caption=captions or [],
        matched_rules=rules or [],
        speeches=speeches or [],
        suggestions=suggestions or [],
    )


def test_caption_only_not_meaningful():
    """纯 caption 不入表."""
    r = _result(captions=[CaptionEntry(description="有人在看电视")])
    res = classify(r)
    assert res == {
        "is_meaningful": False,
        "has_rule_hit": False,
        "has_suggestion": False,
        "has_asr": False,
    }


def test_empty_result_not_meaningful():
    res = classify(_result())
    assert res["is_meaningful"] is False


def test_rule_hit_only():
    r = _result(rules=[MatchedRule(rule_id="r1", reason="kitchen on")])
    res = classify(r)
    assert res == {
        "is_meaningful": True,
        "has_rule_hit": True,
        "has_suggestion": False,
        "has_asr": False,
    }


def test_suggestion_only():
    r = _result(suggestions=[Suggestion(event="高温", action="开空调")])
    res = classify(r)
    assert res["is_meaningful"] is True
    assert res["has_suggestion"] is True
    assert res["has_rule_hit"] is False
    assert res["has_asr"] is False


def test_asr_complete_needs_response():
    """needs_response=True AND is_complete=True → has_asr=True."""
    r = _result(
        speeches=[
            Speech(
                needs_response=True,
                speaker="用户",
                content="打开窗户",
                is_complete=True,
            )
        ]
    )
    res = classify(r)
    assert res["is_meaningful"] is True
    assert res["has_asr"] is True


def test_asr_chat_filtered():
    """needs_response=False(家人闲聊)不算 has_asr."""
    r = _result(
        speeches=[
            Speech(
                needs_response=False, speaker="妈妈", content="今天好热", is_complete=True
            )
        ]
    )
    res = classify(r)
    assert res["has_asr"] is False
    assert res["is_meaningful"] is False


def test_asr_incomplete_filtered():
    """status=incomplete 不算 has_asr."""
    r = _result(
        speeches=[
            Speech(
                needs_response=True, speaker="用户", content="打开", is_complete=False
            )
        ]
    )
    res = classify(r)
    assert res["has_asr"] is False


def test_asr_mixed_some_count():
    """多 Speech:只要有一个满足条件就 has_asr=True."""
    r = _result(
        speeches=[
            Speech(needs_response=False, speaker="A", content="闲聊", is_complete=True),
            Speech(needs_response=True, speaker="B", content="开灯", is_complete=True),
            Speech(needs_response=True, speaker="C", content="关...", is_complete=False),
        ]
    )
    res = classify(r)
    assert res["has_asr"] is True


def test_all_three_combined():
    """同一推理同时有 rule + suggestion + ASR → 三个 has_* 都 True,1 行 event."""
    r = _result(
        rules=[MatchedRule(rule_id="r1", reason="x")],
        suggestions=[Suggestion(event="e", action="a")],
        speeches=[
            Speech(needs_response=True, speaker="u", content="c", is_complete=True)
        ],
    )
    res = classify(r)
    assert res == {
        "is_meaningful": True,
        "has_rule_hit": True,
        "has_suggestion": True,
        "has_asr": True,
    }
