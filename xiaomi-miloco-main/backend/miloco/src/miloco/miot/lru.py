"""设备 iid LRU 后端存储。

每个 device 保留 capacity 个最近被操作的 iid（``prop.s.p`` / ``action.s.a``），
作为 catalog 注入时挑选 spec 子集的依据。落到 SQLite ``device_lru`` 表
（``(did, key, touched_at)``）—— 用关系表而不是 KV blob，避免每次 touch 都要
read-modify-write 整张 LRU 序列化。

写入路径：``MiotService.control_device`` / ``get_device_status`` 成功后由服务端
直接调 ``LRUStore.touch``。CLI 不再持有 touch 接口；catalog 注入时读 snapshot
拿到 iid，再用本地 home_info 的 ``iid_to_key`` 翻译为 type_name 并入 spec 行。
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

DEFAULT_CAPACITY = 7


def _us_to_iso(ts_us: int | None) -> str | None:
    if ts_us is None:
        return None
    return datetime.fromtimestamp(ts_us / 1_000_000, tz=UTC).isoformat()


class LRUStore:
    def __init__(self, db_connector):
        self._db = db_connector

    def touch(self, did: str, key: str, capacity: int = DEFAULT_CAPACITY) -> None:
        """Bump (did, key) 的 touched_at 到 now，并保持每个 did 至多 capacity 条。

        ``key`` 由调用方保证为 iid 形态（``prop.s.p`` / ``action.s.a``），
        服务端 control / status 路径已经做过 ``_parse_prop_iid`` / ``_parse_action_iid``
        校验，这里不再重复过滤。
        """
        now_us = int(time.time() * 1_000_000)
        # 先写入或刷新 (did, key)
        self._db.execute_update(
            "INSERT OR REPLACE INTO device_lru (did, key, touched_at) VALUES (?, ?, ?)",
            (did, key, now_us),
        )
        # 再裁剪：仅保留该 did 下 touched_at 最大的 capacity 条
        self._db.execute_update(
            """
            DELETE FROM device_lru
             WHERE did = ?
               AND key NOT IN (
                   SELECT key FROM device_lru
                    WHERE did = ?
                    ORDER BY touched_at DESC
                    LIMIT ?
               )
            """,
            (did, did, capacity),
        )

    def clear(self) -> None:
        """Delete all LRU records. Called on account switch."""
        self._db.execute_update("DELETE FROM device_lru")

    def load(self) -> dict:
        """全量 snapshot：``{"version":1, "updated_at":..., "histories":{did:[iid,...]}}``。

        每个设备的 list 按 touched_at 降序（MRU 在前）。
        """
        rows = self._db.execute_query(
            "SELECT did, key, touched_at FROM device_lru "
            "ORDER BY did, touched_at DESC"
        )
        histories: dict[str, list[str]] = {}
        max_ts: int | None = None
        for row in rows:
            histories.setdefault(row["did"], []).append(row["key"])
            ts = row["touched_at"]
            if max_ts is None or ts > max_ts:
                max_ts = ts
        return {
            "version": 1,
            "updated_at": _us_to_iso(max_ts),
            "histories": histories,
        }
