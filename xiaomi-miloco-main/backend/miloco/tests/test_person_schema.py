# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Person schema 校验回归测试。

覆盖 PersonCreate / PersonUpdate: name 去空白 + 拒空, role 空串归一化为 None,
PATCH 用 model_fields_set 区分 role "未传(不改)" 与 "传空(清空)"。
"""

import pytest
from miloco.person.schema import PersonCreate, PersonUpdate
from pydantic import ValidationError


def test_person_create_strips_name_and_role():
    p = PersonCreate(name="  李四  ", role="  爸爸  ")
    assert p.name == "李四"
    assert p.role == "爸爸"


def test_person_create_role_blank_to_none():
    assert PersonCreate(name="x", role="").role is None
    assert PersonCreate(name="x", role="   ").role is None
    assert PersonCreate(name="x").role is None


@pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
def test_person_create_rejects_blank_name(bad):
    with pytest.raises(ValidationError):
        PersonCreate(name=bad)


def test_person_update_name_none_passthrough():
    # PATCH 不带 name → name 为 None 表示不改, 不该被校验拦
    u = PersonUpdate(role=None)
    assert u.name is None


@pytest.mark.parametrize("bad", ["", "   "])
def test_person_update_rejects_blank_name(bad):
    with pytest.raises(ValidationError):
        PersonUpdate(name=bad)


def test_person_update_role_blank_to_none():
    assert PersonUpdate(role="").role is None


def test_person_update_role_fields_set_distinguishes_clear_vs_unset():
    # 路由靠 model_fields_set 区分"未传 role(本次不改)"与"显式传空/null(清空角色)":
    assert "role" not in PersonUpdate(name="x").model_fields_set       # 未传 → 不改
    u_empty = PersonUpdate(role="")                                    # 传空串 → 清空(归一 None)
    assert "role" in u_empty.model_fields_set and u_empty.role is None
    u_null = PersonUpdate(role=None)                                   # 传 null → 清空
    assert "role" in u_null.model_fields_set and u_null.role is None
    u_set = PersonUpdate(role="爸爸")                                   # 传值 → 设定
    assert "role" in u_set.model_fields_set and u_set.role == "爸爸"
