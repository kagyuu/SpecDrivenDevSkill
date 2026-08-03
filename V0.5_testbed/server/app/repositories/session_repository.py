"""セッションRepository層 (docs/P003-backend-spec.md §2, §6.2)."""
from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

SESSION_LIFETIME = timedelta(hours=8)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def create(conn: sqlite3.Connection, user_id: int) -> str:
    session_id = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + SESSION_LIFETIME
    conn.execute(
        "INSERT INTO SESSIONS (session_id, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
        (session_id, user_id, _iso(expires_at), _iso(now)),
    )
    conn.commit()
    return session_id


def find_valid(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM SESSIONS WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    if row is None:
        return None
    if row["expires_at"] <= _now_iso():
        return None
    return row


def delete(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute("DELETE FROM SESSIONS WHERE session_id = ?", (session_id,))
    conn.commit()
