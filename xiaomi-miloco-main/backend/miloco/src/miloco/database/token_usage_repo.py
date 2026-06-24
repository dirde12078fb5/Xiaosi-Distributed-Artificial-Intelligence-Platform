"""Token usage event log repo — SQLite storage with daily rollup retention.

Schema:
  - token_usage         : live event rows (last 3 days), one row per API call
  - token_usage_daily   : per-day rollup keyed by (date, model, type), preserved
                          across retention window so historical trend / model /
                          type breakdown stay queryable

Field semantics:
  - input_tokens   = prompt_tokens (total input, all modalities)
  - cache_tokens   = prompt_tokens_details.cached_tokens   (⊆ input_tokens)
  - video_tokens   = prompt_tokens_details.video_tokens    (⊆ input_tokens)
  - audio_tokens   = prompt_tokens_details.audio_tokens    (⊆ input_tokens)
  - output_tokens  = completion_tokens
Derivations (no need to store):
  - text_tokens     = input - video - audio
  - billable_tokens = input - cache

Retention: on first insert of each day, events older than 3 days are aggregated
by (date, model, type) into the daily table via INSERT...SELECT...GROUP BY +
ON CONFLICT UPSERT, then deleted from the live table. The whole operation runs
in a single explicit transaction (BEGIN/COMMIT) — the connector is in autocommit
mode, so we must start a transaction explicitly for atomicity.
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta

from miloco.database.connector import get_db_connector

logger = logging.getLogger(__name__)

_RETENTION_DAYS = 3
_DEFAULT_EVENT_LIMIT = 100000  # ample headroom for the 3-day retention window


class TokenUsageRepo:
    """Data access object for token_usage + token_usage_daily."""

    def __init__(self) -> None:
        self.db = get_db_connector()
        self._last_archive_check: date | None = None

    def insert(self, model: str, usage: dict, type: str) -> None:
        """Insert one event. Triggers rollup on first call of each new day.

        `type` is either ``"realtime"`` (perception-loop driven) or
        ``"on_demand"`` (user-initiated query).
        """
        ts_ms = int(time.time() * 1000)
        today = datetime.fromtimestamp(ts_ms / 1000).date()
        if self._last_archive_check != today:
            # Only mark "done for today" after rollup succeeds. Otherwise a
            # persistent failure (disk full, lock contention) would be masked:
            # the flag would skip retries all day while the live table grows.
            self._maybe_rollup(ts_ms)
            self._last_archive_check = today

        details = usage.get("prompt_tokens_details") or {}
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cache_tokens = details.get("cached_tokens") or 0
        video_tokens = details.get("video_tokens") or 0
        audio_tokens = details.get("audio_tokens") or 0

        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO token_usage "
                "(timestamp, model, type, input_tokens, output_tokens, "
                " cache_tokens, video_tokens, audio_tokens, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ts_ms, model, type,
                    input_tokens, output_tokens,
                    cache_tokens, video_tokens, audio_tokens,
                    ts_ms,
                ),
            )
            conn.commit()

    def clear_all(self) -> dict[str, int]:
        """删除全部 token 用量(实时表 + 日 rollup),返回各表删除行数。

        供 admin 重置统计用(不可恢复)。两表在同一事务内一并清空。
        """
        with self.db.get_connection() as conn:
            n_live = conn.execute("SELECT COUNT(*) FROM token_usage").fetchone()[0]
            n_daily = conn.execute(
                "SELECT COUNT(*) FROM token_usage_daily"
            ).fetchone()[0]
            conn.execute("DELETE FROM token_usage")
            conn.execute("DELETE FROM token_usage_daily")
            conn.commit()
        return {"token_usage": int(n_live), "token_usage_daily": int(n_daily)}

    def list_events(
        self,
        since_ms: int | None = None,
        until_ms: int | None = None,
        limit: int = _DEFAULT_EVENT_LIMIT,
    ) -> tuple[list[dict], bool]:
        """Return raw events in [since_ms, until_ms]. Returns (rows, truncated).

        Defaults: since=today 00:00 local, until=now. ``limit`` caps the result
        so callers can't accidentally pull tens of MB; ``truncated=True`` signals
        that more rows exist beyond the cap (caller should narrow the window).
        """
        if since_ms is None:
            since_ms = int(
                datetime.combine(date.today(), datetime.min.time()).timestamp() * 1000
            )
        if until_ms is None:
            until_ms = int(time.time() * 1000)
        # Fetch limit+1 so we can detect overflow without an extra COUNT.
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT timestamp, model, type, input_tokens, output_tokens, "
                "       cache_tokens, video_tokens, audio_tokens "
                "FROM token_usage WHERE timestamp BETWEEN ? AND ? "
                "ORDER BY timestamp ASC LIMIT ?",
                (since_ms, until_ms, limit + 1),
            ).fetchall()
        truncated = len(rows) > limit
        if truncated:
            rows = rows[:limit]
        return [dict(r) for r in rows], truncated

    def aggregate_buckets(
        self,
        since_ms: int | None = None,
        until_ms: int | None = None,
        bin_minutes: int = 60,
    ) -> list[dict]:
        """Bucketed aggregation of raw events in [since_ms, until_ms], grouped by
        (time bucket, model, type). ``bin_minutes`` is the bucket width.

        Used by the "today" view: the response size is bounded by bucket count
        (≈ day / bin × models × types), not by event count, so it never hits the
        raw-event cap regardless of activity. Returns rows with ``bucket_ms``
        (bucket start, ms epoch) plus per-bucket sums.
        """
        if since_ms is None:
            since_ms = int(
                datetime.combine(date.today(), datetime.min.time()).timestamp() * 1000
            )
        if until_ms is None:
            until_ms = int(time.time() * 1000)
        bin_ms = max(1, bin_minutes) * 60_000
        with self.db.get_connection() as conn:
            # CAST(... AS INTEGER) 截断为整数桶下标；timestamp ≥ since 保证非负 = floor。
            rows = conn.execute(
                "SELECT CAST((timestamp - ?) / ? AS INTEGER) AS bkt, model, type, "
                "       COUNT(*) AS calls, "
                "       SUM(input_tokens) AS input_tokens, "
                "       SUM(output_tokens) AS output_tokens, "
                "       SUM(cache_tokens) AS cache_tokens, "
                "       SUM(video_tokens) AS video_tokens, "
                "       SUM(audio_tokens) AS audio_tokens "
                "FROM token_usage WHERE timestamp BETWEEN ? AND ? "
                "GROUP BY bkt, model, type ORDER BY bkt, model, type",
                (since_ms, bin_ms, since_ms, until_ms),
            ).fetchall()
        out: list[dict] = []
        for r in rows:
            d = dict(r)
            bkt = d.pop("bkt")
            d["bucket_ms"] = since_ms + bkt * bin_ms
            out.append(d)
        return out

    def aggregate_daily(
        self, since: str | None = None, until: str | None = None
    ) -> list[dict]:
        """Return per-day rollup rows. `since` / `until` are inclusive YYYY-MM-DD.

        Combines `token_usage_daily` (historical) with on-the-fly aggregation of
        `token_usage` (live, last 3 days) so the caller sees a uniform daily view.
        """
        conditions: list[str] = []
        params: list = []
        if since:
            conditions.append("date >= ?")
            params.append(since)
        if until:
            conditions.append("date <= ?")
            params.append(until)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with self.db.get_connection() as conn:
            historical = conn.execute(
                f"SELECT date, model, type, calls, input_tokens, output_tokens, "
                f"       cache_tokens, video_tokens, audio_tokens "
                f"FROM token_usage_daily {where} ORDER BY date ASC, model, type",
                params,
            ).fetchall()

            live = conn.execute(
                f"SELECT date(timestamp / 1000, 'unixepoch', 'localtime') AS date, "
                f"  model, type, "
                f"  COUNT(*) AS calls, "
                f"  SUM(input_tokens) AS input_tokens, "
                f"  SUM(output_tokens) AS output_tokens, "
                f"  SUM(cache_tokens) AS cache_tokens, "
                f"  SUM(video_tokens) AS video_tokens, "
                f"  SUM(audio_tokens) AS audio_tokens "
                f"FROM token_usage "
                f"GROUP BY date, model, type "
                f"{('HAVING ' + ' AND '.join(conditions)) if conditions else ''} "
                f"ORDER BY date ASC, model, type",
                params,
            ).fetchall()

        return [dict(r) for r in historical] + [dict(r) for r in live]

    def _maybe_rollup(self, now_ms: int) -> None:
        """Roll up events older than _RETENTION_DAYS into token_usage_daily.

        SQL does the GROUP BY internally via INSERT...SELECT...ON CONFLICT,
        then a DELETE prunes the live table. Both wrapped in one transaction.
        """
        # Day-aligned cutoff: a day is either fully rolled up or fully raw,
        # never split. Otherwise aggregate_daily() would return two rows for
        # the boundary day (one from each table) sharing the same key.
        today = datetime.fromtimestamp(now_ms / 1000).date()
        cutoff_date = today - timedelta(days=_RETENTION_DAYS)
        cutoff_ms = int(
            datetime.combine(cutoff_date, datetime.min.time()).timestamp() * 1000
        )
        with self.db.get_connection() as conn:
            exists = conn.execute(
                "SELECT 1 FROM token_usage WHERE timestamp < ? LIMIT 1",
                (cutoff_ms,),
            ).fetchone()
            if not exists:
                return

            conn.execute("BEGIN")
            try:
                conn.execute(
                    """
                    INSERT INTO token_usage_daily
                        (date, model, type, calls,
                         input_tokens, output_tokens,
                         cache_tokens, video_tokens, audio_tokens)
                    SELECT
                        date(timestamp / 1000, 'unixepoch', 'localtime') AS d,
                        model, type,
                        COUNT(*),
                        SUM(input_tokens), SUM(output_tokens),
                        SUM(cache_tokens), SUM(video_tokens), SUM(audio_tokens)
                    FROM token_usage
                    WHERE timestamp < ?
                    GROUP BY d, model, type
                    ON CONFLICT(date, model, type) DO UPDATE SET
                        calls = calls + excluded.calls,
                        input_tokens = input_tokens + excluded.input_tokens,
                        output_tokens = output_tokens + excluded.output_tokens,
                        cache_tokens = cache_tokens + excluded.cache_tokens,
                        video_tokens = video_tokens + excluded.video_tokens,
                        audio_tokens = audio_tokens + excluded.audio_tokens
                    """,
                    (cutoff_ms,),
                )
                deleted = conn.execute(
                    "DELETE FROM token_usage WHERE timestamp < ?", (cutoff_ms,)
                ).rowcount
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            logger.info(
                "rolled up %d events older than %d ms into token_usage_daily",
                deleted,
                cutoff_ms,
            )


_repo: TokenUsageRepo | None = None


def get_token_usage_repo() -> TokenUsageRepo:
    """Singleton accessor."""
    global _repo
    if _repo is None:
        _repo = TokenUsageRepo()
    return _repo


def fire_record(model: str, usage: dict, type: str) -> None:
    """Record one omni usage event (synchronous direct insert).

    历史教训:曾用 ``asyncio.create_task`` 排到当前 loop 异步写,但感知主路径每窗
    跑在 inference 线程的临时 loop(``asyncio.run`` 起的)上,窗末 ``asyncio.run``
    退出会把该 task ``cancel``;``CancelledError`` 是 ``BaseException`` 又躲过了
    ``except Exception`` → realtime 用量在 Linux(fsync 真落盘、insert 慢)上几乎必丢、
    macOS(fsync 近 no-op)上几乎必中,开发自测全绿、生产静默丢数据。

    现在直接同步 insert:omni 调用本身 8-12s,一次 sqlite insert(~数十 ms)完全无感,
    且 loop 归属无关、Mac/Linux 行为一致、不会被 cancel。同步路径里不再有 await 点,
    不可能产生 ``CancelledError``,故只兜 ``Exception``(含 sqlite lock / disk full 的
    ``sqlite3.OperationalError``)——用量记录永不把异常抛进 omni 请求路径;
    ``KeyboardInterrupt`` / ``SystemExit`` 仍照常向上传播,不被静默吞掉。
    """
    try:
        get_token_usage_repo().insert(model, usage, type)
    except Exception as e:  # noqa: BLE001
        logger.warning("usage log failed: %s", e)
