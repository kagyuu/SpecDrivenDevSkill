"""会議室Service層。docs/P003-backend-spec.md §5.4, §5.5。"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from app.api.errors import ApiError
from app.repositories.rooms import (
    Room,
    create_room,
    deactivate_room,
    get_room_by_id,
    list_active_rooms,
    list_rooms,
    update_room,
)
from app.repositories.users import User
from app.schemas.room import RoomCreateRequest, RoomUpdateRequest


def list_rooms_flow(conn: sqlite3.Connection, current_user: User, include_inactive: bool) -> list[Room]:
    # 一般ユーザーが include_inactive=true を付けても無視する(docs/P003-backend-spec.md §5.4)。
    if include_inactive and current_user.is_admin:
        return list_rooms(conn, include_inactive=True)
    return list_active_rooms(conn)


def create_room_flow(conn: sqlite3.Connection, payload: RoomCreateRequest, now: datetime) -> Room:
    room_id = create_room(
        conn,
        name=payload.name,
        capacity=payload.capacity,
        equipment=payload.equipment,
        description=payload.description,
        is_active=payload.is_active,
        created_at=now.isoformat(),
    )
    return get_room_by_id(conn, room_id)


def update_room_flow(
    conn: sqlite3.Connection,
    room_id: int,
    payload: RoomUpdateRequest,
    now: datetime,
) -> Room:
    existing = get_room_by_id(conn, room_id)
    if existing is None:
        raise ApiError(404, "NOT_FOUND", "指定した会議室が見つかりません")

    update_room(
        conn,
        room_id,
        name=payload.name,
        capacity=payload.capacity,
        equipment=payload.equipment,
        description=payload.description,
        is_active=payload.is_active,
        updated_at=now.isoformat(),
    )
    return get_room_by_id(conn, room_id)


def deactivate_room_flow(conn: sqlite3.Connection, room_id: int, now: datetime) -> None:
    existing = get_room_by_id(conn, room_id)
    if existing is None:
        raise ApiError(404, "NOT_FOUND", "指定した会議室が見つかりません")
    deactivate_room(conn, room_id, updated_at=now.isoformat())
