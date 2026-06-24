# Copyright (C) 2025 Xiaomi Corporation
# This software may be used and distributed according to the terms of the Xiaomi Miloco License Agreement.

"""Person service."""

import logging

from miloco.database.person_repo import UNSET, PersonRepo
from miloco.middleware.exceptions import (
    BadRequestException,
    ConflictException,
    ResourceNotFoundException,
)
from miloco.person.schema import Person

logger = logging.getLogger(__name__)


class PersonService:
    def __init__(self, person_repo: PersonRepo):
        self._person_repo = person_repo

    def list_persons(self) -> list[Person]:
        return self._person_repo.get_all()

    def get_person(self, person_id: str) -> Person | None:
        return self._person_repo.get_by_id(person_id)

    def exists(self, person_id: str) -> bool:
        return self._person_repo.exists(person_id)

    def create_person(self, name: str, role: str | None) -> str:
        # service 层兜底校验：name 必填非空（schema 层 Field 已挡 REST 入口，这里
        # 守住 split / cli / 内部调用等不走 pydantic 的路径）。
        name = (name or "").strip()
        if not name:
            raise BadRequestException("name 不可为空")
        if self._person_repo.exists_by_name(name):
            raise ConflictException(f"Person name '{name}' already exists")
        return self._person_repo.create(name, role)

    def update_person(
        self, person_id: str, name: str | None = None, role: object = UNSET
    ) -> None:
        if not self._person_repo.exists(person_id):
            raise ResourceNotFoundException(f"Person '{person_id}' not found")
        # name 为 None 表示本次 PATCH 不动 name；显式传了就必须是非空真名，
        # 不能像旧逻辑那样 `if name and` 把空串静默吞掉（会清空 name）。
        if name is not None:
            name = name.strip()
            if not name:
                raise BadRequestException("name 不可为空")
            if self._person_repo.exists_by_name(name, exclude_id=person_id):
                raise ConflictException(f"Person name '{name}' already exists")
        self._person_repo.update(person_id, name, role)

    def delete_person(self, person_id: str) -> None:
        if not self._person_repo.exists(person_id):
            raise ResourceNotFoundException(f"Person '{person_id}' not found")
        self._person_repo.delete(person_id)
        logger.info("Person deleted: id=%s", person_id)
