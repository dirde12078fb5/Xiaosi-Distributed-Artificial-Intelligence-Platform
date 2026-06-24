# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Independent evaluator for ``lifecycle=temporary`` rules.

V3 §5.5 Step 4d (latest v3-system-overview.md spec) decouples temporary
self-deletion from the action kind::

    terminate_when 由 Miloco 后台独立评估通路检测，跟 Rule 自身的动作类型
    无关 —— 一条 state 模式 + 设备直控 + temporary 的 rule 设计上完全合法
    （动作直调设备，背后 terminate_when 时机一到 rule 自动消失）。

This module provides the scaffolding: a periodic task that scans all
``lifecycle=temporary`` rules, runs them through ``_evaluate``, and deletes
the rule when evaluation says the condition is met.

⚠️ **当前实现现状**：``_evaluate`` 是 stub 永远返 ``False`` —— 任何
``lifecycle=temporary`` 的规则（不论 event / state、不论走设备直控还是 Agent
回调）目前都**不会被自动清理**，只能依赖：
  1. ``miloco-terminate-task`` skill 显式删除（用户取消 / 到期 cron 触发）；或
  2. ``miloco-cli rule delete <id>`` 手动兜底。

依赖"自动消失"语义的链路必须建立显式删除兜底（见
plugins/skills/miloco-create-task/SKILL.md §4d 关于 temporary 的注解）。完成
``_evaluate`` 实装前请勿假设 temporary 等价于 self-cleaning。

The real implementation is intentionally deferred -- it likely needs one or
more of:

- Time-phrase parsing for absolute deadlines (e.g. "今天 23:59 后失效"
  → ISO timestamp + ``datetime.now()`` comparison)
- LLM-based evaluation for vague conditions (e.g. "本次客人离开")
- Subscription to OpenClaw skill-emitted terminate signals

When that lands, replace the body of ``_evaluate`` only; the surrounding
loop / scheduling stays the same.
"""

from __future__ import annotations

import asyncio
import logging

from miloco.rule.schema import Rule, RuleLifecycle
from miloco.rule.service import RuleService

logger = logging.getLogger(__name__)


class TerminateEvaluator:
    """Periodic background task that auto-deletes temporary rules whose
    ``terminate_when`` condition has been met.

    Lifecycle is owned by ``Manager``: ``start()`` is called after
    ``init_rule_service`` succeeds; ``stop()`` is best-effort -- the
    interpreter shutdown will cancel the task either way.

    Attributes:
        interval_seconds: how often the scan runs. Defaults to 5 min, which
            matches the typical granularity of natural-language temporary
            conditions ("今天过完", "本次客人离开"). Lower values cost more
            (each tick may end up calling an LLM), higher values delay
            cleanup. Tunable via the constructor.
    """

    def __init__(
        self,
        rule_service: RuleService,
        *,
        interval_seconds: int = 300,
    ) -> None:
        self._rule_service = rule_service
        self._interval = max(int(interval_seconds), 1)
        self._task: asyncio.Task | None = None

    # ---- lifecycle ----

    def start(self) -> None:
        """Spawn the periodic scan task. Idempotent."""
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(
            self._run(), name="rule_terminate_evaluator"
        )
        logger.info(
            "TerminateEvaluator started (interval=%ds)", self._interval
        )

    async def stop(self) -> None:
        """Cancel the periodic task. Idempotent."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
            logger.info("TerminateEvaluator stopped")

    # ---- main loop ----

    async def _run(self) -> None:
        # First scan immediately so newly-created temporary rules don't have
        # to wait one full interval before becoming eligible.
        while True:
            try:
                await self._tick()
            except Exception as e:  # noqa: BLE001
                logger.exception("TerminateEvaluator tick failed: %s", e)
            try:
                await asyncio.sleep(self._interval)
            except asyncio.CancelledError:
                return

    async def _tick(self) -> None:
        rules = await self._rule_service.get_all_rules(enabled_only=False)
        for rule in rules:
            if rule.lifecycle != RuleLifecycle.TEMPORARY:
                continue
            if not rule.terminate_when:
                continue
            try:
                should_terminate = await self._evaluate(rule)
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "TerminateEvaluator: evaluate failed for rule %s: %s",
                    rule.id,
                    e,
                )
                continue
            if should_terminate:
                logger.info(
                    "TerminateEvaluator: terminating rule %s "
                    "(terminate_when=%r)",
                    rule.id,
                    rule.terminate_when,
                )
                try:
                    await self._rule_service.delete_rule(rule.id)
                except Exception as e:  # noqa: BLE001
                    logger.error(
                        "TerminateEvaluator: delete_rule failed for %s: %s",
                        rule.id,
                        e,
                    )

    # ---- evaluation hook ----

    async def _evaluate(self, rule: Rule) -> bool:
        """Return True when ``rule.terminate_when`` is judged satisfied.

        STUB. Always returns False today; real evaluation is left to a
        follow-up. See the module docstring for candidate strategies.
        """
        logger.debug(
            "TerminateEvaluator stub: rule=%s terminate_when=%r -> False",
            rule.id,
            rule.terminate_when,
        )
        return False
