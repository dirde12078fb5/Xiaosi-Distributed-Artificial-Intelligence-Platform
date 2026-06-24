# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""home_profile schema — 条目模型 + API 请求体。

成员绑定（D3）：条目用 ``subject_id``(person_id, 可空) + ``subject_name``(兜底/展示)
取代旧的自由文本 ``subject``。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

EntryType = Literal[
    "member_persona",
    "member_health",
    "member_routine",
    "member_entertain",
    "member_preference",
    "family",
    "space",
    "device",
]
EntrySource = Literal["observed", "user_told"]
Target = Literal["profile", "candidates", "both"]

# 不绑定具体主体的预留 subject_name：member_* 用 "shared"（全家共享），
# space/device 用 "general"（通用）。渲染期归到「共享」/「通用」分组。
_RESERVED_SUBJECTS = frozenset({"shared", "general"})


class Entry(BaseModel):
    id: str
    type: EntryType
    subject_id: str | None = None
    subject_name: str | None = None
    content: str
    confidence: float
    evidence_count: int
    first_seen: str
    last_seen: str
    source: EntrySource
    evidence_log: list[str] = Field(default_factory=list)


class ProfileEntry(Entry):
    archived: bool = False


class CandidatesIndex(BaseModel):
    version: int = 1
    entries: list[Entry] = Field(default_factory=list)


class ProfileIndex(BaseModel):
    version: int = 1
    entries: list[ProfileEntry] = Field(default_factory=list)


# ─── op 请求体（移植 store.ts:95-118，subject → subject_id/subject_name）──────────


class EntryPayload(BaseModel):
    """新建条目的字段（不含 id/计数/时间戳，由 service 填充）。

    ``confidence``/``source`` 缺省为 ``0.5``/``observed``：``--user-edit`` 路径下
    可省略，service 会统一覆盖为 ``user_told``/``1.0``；观察路径（observe skill）
    每次都显式传真实证据强度，缺省仅作兜底。
    """

    type: EntryType
    subject_id: str | None = None
    subject_name: str | None = None
    content: str
    confidence: float = 0.5
    source: EntrySource = "observed"
    evidence_log: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _normalize_reserved_subject(self) -> "EntryPayload":
        # "shared"（全家共享）/"general"（通用空间·设备）是不绑定具体主体的预留值，
        # 约定 subject_id 留空；从源头消除 sentinel 与 person 绑定并存的歧义
        if self.subject_name in _RESERVED_SUBJECTS:
            self.subject_id = None
        return self


class EntryEdit(BaseModel):
    """表格直编 patch：所有字段可选，仅覆盖显式提供的字段。

    供 web 在表格里逐格订正（含计数/时间戳），不带 agent 的证据累加语义。
    依赖 ``model_fields_set`` 区分「置空」与「未提供」，故 subject_id/
    subject_name 可被显式设为 null 以清除主体绑定。
    """

    type: EntryType | None = None
    subject_id: str | None = None
    subject_name: str | None = None
    content: str | None = None
    confidence: float | None = None
    source: EntrySource | None = None
    evidence_count: int | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    evidence_log: list[str] | None = None


class CandidateOp(BaseModel):
    op: Literal["add", "merge", "update", "delete"]
    id: str | None = None
    date: str
    entry: EntryPayload | None = None
    edit: EntryEdit | None = None
    evidence_log: str | None = None
    confidence_delta: float | None = None


class ProfileOp(BaseModel):
    op: Literal["add", "merge", "replace", "update", "delete"]
    id: str | None = None
    date: str | None = None
    entry: EntryPayload | None = None
    edit: EntryEdit | None = None
    from_: str | None = Field(default=None, alias="from")
    evidence_log: str | None = None
    confidence_delta: float | None = None

    model_config = {"populate_by_name": True}


class CandidateWriteBody(BaseModel):
    ops: list[CandidateOp]


class ProfileWriteBody(BaseModel):
    ops: list[ProfileOp]
    user_edit: bool = False


class ReassignMapping(BaseModel):
    """把若干来源（旧 subject_name 或 subject_id）重指到统一目标主体。

    既用于成员的不同称呼 → 同一 person_id 绑定，也用于统一空间/设备等非成员的
    subject_name（此时 to_subject_id 留空，仅收敛名称）。
    """

    from_subject_ids: list[str] = Field(default_factory=list)
    from_subject_names: list[str] = Field(default_factory=list)
    to_subject_id: str | None = None
    to_subject_name: str | None = None


class ReassignBody(BaseModel):
    mappings: list[ReassignMapping]


class ImportBody(BaseModel):
    """迁移导入：整体写入旧结构条目，保留 id/时间戳/evidence/confidence/archived。"""

    profile: list[ProfileEntry] = Field(default_factory=list)
    candidates: list[Entry] = Field(default_factory=list)


class ResetBody(ImportBody):
    """测试场景重置：全量覆盖候选区+正式区，默认随即 commit 渲染 md。"""

    commit: bool = True


class OpResult(BaseModel):
    op: str
    id: str
    ok: bool
    message: str | None = None
