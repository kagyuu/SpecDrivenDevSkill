"""Room repository (U002-T1, docs/P007-impl-direction/U002-room-management.md).

`equipment` is stored as a JSON string in the DB (docs/P003-backend-spec.md
2.2節) and encoded/decoded to/from `list[str]` here, at the Repository
boundary, so no other layer needs to know the storage representation.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import TypedDict


class RoomRow(TypedDict):
    room_id: int
    name: str
    capacity: int
    equipment: list[str]
    description: str | None
    is_active: int


def _row_to_room(row: sqlite3.Row) -> RoomRow:
    data = dict(row)
    data["equipment"] = json.loads(data["equipment"])
    return data  # type: ignore[return-value]


def find_all(conn: sqlite3.Connection, include_inactive: bool = False) -> list[RoomRow]:
    query = "SELECT room_id, name, capacity, equipment, description, is_active FROM rooms"
    if not include_inactive:
        query += " WHERE is_active = 1"
    query += " ORDER BY room_id"
    rows = conn.execute(query).fetchall()
    return [_row_to_room(row) for row in rows]


def find_by_id(conn: sqlite3.Connection, room_id: int) -> RoomRow | None:
    row = conn.execute(
        "SELECT room_id, name, capacity, equipment, description, is_active "
        "FROM rooms WHERE room_id = ?",
        (room_id,),
    ).fetchone()
    return _row_to_room(row) if row is not None else None


def create(
    conn: sqlite3.Connection,
    name: str,
    capacity: int,
    equipment: list[str],
    description: str | None,
) -> RoomRow:
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        cursor = conn.execute(
            "INSERT INTO rooms (name, capacity, equipment, description, is_active, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
            (name, capacity, json.dumps(equipment), description, now, now),
        )
        room_id = cursor.lastrowid
    room = find_by_id(conn, room_id)
    assert room is not None  # just inserted
    return room


def update(
    conn: sqlite3.Connection,
    room_id: int,
    name: str,
    capacity: int,
    equipment: list[str],
    description: str | None,
    is_active: bool,
) -> RoomRow | None:
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        cursor = conn.execute(
            "UPDATE rooms SET name = ?, capacity = ?, equipment = ?, description = ?, "
            "is_active = ?, updated_at = ? WHERE room_id = ?",
            (name, capacity, json.dumps(equipment), description, int(is_active), now, room_id),
        )
        if cursor.rowcount == 0:
            return None
    return find_by_id(conn, room_id)


def deactivate(conn: sqlite3.Connection, room_id: int) -> RoomRow | None:
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        cursor = conn.execute(
            "UPDATE rooms SET is_active = 0, updated_at = ? WHERE room_id = ?",
            (now, room_id),
        )
        if cursor.rowcount == 0:
            return None
    return find_by_id(conn, room_id)
