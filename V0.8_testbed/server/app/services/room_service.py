"""Room Service layer (U002-T1, docs/P007-impl-direction/U002-room-management.md).

Validation per docs/P002-frontend-spec.md 3.6節. Authorization (admin-only
for write operations) is the Router layer's job (U002-T2), per this task's
own 実装してはいけないこと.
"""

from __future__ import annotations

import sqlite3

from app.exceptions import NotFoundError, ValidationError
from app.repositories import room_repository
from app.repositories.room_repository import RoomRow

_NAME_MAX_LENGTH = 50
_DESCRIPTION_MAX_LENGTH = 200


def _validate(name: str, capacity: int, description: str | None) -> None:
    fields: dict[str, str] = {}
    if not name or not name.strip():
        fields["name"] = "会議室名を入力してください"
    elif len(name) > _NAME_MAX_LENGTH:
        fields["name"] = "会議室名は50文字以内で入力してください"

    if capacity < 1:
        fields["capacity"] = "収容人数は1以上の整数で入力してください"

    if description is not None and len(description) > _DESCRIPTION_MAX_LENGTH:
        fields["description"] = "説明文は200文字以内で入力してください"

    if fields:
        raise ValidationError(fields=fields)


def list_rooms(conn: sqlite3.Connection, include_inactive: bool = False) -> list[RoomRow]:
    return room_repository.find_all(conn, include_inactive=include_inactive)


def create(
    conn: sqlite3.Connection,
    name: str,
    capacity: int,
    equipment: list[str],
    description: str | None,
) -> RoomRow:
    _validate(name, capacity, description)
    return room_repository.create(conn, name, capacity, equipment, description)


def update(
    conn: sqlite3.Connection,
    room_id: int,
    name: str,
    capacity: int,
    equipment: list[str],
    description: str | None,
    is_active: bool,
) -> RoomRow:
    _validate(name, capacity, description)
    room = room_repository.update(conn, room_id, name, capacity, equipment, description, is_active)
    if room is None:
        raise NotFoundError("会議室が見つかりません")
    return room


def deactivate(conn: sqlite3.Connection, room_id: int) -> RoomRow:
    room = room_repository.deactivate(conn, room_id)
    if room is None:
        raise NotFoundError("会議室が見つかりません")
    return room
