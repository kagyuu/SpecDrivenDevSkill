"""rooms テーブルへのデータアクセス(読み取りのみ、書き込みはU003で追加)。

docs/P003-backend-spec.md §5.4, §6。

※ get_room_by_id はU002-T4で追加した。docs/P007-impl-direction/U002-reservation-core.md
U002-T4(予約作成フロー)が、対象会議室の有効性・収容人数を確認するために単一IDでの
参照を必要とすることが実装時に判明したため(P007計画時点でのタスク分割の抜け)。
list_active_rooms と異なり is_active を問わず取得する(無効化された会議室への予約を
ROOM_INACTIVEとして正しく判定するには、まず存在を確認できる必要があるため)。
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Room:
    id: int
    name: str
    capacity: int
    equipment: list[str]
    description: str | None
    is_active: bool
    created_at: str
    updated_at: str


def _row_to_room(row: sqlite3.Row) -> Room:
    return Room(
        id=row["id"],
        name=row["name"],
        capacity=row["capacity"],
        equipment=json.loads(row["equipment_json"]),
        description=row["description"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def list_active_rooms(conn: sqlite3.Connection) -> list[Room]:
    rows = conn.execute(
        "SELECT * FROM rooms WHERE is_active = 1 ORDER BY id"
    ).fetchall()
    return [_row_to_room(row) for row in rows]


def get_room_by_id(conn: sqlite3.Connection, room_id: int) -> Room | None:
    row = conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    return _row_to_room(row) if row else None


def list_rooms(conn: sqlite3.Connection, include_inactive: bool) -> list[Room]:
    if include_inactive:
        rows = conn.execute("SELECT * FROM rooms ORDER BY id").fetchall()
    else:
        rows = conn.execute("SELECT * FROM rooms WHERE is_active = 1 ORDER BY id").fetchall()
    return [_row_to_room(row) for row in rows]


def create_room(
    conn: sqlite3.Connection,
    name: str,
    capacity: int,
    equipment: list[str],
    description: str | None,
    is_active: bool,
    created_at: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO rooms (name, capacity, equipment_json, description, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (name, capacity, json.dumps(equipment, ensure_ascii=False), description, 1 if is_active else 0, created_at, created_at),
    )
    conn.commit()
    return cursor.lastrowid


def update_room(
    conn: sqlite3.Connection,
    room_id: int,
    name: str,
    capacity: int,
    equipment: list[str],
    description: str | None,
    is_active: bool,
    updated_at: str,
) -> None:
    conn.execute(
        """
        UPDATE rooms
        SET name = ?, capacity = ?, equipment_json = ?, description = ?, is_active = ?, updated_at = ?
        WHERE id = ?
        """,
        (name, capacity, json.dumps(equipment, ensure_ascii=False), description, 1 if is_active else 0, updated_at, room_id),
    )
    conn.commit()


def deactivate_room(conn: sqlite3.Connection, room_id: int, updated_at: str) -> None:
    conn.execute(
        "UPDATE rooms SET is_active = 0, updated_at = ? WHERE id = ?",
        (updated_at, room_id),
    )
    conn.commit()
