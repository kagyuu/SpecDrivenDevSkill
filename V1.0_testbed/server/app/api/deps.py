"""FastAPI依存性: DB接続の取得、認証ミドルウェア。docs/P003-backend-spec.md §2.1。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Iterator

from fastapi import Depends, Request

from app.api.errors import ApiError
from app.db.connection import get_connection
from app.repositories.sessions import get_session, is_session_valid
from app.repositories.users import User, get_user_by_id

SESSION_COOKIE_NAME = "session_id"


def get_db() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _unauthenticated() -> ApiError:
    return ApiError(401, "UNAUTHENTICATED", "ログインが必要です")


def get_current_user(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise _unauthenticated()

    session = get_session(conn, token)
    if session is None:
        raise _unauthenticated()

    now = datetime.now(timezone.utc)
    if not is_session_valid(session, now=now):
        raise _unauthenticated()

    user = get_user_by_id(conn, session.user_id)
    if user is None or not user.is_active:
        raise _unauthenticated()

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise ApiError(403, "FORBIDDEN", "この操作には管理者権限が必要です")
    return user
