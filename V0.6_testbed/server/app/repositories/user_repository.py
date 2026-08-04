"""ユーザーRepository層 (SQLite CRUD)。

U001-3: find_by_employee_id, find_by_id
U002-2: list, insert, update, set_active
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_by_employee_id(conn: sqlite3.Connection, employee_id: str) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM USERS WHERE employee_id = ?", (employee_id,))
    return cur.fetchone()


def find_by_id(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM USERS WHERE id = ?", (user_id,))
    return cur.fetchone()


def list(conn: sqlite3.Connection, include_inactive: bool = True) -> list[sqlite3.Row]:
    if include_inactive:
        cur = conn.execute("SELECT * FROM USERS ORDER BY id")
    else:
        cur = conn.execute("SELECT * FROM USERS WHERE is_active = 1 ORDER BY id")
    return cur.fetchall()


def insert(conn: sqlite3.Connection, employee_id: str, name: str, password_hash: str,
           role: str, is_active: bool = True) -> sqlite3.Row:
    now = _now_iso()
    cur = conn.execute(
        "INSERT INTO USERS (employee_id, name, password_hash, role, is_active, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (employee_id, name, password_hash, role, 1 if is_active else 0, now, now),
    )
    conn.commit()
    return find_by_id(conn, cur.lastrowid)


def update(conn: sqlite3.Connection, user_id: int, name: str, role: str, is_active: bool,
           new_password_hash: str | None = None) -> sqlite3.Row | None:
    if find_by_id(conn, user_id) is None:
        return None
    now = _now_iso()
    if new_password_hash is not None:
        conn.execute(
            "UPDATE USERS SET name = ?, role = ?, is_active = ?, password_hash = ?, updated_at = ? "
            "WHERE id = ?",
            (name, role, 1 if is_active else 0, new_password_hash, now, user_id),
        )
    else:
        conn.execute(
            "UPDATE USERS SET name = ?, role = ?, is_active = ?, updated_at = ? WHERE id = ?",
            (name, role, 1 if is_active else 0, now, user_id),
        )
    conn.commit()
    return find_by_id(conn, user_id)


def set_active(conn: sqlite3.Connection, user_id: int, is_active: bool) -> sqlite3.Row | None:
    if find_by_id(conn, user_id) is None:
        return None
    now = _now_iso()
    conn.execute(
        "UPDATE USERS SET is_active = ?, updated_at = ? WHERE id = ?",
        (1 if is_active else 0, now, user_id),
    )
    conn.commit()
    return find_by_id(conn, user_id)
