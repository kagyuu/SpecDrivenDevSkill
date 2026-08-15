"""sessions テーブルへのデータアクセス。docs/P003-backend-spec.md §2.1, §5.1〜§5.3, §6。

``is_session_valid`` を含め、このモジュールのいずれの関数も内部で ``datetime.now()`` 等の
システム時計を呼び出さない。有効期限判定に必要な「現在時刻」は、呼び出し元(Service層)が
計算して明示的な引数として渡す。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Session:
    token: str
    user_id: int
    created_at: str
    expires_at: str


def create_session(
    conn: sqlite3.Connection,
    token: str,
    user_id: int,
    created_at: str,
    expires_at: str,
) -> None:
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, created_at, expires_at),
    )
    conn.commit()


def get_session(conn: sqlite3.Connection, token: str) -> Session | None:
    row = conn.execute("SELECT * FROM sessions WHERE token = ?", (token,)).fetchone()
    if not row:
        return None
    return Session(
        token=row["token"],
        user_id=row["user_id"],
        created_at=row["created_at"],
        expires_at=row["expires_at"],
    )


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()


def is_session_valid(session: Session, now: datetime) -> bool:
    expires_at = datetime.fromisoformat(session.expires_at)
    return now < expires_at
