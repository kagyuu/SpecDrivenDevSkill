"""`sessions` テーブルのデータアクセス(P003 2.2 / 3.2、ADR-006)。"""

from __future__ import annotations

import sqlite3


def create(
    conn: sqlite3.Connection,
    session_id: str,
    user_id: str,
    created_at: str,
    last_accessed_at: str,
    expires_at: str,
) -> None:
    conn.execute(
        "INSERT INTO sessions(session_id, user_id, created_at, last_accessed_at, expires_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (session_id, user_id, created_at, last_accessed_at, expires_at),
    )


def find(conn: sqlite3.Connection, session_id: str) -> dict | None:
    row = conn.execute(
        "SELECT session_id, user_id, created_at, last_accessed_at, expires_at"
        " FROM sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def touch(conn: sqlite3.Connection, session_id: str, now: str) -> None:
    """スライディング期限のため `last_accessed_at` を更新する(P003 2.2)。"""
    conn.execute(
        "UPDATE sessions SET last_accessed_at = ? WHERE session_id = ?", (now, session_id)
    )


def delete(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))


def delete_by_user(conn: sqlite3.Connection, user_id: str) -> None:
    """権限変更・無効化時のセッション一括削除(P003 4.3)。"""
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))


def delete_expired(conn: sqlite3.Connection, now: str, idle_threshold: str) -> None:
    """期限切れ行の掃除。ログイン処理のたびに1回実行する(P003 2.2)。"""
    conn.execute(
        "DELETE FROM sessions WHERE expires_at <= ? OR last_accessed_at <= ?",
        (now, idle_threshold),
    )


def count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) AS c FROM sessions").fetchone()["c"])
