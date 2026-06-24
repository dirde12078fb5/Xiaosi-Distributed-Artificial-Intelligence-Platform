# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""task schema 校验测试（方案 P 后）：task_id 字符集 / description 长度 /
link_kind 枚举（移除 memory）/ TaskCreateRequest body 收窄（拒 refs 字段）。
"""

import pytest
from miloco.task.schema import (
    LinkKind,
    TaskCreateRequest,
    TaskLinkAddRequest,
)
from pydantic import ValidationError


def test_task_id_must_be_snake_case_ascii():
    with pytest.raises(ValidationError):
        TaskCreateRequest(task_id="DrinkWater", description="x")
    with pytest.raises(ValidationError):
        TaskCreateRequest(task_id="喝水", description="x")
    with pytest.raises(ValidationError):
        TaskCreateRequest(task_id="", description="x")
    with pytest.raises(ValidationError):
        TaskCreateRequest(task_id="a" * 33, description="x")
    # OK
    TaskCreateRequest(task_id="drink_water", description="x")


def test_description_max_200():
    with pytest.raises(ValidationError):
        TaskCreateRequest(task_id="t", description="x" * 201)
    TaskCreateRequest(task_id="t", description="x" * 200)


def test_refs_fields_rejected_as_unknown():
    """方案 P：refs 字段全部移除，body 含 refs 返 422 unknown_field。"""
    for forbidden in ("rule_refs", "cron_refs", "memory_refs"):
        with pytest.raises(ValidationError):
            TaskCreateRequest.model_validate(
                {"task_id": "t", "description": "x", forbidden: ["r1"]}
            )


def test_empty_task_now_allowed():
    """方案 P：空 task 合法（refs 还未挂时即为空）。"""
    TaskCreateRequest(task_id="t", description="x")


def test_link_kind_enum_no_memory():
    """方案 P：``memory`` 移除，仅 rule / cron。"""
    assert LinkKind.RULE.value == "rule"
    assert LinkKind.CRON.value == "cron"
    assert "MEMORY" not in LinkKind.__members__


def test_task_link_add_request_validates_kind():
    TaskLinkAddRequest(kind="rule", ref="r1")
    TaskLinkAddRequest(kind="cron", ref="job1")
    with pytest.raises(ValidationError):
        TaskLinkAddRequest(kind="memory", ref="x")  # 方案 P 已移除
    with pytest.raises(ValidationError):
        TaskLinkAddRequest(kind="task", ref="x")
    with pytest.raises(ValidationError):
        TaskLinkAddRequest(kind="rule", ref="")
