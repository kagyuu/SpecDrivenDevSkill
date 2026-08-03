"""会議室Repository層 (docs/P003-backend-spec.md §7.4〜§7.7)."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def list(conn: sqlite3.Connection, include_inactive: bool = False) -> list[sqlite3.Row]:
    if include_inactive:
        cur = conn.execute("SELECT * FROM ROOMS ORDER BY id")
    else:
        cur = conn.execute("SELECT * FROM ROOMS WHERE is_active = 1 ORDER BY id")
    return cur.fetchall()


def find(conn: sqlite3.Connection, room_id: int) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM ROOMS WHERE id = ?", (room_id,))
    return cur.fetchone()


def find_by_name_active(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    """有効な会議室のうち同名のものを検索する(重複チェック用)。"""
    cur = conn.execute("SELECT * FROM ROOMS WHERE name = ? AND is_active = 1", (name,))
    return cur.fetchone()


def insert(conn: sqlite3.Connection, name: str, capacity: int, equipment: str,
           is_active: bool = True) -> sqlite3.Row:
    now = _now_iso()
    cur = conn.execute(
        "INSERT INTO ROOMS (name, capacity, equipment, is_active, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, capacity, equipment, 1 if is_active else 0, now, now),
    )
    conn.commit()
    return find(conn, cur.lastrowid)


def update(conn: sqlite3.Connection, room_id: int, name: str, capacity: int, equipment: str,
           is_active: bool) -> sqlite3.Row | None:
    if find(conn, room_id) is None:
        return None
    now = _now_iso()
    conn.execute(
        "UPDATE ROOMS SET name = ?, capacity = ?, equipment = ?, is_active = ?, updated_at = ? "
        "WHERE id = ?",
        (name, capacity, equipment, 1 if is_active else 0, now, room_id),
    )
    conn.commit()
    return find(conn, room_id)


def set_active(conn: sqlite3.Connection, room_id: int, is_active: bool) -> sqlite3.Row | None:
    if find(conn, room_id) is None:
        return None
    now = _now_iso()
    conn.execute(
        "UPDATE ROOMS SET is_active = ?, updated_at = ? WHERE id = ?",
        (1 if is_active else 0, now, room_id),
    )
    conn.commit()
    return find(conn, room_id)
