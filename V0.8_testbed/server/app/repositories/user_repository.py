"""User repository.

U001-T3 implements the read methods needed by app/services/auth_service.py
(find_by_id, find_active_by_id). U003-T2 adds find_active_for_directory
(see that function's own docstring for why, ahead of its originally listed
task). U005-T1 adds full CRUD (find_all/create/update/deactivate/
count_active_admins).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import TypedDict


class UserRow(TypedDict):
    user_id: str
    name: str
    password_hash: str
    role: str
    is_active: int


def find_by_id(conn: sqlite3.Connection, user_id: str) -> UserRow | None:
    """Return the user row regardless of is_active, or None if not found."""
    row = conn.execute(
        "SELECT user_id, name, password_hash, role, is_active "
        "FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def find_active_by_id(conn: sqlite3.Connection, user_id: str) -> UserRow | None:
    """Return the user row only if it exists and is_active = 1."""
    row = conn.execute(
        "SELECT user_id, name, password_hash, role, is_active "
        "FROM users WHERE user_id = ? AND is_active = 1",
        (user_id,),
    ).fetchone()
    return dict(row) if row is not None else None


class DirectoryEntry(TypedDict):
    employee_id: str
    name: str


def find_active_for_directory(conn: sqlite3.Connection) -> list[DirectoryEntry]:
    """docs/P003-backend-spec.md 4.10節: 参加者候補一覧(GET /api/users/directory,
    reservation_service.list_participant_candidates)向けの軽量クエリ。
    password_hash・role・is_active はSELECT句に含めない(万一のフィールド漏洩を
    型レベルでも防ぐ、という4.10節の方針どおり)。

    Added by U003-T2 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md)
    even though this file is not listed in that task's own 作成・編集対象ファイル -
    docs/P003-backend-spec.md 4.10節 explicitly requires this method to exist
    for list_participant_candidates to be implementable, so it is added here
    rather than left as a gap between the spec and the sprint file's own
    bookkeeping.
    """
    rows = conn.execute(
        "SELECT user_id, name FROM users WHERE is_active = 1 ORDER BY user_id"
    ).fetchall()
    return [{"employee_id": row["user_id"], "name": row["name"]} for row in rows]


def find_all(conn: sqlite3.Connection, include_inactive: bool = False) -> list[UserRow]:
    """docs/P002-frontend-spec.md 4.10節。password_hashを含む(app/schemas/user.py
    のUserResponse側でこの列を除外することでレスポンスからの漏洩を防ぐ、
    docs/P003-backend-spec.md 4.11〜4.11.2節の方針どおり)。"""
    query = "SELECT user_id, name, password_hash, role, is_active FROM users"
    if not include_inactive:
        query += " WHERE is_active = 1"
    query += " ORDER BY user_id"
    rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]  # type: ignore[misc]


def create(
    conn: sqlite3.Connection, user_id: str, name: str, password_hash: str, role: str
) -> UserRow:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO users (user_id, name, password_hash, role, is_active, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 1, ?, ?)",
        (user_id, name, password_hash, role, now, now),
    )
    conn.commit()
    user = find_by_id(conn, user_id)
    assert user is not None  # just inserted
    return user


def update(
    conn: sqlite3.Connection,
    user_id: str,
    name: str,
    password_hash: str | None,
    role: str,
    is_active: bool,
) -> UserRow | None:
    """`password_hash=None` leaves the stored hash unchanged
    (docs/P002-frontend-spec.md 3.7節: "パスワード... 編集時は任意(空欄=変更なし)")."""
    now = datetime.now(timezone.utc).isoformat()
    if password_hash is None:
        cursor = conn.execute(
            "UPDATE users SET name = ?, role = ?, is_active = ?, updated_at = ? WHERE user_id = ?",
            (name, role, int(is_active), now, user_id),
        )
    else:
        cursor = conn.execute(
            "UPDATE users SET name = ?, password_hash = ?, role = ?, is_active = ?, "
            "updated_at = ? WHERE user_id = ?",
            (name, password_hash, role, int(is_active), now, user_id),
        )
    if cursor.rowcount == 0:
        conn.commit()
        return None
    conn.commit()
    return find_by_id(conn, user_id)


def deactivate(conn: sqlite3.Connection, user_id: str) -> UserRow | None:
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "UPDATE users SET is_active = 0, updated_at = ? WHERE user_id = ?", (now, user_id)
    )
    if cursor.rowcount == 0:
        conn.commit()
        return None
    conn.commit()
    return find_by_id(conn, user_id)


def count_active_admins(conn: sqlite3.Connection, exclude_user_id: str | None = None) -> int:
    """docs/P003-backend-spec.md 4.11〜4.11.2節: 最後の管理者保護の判定に使う。
    `exclude_user_id` を指定すると、その1件を無効化した"後"の件数を先読みで
    数えられる(対象ユーザー自身をCOUNTから除外する)。"""
    query = "SELECT COUNT(*) AS n FROM users WHERE role = 'admin' AND is_active = 1"
    params: list = []
    if exclude_user_id is not None:
        query += " AND user_id != ?"
        params.append(exclude_user_id)
    row = conn.execute(query, params).fetchone()
    return row["n"]
