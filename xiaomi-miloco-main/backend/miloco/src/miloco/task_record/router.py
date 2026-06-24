# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""task_record / task_link HTTP 路由（spec 2026-06-10 §5.2）。

8 个 endpoint：
- ``POST /tasks/{task_id}/link``                      cron 显式挂 task_link（方案 P 阶段 B）
- ``POST /tasks/{task_id}/record``                    record 初始化（方案 P 阶段 A'）
- ``GET  /tasks/{task_id}/record``                    读活跃 record + 子表 + derived
- ``PATCH /tasks/{task_id}/record``                   白名单字段更新
- ``POST /tasks/{task_id}/record/compute``            派生量（含历史日期 / 跨窗口）
- ``POST /tasks/{task_id}/record/progress/increment`` progress mutate
- ``POST /tasks/{task_id}/record/event/append``       event 子表 INSERT
- ``POST /tasks/{task_id}/record/session/start``      duration session 起始
- ``POST /tasks/{task_id}/record/session/end``        duration session 结束

router prefix 在 main.py 加 ``/api``，实际路径为 ``/api/tasks/...``。
"""

import logging

from fastapi import APIRouter, Depends, Query

from miloco.database.task_repo import TaskLinkConflict, TaskRepo
from miloco.middleware import verify_token
from miloco.middleware.exceptions import (
    ConflictException,
    ResourceNotFoundException,
    ValidationException,
)
from miloco.schema.common_schema import NormalResponse
from miloco.task_record.schema import (
    EventAppendRequest,
    ProgressIncrementRequest,
    RecordInitRequest,
    RecordPatchRequest,
    SessionAtRequest,
    TaskLinkRequest,
)
from miloco.task_record.service import (
    RecordAlreadyExistsError,
    RecordNotFoundError,
    RecordSchemaError,
    RecordWrongKindError,
    TaskNotFoundError,
    TaskRecordService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["TaskRecord"])


def _service() -> TaskRecordService:
    return TaskRecordService()


# ── link ─────────────────────────────────────────────────────────────────────


@router.post("/{task_id}/link", summary="Attach cron link", response_model=NormalResponse)
async def attach_link(
    task_id: str,
    req: TaskLinkRequest,
    current_user: str = Depends(verify_token),
):
    """方案 P 阶段 B：agent 拿到 cron jobId 后显式挂 task_link。

    ``rule`` kind 不允许走此 endpoint（rule create endpoint 自动写 task_link，
    P4 改造）；P2-P4 之间若 caller 传 ``rule`` 走此 endpoint，统一返
    ``wrong_kind``——避免双写孤儿。
    """
    logger.info(
        "Attach link - User: %s, task_id: %s, kind: %s",
        current_user,
        task_id,
        req.kind,
    )
    if req.kind != "cron":
        raise ValidationException(
            f"wrong_kind: /link 当前仅接受 cron，收到 {req.kind!r}"
        )
    try:
        TaskRepo().add_link(task_id, req.kind, req.ref)
    except TaskLinkConflict as e:
        msg = str(e)
        if "不存在" in msg or "FOREIGN KEY" in msg:
            raise ResourceNotFoundException(
                f"task_not_found: {task_id}"
            ) from e
        raise ConflictException(f"link_already_exists: {msg}") from e
    return NormalResponse(
        code=0, message="Link attached", data={"task_id": task_id, "kind": req.kind}
    )


# ── record CRUD ──────────────────────────────────────────────────────────────


@router.post(
    "/{task_id}/record", summary="Init Record", response_model=NormalResponse
)
async def init_record(
    task_id: str,
    req: RecordInitRequest,
    current_user: str = Depends(verify_token),
):
    """方案 P 阶段 A'：插主表活跃行。前提 task 已存在。"""
    logger.info(
        "Init record - User: %s, task_id: %s, kind: %s",
        current_user,
        task_id,
        req.kind.value,
    )
    try:
        view = _service().init_record(task_id, req.kind, req.content)
    except TaskNotFoundError as e:
        raise ResourceNotFoundException(f"task_not_found: {e}") from e
    except RecordAlreadyExistsError as e:
        raise ConflictException(f"record_already_exists: {e}") from e
    except RecordSchemaError as e:
        raise ValidationException(f"schema_invalid: {e}") from e
    return NormalResponse(code=0, message="Record initialized", data=view)


@router.get(
    "/{task_id}/record", summary="Get Active Record", response_model=NormalResponse
)
async def get_record(task_id: str, current_user: str = Depends(verify_token)):
    try:
        view = _service().get_active_record(task_id)
    except RecordNotFoundError as e:
        raise ResourceNotFoundException(f"no_active_record: {e}") from e
    return NormalResponse(code=0, message="Record retrieved", data=view)


@router.patch(
    "/{task_id}/record", summary="Patch Active Record", response_model=NormalResponse
)
async def patch_record(
    task_id: str,
    req: RecordPatchRequest,
    current_user: str = Depends(verify_token),
):
    patch = req.model_dump()
    try:
        view = _service().patch_active_record(task_id, patch)
    except RecordNotFoundError as e:
        raise ResourceNotFoundException(f"no_active_record: {e}") from e
    except RecordSchemaError as e:
        raise ValidationException(f"schema_invalid: {e}") from e
    return NormalResponse(code=0, message="Record patched", data=view)


# ── compute ──────────────────────────────────────────────────────────────────


@router.post(
    "/{task_id}/record/compute",
    summary="Compute Derived",
    response_model=NormalResponse,
)
async def compute_record(
    task_id: str,
    window: str = Query("all"),
    date: str | None = Query(None),
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None),
    current_user: str = Depends(verify_token),
):
    """派生量计算。三套互斥用法：

    - 默认（无 query）：当前活跃行 derived
    - ``?window=day|week|month``：按当前 period 聚合（按 kind 限制，见 §10.8）
    - ``?date=YYYY-MM-DD``：单日历史归档行 derived
    - ``?from=YYYY-MM-DD&to=YYYY-MM-DD``：区间聚合 derived（G1）

    互斥：``window != 'all'`` 不能配 ``date``；``from/to`` 不能配 ``window``/``date``。
    """
    if (from_ is not None) ^ (to is not None):
        raise ValidationException(
            "schema_invalid: from 和 to 必须成对提供"
        )
    if from_ is not None and (window != "all" or date is not None):
        raise ValidationException(
            "schema_invalid: from/to 与 window/date 互斥"
        )
    try:
        if from_ is not None:
            result = _service().compute_range(
                task_id, from_date=from_, to_date=to
            )
        else:
            result = _service().compute_derived(
                task_id, window=window, date=date
            )
    except RecordNotFoundError as e:
        raise ResourceNotFoundException(f"no_active_record: {e}") from e
    except RecordSchemaError as e:
        raise ValidationException(f"schema_invalid: {e}") from e
    return NormalResponse(code=0, message="Derived computed", data=result)


@router.get(
    "/{task_id}/record/archives",
    summary="List Archives",
    response_model=NormalResponse,
)
async def list_archives(
    task_id: str,
    current_user: str = Depends(verify_token),
):
    """列出该 task 全部 archive 行 + 每日 derived 快照（G2）。"""
    try:
        result = _service().list_archives(task_id)
    except RecordNotFoundError as e:
        raise ResourceNotFoundException(f"no_active_record: {e}") from e
    return NormalResponse(code=0, message="Archives listed", data=result)


# ── progress mutate ──────────────────────────────────────────────────────────


@router.post(
    "/{task_id}/record/progress/increment",
    summary="Progress Increment",
    response_model=NormalResponse,
)
async def progress_increment(
    task_id: str,
    req: ProgressIncrementRequest,
    current_user: str = Depends(verify_token),
):
    try:
        result = _service().progress_increment(task_id, delta=req.delta)
    except RecordNotFoundError as e:
        raise ResourceNotFoundException(f"no_active_record: {e}") from e
    except RecordWrongKindError as e:
        raise ValidationException(f"wrong_kind: {e}") from e
    return NormalResponse(code=0, message="Progress incremented", data=result)


# ── event mutate ─────────────────────────────────────────────────────────────


@router.post(
    "/{task_id}/record/event/append",
    summary="Event Append",
    response_model=NormalResponse,
)
async def event_append(
    task_id: str,
    req: EventAppendRequest,
    current_user: str = Depends(verify_token),
):
    try:
        result = _service().event_append(
            task_id, description=req.description, at=req.at
        )
    except RecordNotFoundError as e:
        raise ResourceNotFoundException(f"no_active_record: {e}") from e
    except RecordSchemaError as e:
        raise ValidationException(f"schema_invalid: {e}") from e
    except RecordWrongKindError as e:
        raise ValidationException(f"wrong_kind: {e}") from e
    return NormalResponse(code=0, message="Event appended", data=result)


# ── duration mutate ──────────────────────────────────────────────────────────


@router.post(
    "/{task_id}/record/session/start",
    summary="Session Start",
    response_model=NormalResponse,
)
async def session_start(
    task_id: str,
    req: SessionAtRequest,
    current_user: str = Depends(verify_token),
):
    try:
        result = _service().session_start(task_id, at=req.at)
    except RecordNotFoundError as e:
        raise ResourceNotFoundException(f"no_active_record: {e}") from e
    except RecordSchemaError as e:
        raise ValidationException(f"schema_invalid: {e}") from e
    except RecordWrongKindError as e:
        raise ValidationException(f"wrong_kind: {e}") from e
    return NormalResponse(code=0, message="Session started", data=result)


@router.post(
    "/{task_id}/record/session/end",
    summary="Session End",
    response_model=NormalResponse,
)
async def session_end(
    task_id: str,
    req: SessionAtRequest,
    current_user: str = Depends(verify_token),
):
    try:
        result = _service().session_end(task_id, at=req.at)
    except RecordNotFoundError as e:
        raise ResourceNotFoundException(f"no_active_record: {e}") from e
    except RecordSchemaError as e:
        raise ValidationException(f"schema_invalid: {e}") from e
    except RecordWrongKindError as e:
        raise ValidationException(f"wrong_kind: {e}") from e
    return NormalResponse(code=0, message="Session ended", data=result)
