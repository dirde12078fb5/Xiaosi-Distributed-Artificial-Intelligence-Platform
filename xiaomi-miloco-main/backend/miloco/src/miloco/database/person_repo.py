# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Person data access object."""

import logging
import uuid
from typing import Any

from miloco.database.connector import get_db_connector
from miloco.person.schema import Person
from miloco.utils.time_utils import ms_to_iso_local, now_ms

logger = logging.getLogger(__name__)

# sentinel：PATCH 时区分"未传 role(本次不改)"与"显式清空(写 SQL NULL)"。role 可空,需要这第三态。
UNSET: Any = object()


class PersonRepo:
    def __init__(self):
        self.db_connector = get_db_connector()

    # v2 起 person 只读自己,**不再 JOIN biometric**——那张表 v1 用来存
    # face/voice 注册记录,但实际从未被写入,且新流程"是否录了人脸"由文件系统
    # identity_lib/persons/<id>/tier_a/face_* 图像实际样本数表达(走
    # /api/identity/persons/<id>/samples/montage 的 face_count)。

    def _row_to_person(self, row: dict[str, Any]) -> Person:
        return Person(
            id=row["id"],
            name=row["name"],
            role=row.get("role"),
            created_at=ms_to_iso_local(row.get("created_at")),
            updated_at=ms_to_iso_local(row.get("updated_at")),
        )

    def get_all(self) -> list[Person]:
        rows = self.db_connector.execute_query(
            "SELECT * FROM person ORDER BY created_at ASC"
        )
        return [self._row_to_person(r) for r in rows]

    def get_by_id(self, person_id: str) -> Person | None:
        rows = self.db_connector.execute_query(
            "SELECT * FROM person WHERE id = ?", (person_id,)
        )
        return self._row_to_person(rows[0]) if rows else None

    def exists(self, person_id: str) -> bool:
        rows = self.db_connector.execute_query(
            "SELECT id FROM person WHERE id = ?", (person_id,)
        )
        return bool(rows)

    def exists_by_name(self, name: str, exclude_id: str | None = None) -> bool:
        if exclude_id:
            rows = self.db_connector.execute_query(
                "SELECT id FROM person WHERE name = ? AND id != ?", (name, exclude_id)
            )
        else:
            rows = self.db_connector.execute_query(
                "SELECT id FROM person WHERE name = ?", (name,)
            )
        return bool(rows)

    def create(self, name: str, role: str | None) -> str:
        # 最后一道 sanity 闸：name 必填非空（schema + service 已校验，这里防御内部误调）。
        assert name and name.strip(), "person.name 不可为空"
        person_id = str(uuid.uuid4())
        ts = now_ms()
        self.db_connector.execute_update(
            "INSERT INTO person (id, name, role, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (person_id, name, role, ts, ts),
        )
        logger.info("Person created: id=%s name=%s", person_id, name)
        return person_id

    def update(self, person_id: str, name: str | None = None, role: object = UNSET) -> bool:
        fields = []
        params = []
        if name is not None:
            # name 为 None = 本次不改 name；显式传了就必须非空（service 已拦，这里 sanity）。
            assert name.strip(), "person.name 不可为空"
            fields.append("name = ?")
            params.append(name)
        if role is not UNSET:
            # role is UNSET = 本次不改；role is None = 显式清空(写 SQL NULL)；其余 = 设值。
            fields.append("role = ?")
            params.append(role)
        if not fields:
            return False
        fields.append("updated_at = ?")
        params.append(now_ms())
        params.append(person_id)
        affected = self.db_connector.execute_update(
            f"UPDATE person SET {', '.join(fields)} WHERE id = ?",
            tuple(params),
        )
        return affected > 0

    def delete(self, person_id: str) -> bool:
        affected = self.db_connector.execute_update(
            "DELETE FROM person WHERE id = ?", (person_id,)
        )
        return affected > 0
