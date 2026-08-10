"""Session repository (U001-T3, docs/P007-impl-direction/U001-foundation-and-auth.md).

Implements the sessions table access needed by ADR-003 (Cookie-based
server-side sessions): create / find_valid / delete / delete_by_user_id.

Called by app/services/auth_service.py (U001-T3, session_id generated there
via secrets.token_urlsafe(32)) and covered indirectly by
server/tests/test_auth_service.py.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import TypedDict

SESSION_LIFETIME = timedelta(hours=8)  # docs/P002-frontend-spec.md 2章


class SessionRow(TypedDict):
    session_id: str
    user_id: str
    expires_at: str
    created_at: str


def create(conn: sqlite3.Connection, session_id: str, user_id: str) -> SessionRow:
    """Insert a new session row with an 8-hour fixed expiry from now."""
    now = datetime.now(timezone.utc)
    expires_at = now + SESSION_LIFETIME
    with conn:
        conn.execute(
            "INSERT INTO sessions (session_id, user_id, expires_at, created_at) "
            "VALUES (?, ?, ?, ?)",
            (session_id, user_id, expires_at.isoformat(), now.isoformat()),
        )
    return {
        "session_id": session_id,
        "user_id": user_id,
        "expires_at": expires_at.isoformat(),
        "created_at": now.isoformat(),
    }


def find_valid(conn: sqlite3.Connection, session_id: str) -> SessionRow | None:
    """Return the session row only if it exists and has not expired."""
    row = conn.execute(
        "SELECT session_id, user_id, expires_at, created_at "
        "FROM sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        return None
    if datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
        return None
    return dict(row)


def delete(conn: sqlite3.Connection, session_id: str) -> None:
    """Delete a session. Idempotent: no error if it does not exist."""
    with conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))


def delete_by_user_id(conn: sqlite3.Connection, user_id: str) -> None:
    """Delete every session belonging to a user (used when deactivating a user,
    docs/P003-backend-spec.md 4.11〜4.11.2節)."""
    with conn:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
