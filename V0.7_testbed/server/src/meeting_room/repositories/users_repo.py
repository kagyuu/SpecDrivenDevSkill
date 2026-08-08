"""`users` テーブルのデータアクセス(P002 6.2 / P003 6.3)。

SELECT句に `password_hash` を含めるのは `find_by_id_with_hash` のみ(P002 5.3)。
"""

from __future__ import annotations

import sqlite3

#: `password_hash` を含まない共通のSELECT句(P002 5.3)
_PUBLIC_COLUMNS = "user_id, name, role, is_active, created_at, updated_at"


def to_user_dict(row: sqlite3.Row | None) -> dict | None:
    """`users` の行を P002 5.3 の `User` 表現に変換する。"""
    if row is None:
        return None
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def find_by_id(conn: sqlite3.Connection, user_id: str) -> dict | None:
    row = conn.execute(
        f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    return to_user_dict(row)


def find_by_id_with_hash(conn: sqlite3.Connection, user_id: str) -> dict | None:
    """認証専用。`password_hash` を含む唯一の関数(P003 6.1 API-01)。"""
    row = conn.execute(
        f"SELECT {_PUBLIC_COLUMNS}, password_hash FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    user = to_user_dict(row)
    assert user is not None
    user["password_hash"] = row["password_hash"]
    return user


def list_users(conn: sqlite3.Connection, include_inactive: bool = True) -> list[dict]:
    """`user_id` 昇順のユーザー一覧(P002 5.6 API-08 `scope=management`)。"""
    sql = f"SELECT {_PUBLIC_COLUMNS} FROM users"
    if not include_inactive:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY user_id"
    return [d for d in (to_user_dict(r) for r in conn.execute(sql)) if d is not None]


def list_active_id_and_name(conn: sqlite3.Connection) -> list[dict]:
    """参加者候補(`scope=attendee_candidates`)。`user_id` と `name` だけを返す(P003 6.3)。"""
    return [
        {"user_id": r["user_id"], "name": r["name"]}
        for r in conn.execute(
            "SELECT user_id, name FROM users WHERE is_active = 1 ORDER BY user_id"
        )
    ]


def insert(
    conn: sqlite3.Connection,
    user_id: str,
    name: str,
    password_hash: str,
    role: str,
    is_active: bool,
    now: str,
) -> None:
    conn.execute(
        "INSERT INTO users(user_id, name, password_hash, role, is_active, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, name, password_hash, role, 1 if is_active else 0, now, now),
    )


def update(
    conn: sqlite3.Connection,
    user_id: str,
    name: str,
    role: str,
    is_active: bool,
    now: str,
    password_hash: str | None = None,
) -> None:
    """全置換更新(P002 5.6 API-10)。`password_hash` は指定時のみ更新する。"""
    if password_hash is None:
        conn.execute(
            "UPDATE users SET name = ?, role = ?, is_active = ?, updated_at = ?"
            " WHERE user_id = ?",
            (name, role, 1 if is_active else 0, now, user_id),
        )
    else:
        conn.execute(
            "UPDATE users SET name = ?, role = ?, is_active = ?, password_hash = ?,"
            " updated_at = ? WHERE user_id = ?",
            (name, role, 1 if is_active else 0, password_hash, now, user_id),
        )


def set_active(conn: sqlite3.Connection, user_id: str, is_active: bool, now: str) -> None:
    """論理削除(ADR-008)。"""
    conn.execute(
        "UPDATE users SET is_active = ?, updated_at = ? WHERE user_id = ?",
        (1 if is_active else 0, now, user_id),
    )


def count_active_admins(conn: sqlite3.Connection, exclude_user_id: str | None = None) -> int:
    """有効な管理者の人数(「最後の有効な管理者」判定用。P003 6.3)。"""
    sql = "SELECT COUNT(*) AS c FROM users WHERE role = 'admin' AND is_active = 1"
    params: tuple = ()
    if exclude_user_id is not None:
        sql += " AND user_id <> ?"
        params = (exclude_user_id,)
    return int(conn.execute(sql, params).fetchone()["c"])
