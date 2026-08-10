"""Shared FastAPI dependencies.

get_current_user (U001-T4) is the cross-cutting authentication dependency
called out in docs/P003-backend-spec.md 4.3節 ("この検証ロジックはFastAPIの
依存性注入(Depends(get_current_user))として実装し、認証が必要な全エンドポイント
で共通利用する"). require_admin (U002-T2) layers authorization on top of it.
Every router added in later sprints reuses these two rather than
re-implementing cookie/session/role lookup.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

from fastapi import Cookie, Depends

from app.db.connection import get_connection
from app.exceptions import ForbiddenError
from app.repositories.user_repository import UserRow
from app.services import auth_service


def get_db() -> Iterator[sqlite3.Connection]:
    """Per-request SQLite connection, closed once the request finishes."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    session_id: str | None = Cookie(default=None),
    conn: sqlite3.Connection = Depends(get_db),
) -> UserRow:
    """Resolve the current user from the session_id Cookie.

    Raises app.services.auth_service.UnauthorizedError when the cookie is
    missing, or does not map to a valid/unexpired session - app/errors.py
    registers an app-wide handler that turns that into the 401 response
    docs/P002-frontend-spec.md 4章冒頭 specifies for all authenticated APIs.
    """
    return auth_service.get_current_user(conn, session_id)


def require_admin(user: UserRow = Depends(get_current_user)) -> UserRow:
    """Layers an authorization check on top of get_current_user (U002-T2,
    docs/P007-impl-direction/U002-room-management.md).

    docs/P002-frontend-spec.md 2章: "未ログインの場合は401を返す(403と401を
    区別する。存在確認より認証確認を優先する)" - Depends(get_current_user) runs
    first (401 for missing/invalid session), and only once that succeeds does
    this dependency check role (403 for a valid but non-admin session).
    """
    if user["role"] != "admin":
        raise ForbiddenError()
    return user
