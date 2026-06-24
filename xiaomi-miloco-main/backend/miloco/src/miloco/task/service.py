# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""TaskService — task SSOT 业务编排层。

职责:
- 调 TaskRepo 做 task 表 CRUD
- 联动 RuleRepo:disable/enable 改 rule.enabled;delete 删 rule 行
- list / get 时实时回查 rule 表生成 rule_briefs(task 量级 < 100,N+1 接受)
- 把 cron / memory 操作汇总为 agent_pending 返回,让 agent 落地
"""

import logging

from miloco.database.rule_repo import RuleRepo
from miloco.database.task_repo import TaskLinkConflict, TaskRepo
from miloco.task.schema import (
    BackendSyncResult,
    BackendSyncRuleResult,
    PendingOp,
    RuleBrief,
    TaskCreateRequest,
    TaskDeleteBackendSynced,
    TaskDeleteResult,
    TaskDisableResult,
    TaskFullView,
    TaskLinkAddRequest,
    TaskLinkEntry,
    TaskSummaryView,
    TaskUpdateRequest,
)

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, rule_repo: RuleRepo | None = None):
        self.repo = TaskRepo()
        self.rule_repo = rule_repo or RuleRepo()

    def create_task(self, req: TaskCreateRequest) -> None:
        """方案 P 阶段 D'：仅插 task 占位行；refs 已从 body 移除。"""
        self.repo.create_task(task_id=req.task_id, description=req.description)

    def add_link(self, task_id: str, req: TaskLinkAddRequest) -> None:
        self.repo.add_link(task_id, req.kind, req.ref)

    def update_description(self, task_id: str, req: TaskUpdateRequest) -> bool:
        return self.repo.update_description(task_id, req.description)

    def get_full_view(self, task_id: str) -> TaskFullView | None:
        raw = self.repo.get_full_view(task_id)
        if raw is None:
            return None
        return self._to_full_view(raw)

    def list_for_dedupe(self) -> list[TaskFullView]:
        return [self._to_full_view(raw) for raw in self.repo.list_all()]

    def list_summary(self, window: str) -> list[TaskSummaryView]:
        """一次性出所有 task 的完整状态(基础 + rule_briefs + links + record 摘要)。

        左连接语义:以 task 为主表,没绑 record 的 task 也返(record=None),不丢行。
        TaskRecordService 是无状态轻服务,内部实例化即可,不进 Manager 单例。
        """
        from miloco.task_record.service import TaskRecordService

        task_views = self.list_for_dedupe()
        record_map = TaskRecordService().list_active_summaries(window)
        return [
            TaskSummaryView(
                **view.model_dump(),
                record=record_map.get(view.task_id),
            )
            for view in task_views
        ]

    def _to_full_view(self, raw: dict) -> TaskFullView:
        rule_briefs: list[RuleBrief] = []
        for link in raw["links"]:
            if link["kind"] != "rule":
                continue
            rule = self.rule_repo.get_by_id(link["ref"])
            if rule is None:
                logger.warning(
                    "task_link 引用了不存在的 rule %s (task=%s)",
                    link["ref"],
                    raw["task_id"],
                )
                continue
            rule_briefs.append(
                RuleBrief(
                    rule_id=rule.id,
                    query=rule.condition.query,
                    actions_desc=self._rule_actions_desc(rule),
                )
            )
        return TaskFullView(
            task_id=raw["task_id"],
            description=raw["description"],
            status=raw["status"],
            paused_at=raw["paused_at"],
            created_at=raw["created_at"],
            rule_briefs=rule_briefs,
            links=[TaskLinkEntry(**link) for link in raw["links"]],
        )

    @staticmethod
    def _rule_actions_desc(rule) -> list[str]:
        """rule 动作摘要——event/state 模式下各按"动作 / 描述"路径各取一份。"""
        if rule.mode.value == "event":
            if rule.actions:
                return [
                    f"{a.iid}={a.value if a.value is not None else a.params}"
                    for a in rule.actions
                ]
            return list(rule.action_descriptions)
        out: list[str] = []
        if rule.on_enter_actions:
            out.extend(f"on_enter:{a.iid}" for a in rule.on_enter_actions)
        if rule.on_enter_desc:
            out.append(f"on_enter:{rule.on_enter_desc}")
        if rule.on_exit_actions:
            out.extend(f"on_exit:{a.iid}" for a in rule.on_exit_actions)
        if rule.on_exit_desc:
            out.append(f"on_exit:{rule.on_exit_desc}")
        return out

    def disable_task(self, task_id: str) -> TaskDisableResult:
        return self._toggle_task(task_id, target_status="paused")

    def enable_task(self, task_id: str) -> TaskDisableResult:
        return self._toggle_task(task_id, target_status="active")

    def _toggle_task(self, task_id: str, target_status: str) -> TaskDisableResult:
        meta_result = self.repo.set_status(task_id, target_status)
        if meta_result == "not_found":
            raise TaskLinkConflict(f"task {task_id!r} not found")

        rule_results: list[BackendSyncRuleResult] = []
        for rule_id in self.repo.get_rule_refs(task_id):
            rule = self.rule_repo.get_by_id(rule_id)
            if rule is None:
                rule_results.append(
                    BackendSyncRuleResult(rule_id=rule_id, result="not_found")
                )
                continue
            rule.enabled = target_status == "active"
            ok = self.rule_repo.update(rule)
            rule_results.append(
                BackendSyncRuleResult(
                    rule_id=rule_id, result="ok" if ok else "fail"
                )
            )

        cron_action = "disable" if target_status == "paused" else "enable"
        full = self.repo.get_full_view(task_id)
        agent_pending: list[PendingOp] = []
        for link in full["links"]:
            if link["kind"] == "cron":
                agent_pending.append(
                    PendingOp(kind="cron", ref=link["ref"], action=cron_action)
                )
            # 方案 P：memory 类 link 已废除，不再产生 pending op

        return TaskDisableResult(
            task_id=task_id,
            status=target_status,
            backend_synced=BackendSyncResult(
                meta_status=meta_result, rules=rule_results
            ),
            agent_pending=agent_pending,
        )

    def delete_task(
        self, task_id: str, reason: str = "completed"
    ) -> TaskDeleteResult | None:
        """删 task —— **单事务**（spec §6.4.1）：

        ``BEGIN → INSERT task_terminate_log → DELETE 过期 log → DELETE rule
        × N → DELETE task → COMMIT``。任一步抛异常整笔 ROLLBACK，杜绝
        "log 写了但 task 没删"或"rule 删了但 task 还在"的不一致中间态。

        ``reason`` 来自 ``DELETE /tasks/{id}?reason=`` query 参数，透传到
        ``task_terminate_log.reason``。
        """
        from miloco.database.connector import get_db_connector
        from miloco.database.rule_repo import RuleRepo
        from miloco.database.task_repo import TaskRepo
        from miloco.task_record.schema import TerminateReason
        from miloco.task_record.service import (
            TaskNotFoundError,
            TaskRecordService,
        )

        full = self.repo.get_full_view(task_id)
        if full is None:
            return None

        task_link_count = len(full["links"])
        rule_ids = [link["ref"] for link in full["links"] if link["kind"] == "rule"]

        try:
            reason_enum = TerminateReason(reason)
        except ValueError:
            reason_enum = TerminateReason.COMPLETED

        record_service = TaskRecordService()
        deleted_rules: list[str] = []

        with get_db_connector().get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN")
            try:
                # 1. 审计快照 + 30 天滚动清
                try:
                    record_service.write_terminate_log_in_tx(
                        cursor, task_id, reason_enum
                    )
                except TaskNotFoundError:
                    pass  # task 不存在已被外层 get_full_view 排除，但保留兜底
                record_service.prune_terminate_log_in_tx(cursor)

                # 2. 删 rule（按 task_link 反查的 rule_ids）
                for rid in rule_ids:
                    if RuleRepo.delete_in_tx(cursor, rid):
                        deleted_rules.append(rid)

                # 3. 删 task（FK CASCADE 同步清 task_link / task_record_* 主表 + 子表）
                TaskRepo.delete_task_in_tx(cursor, task_id)

                conn.commit()
            except Exception:
                conn.rollback()
                raise

        agent_pending: list[PendingOp] = [
            PendingOp(kind="cron", ref=link["ref"], action="remove")
            for link in full["links"]
            if link["kind"] == "cron"
        ]

        return TaskDeleteResult(
            task_id=task_id,
            backend_synced=TaskDeleteBackendSynced(
                rules_deleted=deleted_rules,
                task_link_rows_deleted=task_link_count,
            ),
            agent_pending=agent_pending,
        )
