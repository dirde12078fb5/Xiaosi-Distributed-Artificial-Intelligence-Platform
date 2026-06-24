# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Person schema definitions."""

from pydantic import BaseModel, Field, field_validator


def _normalize_optional_str(v: str | None) -> str | None:
    """把空串 / 纯空白归一化为 None——role 只该装真实家庭角色，不该装空白占位。"""
    if v is None:
        return None
    v = v.strip()
    return v or None


def _require_nonempty_name(v: str | None) -> str | None:
    """name 是人物真名、必填唯一标识：去空白后不可为空。None 透传（PATCH 不改 name）。"""
    if v is None:
        return None
    v = v.strip()
    if not v:
        raise ValueError("name 不可为空")
    return v


class PersonCreate(BaseModel):
    name: str = Field(min_length=1)
    role: str | None = None

    _strip_name = field_validator("name")(_require_nonempty_name)
    _norm_role = field_validator("role")(_normalize_optional_str)


class PersonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    role: str | None = None

    _strip_name = field_validator("name")(_require_nonempty_name)
    _norm_role = field_validator("role")(_normalize_optional_str)


class Person(BaseModel):
    id: str
    name: str
    role: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    # v2 起,"该人是否录了人脸/声纹"不再由 DB 字段表达——人脸样本落在
    # identity_lib/persons/<id>/tier_a/face_* 图像,真实数量经
    # /api/identity/persons/<id>/samples/montage 的 face_count 字段查;
    # 声纹这期完全不存,后续重启再加。
