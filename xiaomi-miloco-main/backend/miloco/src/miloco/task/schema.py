# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""task / task_link 数据模型 — task SSOT（spec 2026-06-06）。"""

import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

_TASK_ID_RE = re.compile(r"^[a-z0-9_]{1,32}$")


class LinkKind(str, Enum):
    """``task_link.link_kind`` 取值。方案 P 后 ``memory`` 移除——record 不进
    task_link，FK 直连 task；rule / cron 仍保留。"""

    RULE = "rule"
    CRON = "cron"


class TaskCreateRequest(BaseModel):
    """``POST /tasks`` 入参（方案 P 倒序）。

    body 收窄为 ``{task_id, description}``——task create 仅建占位 task 行，
    rule / cron / record 关联挂载由后续 endpoint 完成：

    - rule create endpoint 内部一笔事务 INSERT rule + INSERT task_link
    - ``POST /tasks/{id}/link`` agent 显式挂 cron
    - ``POST /tasks/{id}/record`` record 不走 task_link（FK 直连 task）

    旧 ``rule_refs / cron_refs / memory_refs`` 字段全部移除（``extra='forbid'``
    拒绝 unknown field，旧 caller 调用会 422）。
    """

    model_config = {"extra": "forbid"}

    task_id: str = Field(..., description="snake_case，[a-z0-9_]{1,32}")
    description: str = Field(..., max_length=200, description="≤200 字符")

    @field_validator("task_id")
    @classmethod
    def _validate_task_id(cls, v: str) -> str:
        if not _TASK_ID_RE.match(v):
            raise ValueError(
                f"task_id 必须匹配 [a-z0-9_]{{1,32}}，收到: {v!r}"
            )
        return v


class TaskLinkAddRequest(BaseModel):
    """``POST /tasks/{task_id}/links`` 追加单条 link 行（保留 endpoint 兼容）。

    方案 P 下 link_kind 收窄到 ``rule | cron``——``memory`` 不再合法。
    """

    kind: Literal["rule", "cron"]
    ref: str = Field(..., min_length=1)


class TaskUpdateRequest(BaseModel):
    """`PATCH /tasks/{task_id}` 改 description。"""

    description: str = Field(..., max_length=200)


class RuleBrief(BaseModel):
    """`task get` / `task list` 中的实时 rule 摘要。"""

    rule_id: str
    query: str
    actions_desc: list[str] = Field(default_factory=list)


class TaskLinkEntry(BaseModel):
    kind: Literal["rule", "cron"]
    ref: str


class TaskFullView(BaseModel):
    """`GET /tasks/{task_id}` 返回。"""

    task_id: str
    description: str
    status: Literal["active", "paused"]
    paused_at: str | None = None
    created_at: str
    rule_briefs: list[RuleBrief] = Field(default_factory=list)
    links: list[TaskLinkEntry] = Field(default_factory=list)


class PendingOp(BaseModel):
    """agent 待执行的 cron 操作（方案 P 后 memory 类已移除）。"""

    kind: Literal["cron"]
    ref: str
    action: Literal[
        "disable",
        "enable",
        "remove",
    ]


class BackendSyncRuleResult(BaseModel):
    rule_id: str
    result: Literal["ok", "fail", "not_found"]


class BackendSyncResult(BaseModel):
    meta_status: Literal["ok", "noop"]
    rules: list[BackendSyncRuleResult] = Field(default_factory=list)


class TaskDisableResult(BaseModel):
    task_id: str
    status: Literal["active", "paused"]
    backend_synced: BackendSyncResult
    agent_pending: list[PendingOp] = Field(default_factory=list)


class TaskDeleteBackendSynced(BaseModel):
    rules_deleted: list[str] = Field(default_factory=list)
    task_link_rows_deleted: int = 0


class TaskDeleteResult(BaseModel):
    task_id: str
    backend_synced: TaskDeleteBackendSynced
    agent_pending: list[PendingOp] = Field(default_factory=list)


# ── task summary 视图(spec 2026-06-11) ──────────────────────────────────────


class WindowRemaining(BaseModel):
    """距当前 window 边界(当日 24:00 上海时区)的剩余时间。

    window='all' 时上层传 None,本对象不构造。
    """

    seconds: int
    display: str


class ActiveSession(BaseModel):
    """duration kind 当前活跃 session;非 duration kind 恒为 None。"""

    started_at: str
    elapsed_minutes: int


class RecordSummary(BaseModel):
    """summary 接口里单个 task 的 record 摘要。

    derived 字段按 kind 不同形态不同(progress/duration/event),
    由 ``TaskRecordService.list_active_summaries`` 拼装。
    """

    kind: Literal["progress", "duration", "event"]
    completed: bool
    active_session: ActiveSession | None
    window_remaining: WindowRemaining | None
    derived: dict[str, Any]


class TaskSummaryView(TaskFullView):
    """summary 接口返回的单条 view,继承 TaskFullView 全部字段 + 追加 record。"""

    record: RecordSummary | None = None
