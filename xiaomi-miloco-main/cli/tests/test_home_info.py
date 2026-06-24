"""home_info.py 测试：校验逻辑、类型推断、设备过滤。"""

from datetime import UTC, datetime

import pytest

from miloco_cli.home_info import (
    ValidationError,
    infer_value,
    list_devices,
    list_persons,
    list_scenes,
    validate_did,
    validate_iid,
    validate_value,
)

# ─── 测试用 home_info 数据 ────────────────────────────────────────────────────

_FAKE_INFO = {
    "updated_at": datetime.now(UTC).isoformat(),
    "devices": [
        {
            "did": "lamp_001",
            "name": "客厅台灯",
            "room": "客厅",
            "category": "light",
            "online": True,
            "spec": {
                "prop.2.1": {"type": "bool"},
                "prop.2.2": {"type": "int", "value_range": [0, 100]},
            },
        },
        {
            "did": "ac_001",
            "name": "卧室空调",
            "room": "卧室",
            "category": "ac",
            "online": False,
            "spec": {},
        },
        {
            "name": "无 did 设备",  # 故意缺少 did 键
            "room": "书房",
        },
    ],
    "scenes": [{"id": "scene_001", "name": "回家模式"}],
    "persons": [{"id": "p1", "name": "爸爸"}],
}


@pytest.fixture(autouse=True)
def mock_home_info(monkeypatch):
    """Mock _fetch to avoid real API calls in tests."""
    monkeypatch.setattr(
        "miloco_cli.home_info._fetch",
        lambda **kwargs: _FAKE_INFO,
    )


# ─── validate_did ─────────────────────────────────────────────────────────────


def test_validate_did_found():
    dev = validate_did("lamp_001", _FAKE_INFO)
    assert dev["name"] == "客厅台灯"


def test_validate_did_not_found():
    with pytest.raises(ValidationError, match="did 'unknown' not found"):
        validate_did("unknown", _FAKE_INFO)


def test_validate_did_handles_missing_did_key():
    """C3 修复：设备字典缺少 did 键不应抛 KeyError。"""
    info = {"devices": [{"name": "no-did-device"}]}
    with pytest.raises(ValidationError):
        validate_did("anything", info)


# ─── validate_iid ─────────────────────────────────────────────────────────────


def test_validate_iid_found():
    spec = validate_iid("lamp_001", "prop.2.1", _FAKE_INFO)
    assert spec["type"] == "bool"


def test_validate_iid_not_found():
    with pytest.raises(ValidationError, match="iid 'prop.9.9' not in spec"):
        validate_iid("lamp_001", "prop.9.9", _FAKE_INFO)


def test_validate_iid_empty_spec_skips_validation():
    """spec 为空时跳过校验，返回空 dict。"""
    result = validate_iid("ac_001", "prop.any", _FAKE_INFO)
    assert result == {}


def test_validate_iid_non_dict_spec_skips():
    """M15 修复：spec 不是 dict 时跳过校验，不应报 TypeError。"""
    info = {
        "devices": [{"did": "x", "spec": ["not", "a", "dict"]}]
    }
    result = validate_iid("x", "prop.1.1", info)
    assert result == {}


# ─── validate_value ───────────────────────────────────────────────────────────


def test_validate_value_in_range():
    validate_value({"value_range": [0, 100]}, 50)  # 不应抛异常


def test_validate_value_out_of_range():
    with pytest.raises(ValidationError, match="out of range"):
        validate_value({"value_range": [0, 100]}, 150)


def test_validate_value_boundary():
    validate_value({"value_range": [0, 100]}, 0)
    validate_value({"value_range": [0, 100]}, 100)


def test_validate_value_no_range():
    validate_value({}, 999)  # 无 value_range，不校验


def test_validate_value_range_error_has_step_and_unit():
    """范围越界报错带上 step 与单位，方便改对。"""
    with pytest.raises(ValidationError, match=r"out of range \[16,30;1\] ℃"):
        validate_value({"value_range": [16, 30, 1], "unit": "℃"}, 40)


def test_validate_value_enum_valid():
    spec = {"value_list": [{"name": "Cool", "value": 2}, {"name": "Heat", "value": 5}]}
    validate_value(spec, 2)  # 合法枚举，不抛


def test_validate_value_enum_invalid_lists_allowed():
    """传错枚举 → 报错列出全部合法取值。"""
    spec = {"value_list": [{"name": "Cool", "value": 2}, {"name": "Heat", "value": 5}]}
    with pytest.raises(ValidationError, match="Cool=2, Heat=5"):
        validate_value(spec, 9)


def test_validate_value_non_numeric_skip():
    validate_value({"value_range": [0, 100]}, "on")  # 字符串跳过


def test_validate_value_short_range_no_crash():
    """Min21 修复：value_range 元素不足 2 时不应 IndexError。"""
    validate_value({"value_range": [0]}, 50)  # 不应抛异常


def test_validate_value_empty_range_no_crash():
    validate_value({"value_range": []}, 50)


# ─── infer_value ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("raw, expected", [
    ("true", True),
    ("True", True),
    ("TRUE", True),
    ("false", False),
    ("False", False),
    ("42", 42),
    ("-10", -10),
    ("3.14", 3.14),
    ("hello", "hello"),
    ("prop.2.1", "prop.2.1"),
    ("", ""),
])
def test_infer_value(raw, expected):
    assert infer_value(raw) == expected


def test_infer_value_returns_int_not_float_for_integer_string():
    result = infer_value("10")
    assert isinstance(result, int)


# ─── list helpers ─────────────────────────────────────────────────────────────


def test_list_devices_all():
    devices = list_devices()
    # 返回所有设备（含缺 did 的那条）
    assert any(d.get("did") == "lamp_001" for d in devices)


def test_list_devices_filter_room():
    devices = list_devices(room="客厅")
    assert all(d.get("room") == "客厅" for d in devices if "room" in d)
    assert len(devices) == 1


def test_list_devices_filter_online():
    devices = list_devices(online_only=True)
    assert all(d.get("online") for d in devices)


def test_list_devices_filter_category():
    devices = list_devices(category="ac")
    assert all(d.get("category") == "ac" for d in devices)


def test_list_scenes():
    scenes = list_scenes()
    assert scenes[0]["name"] == "回家模式"


def test_list_persons():
    persons = list_persons()
    assert persons[0]["name"] == "爸爸"
