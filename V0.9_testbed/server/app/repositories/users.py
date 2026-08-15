"""users テーブルへのデータアクセス。docs/P003-backend-spec.md §5.1〜§5.4, §6。

このモジュール内のいずれの関数も、現在時刻・現在日付をシステム時計から取得しない
(docs/P003-backend-spec.md §6 のRepository層時刻引数ルール)。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    employee_id: str
    name: str
    password_hash: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        employee_id=row["employee_id"],
        name=row["name"],
        password_hash=row["password_hash"],
        role=row["role"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_user_by_employee_id(conn: sqlite3.Connection, employee_id: str) -> User | None:
    row = conn.execute(
        "SELECT * FROM users WHERE employee_id = ? AND is_active = 1",
        (employee_id,),
    ).fetchone()
    return _row_to_user(row) if row else None


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> User | None:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_user(row) if row else None


def list_users(conn: sqlite3.Connection) -> list[User]:
    rows = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    return [_row_to_user(row) for row in rows]


def create_user(
    conn: sqlite3.Connection,
    employee_id: str,
    name: str,
    password_hash: str,
    role: str,
    is_active: bool,
    created_at: str,
) -> int:
    # employee_id の一意制約違反(sqlite3.IntegrityError)はここで捕捉・変換せず、
    # そのままService層に伝播させる(docs/P007-impl-direction/U004-user-administration.md U004-T2)。
    cursor = conn.execute(
        """
        INSERT INTO users (employee_id, name, password_hash, role, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (employee_id, name, password_hash, role, 1 if is_active else 0, created_at, created_at),
    )
    conn.commit()
    return cursor.lastrowid


def update_user(
    conn: sqlite3.Connection,
    user_id: int,
    name: str,
    role: str,
    is_active: bool,
    updated_at: str,
) -> None:
    conn.execute(
        "UPDATE users SET name = ?, role = ?, is_active = ?, updated_at = ? WHERE id = ?",
        (name, role, 1 if is_active else 0, updated_at, user_id),
    )
    conn.commit()


def deactivate_user(conn: sqlite3.Connection, user_id: int, updated_at: str) -> None:
    conn.execute(
        "UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?",
        (updated_at, user_id),
    )
    conn.commit()
