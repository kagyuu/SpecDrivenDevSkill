"""`rooms` テーブルのデータアクセス(P002 6.2 / P003 6.2、ADR-008)。"""

from __future__ import annotations

import sqlite3

_COLUMNS = "room_id, name, capacity, equipment, description, is_active, created_at, updated_at"


def to_room_dict(row: sqlite3.Row | None) -> dict | None:
    """`rooms` の行を P002 5.3 の `Room` 表現に変換する。"""
    if row is None:
        return None
    return {
        "room_id": row["room_id"],
        "name": row["name"],
        "capacity": row["capacity"],
        "equipment": row["equipment"],
        "description": row["description"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def find_by_id(conn: sqlite3.Connection, room_id: int) -> dict | None:
    row = conn.execute(
        f"SELECT {_COLUMNS} FROM rooms WHERE room_id = ?", (room_id,)
    ).fetchone()
    return to_room_dict(row)


def list_rooms(conn: sqlite3.Connection, include_inactive: bool = False) -> list[dict]:
    """`room_id` 昇順の会議室一覧(P002 5.5 API-04)。"""
    sql = f"SELECT {_COLUMNS} FROM rooms"
    if not include_inactive:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY room_id"
    return [d for d in (to_room_dict(r) for r in conn.execute(sql)) if d is not None]


def find_active_by_name(
    conn: sqlite3.Connection, name: str, exclude_room_id: int | None = None
) -> dict | None:
    """同名の**有効な**会議室を探す(更新時は自分自身を除外する。P003 6.2)。"""
    sql = f"SELECT {_COLUMNS} FROM rooms WHERE name = ? AND is_active = 1"
    params: list = [name]
    if exclude_room_id is not None:
        sql += " AND room_id <> ?"
        params.append(exclude_room_id)
    return to_room_dict(conn.execute(sql, params).fetchone())


def insert(
    conn: sqlite3.Connection,
    name: str,
    capacity: int,
    equipment: str,
    description: str,
    is_active: bool,
    now: str,
) -> int:
    cursor = conn.execute(
        "INSERT INTO rooms(name, capacity, equipment, description, is_active, created_at,"
        " updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, capacity, equipment, description, 1 if is_active else 0, now, now),
    )
    return int(cursor.lastrowid)


def update(
    conn: sqlite3.Connection,
    room_id: int,
    name: str,
    capacity: int,
    equipment: str,
    description: str,
    is_active: bool,
    now: str,
) -> None:
    """全項目送信の全置換更新(P002 5.5 API-06)。"""
    conn.execute(
        "UPDATE rooms SET name = ?, capacity = ?, equipment = ?, description = ?,"
        " is_active = ?, updated_at = ? WHERE room_id = ?",
        (name, capacity, equipment, description, 1 if is_active else 0, now, room_id),
    )


def set_active(conn: sqlite3.Connection, room_id: int, is_active: bool, now: str) -> None:
    """論理削除(ADR-008)。物理削除はしない。"""
    conn.execute(
        "UPDATE rooms SET is_active = ?, updated_at = ? WHERE room_id = ?",
        (1 if is_active else 0, now, room_id),
    )
