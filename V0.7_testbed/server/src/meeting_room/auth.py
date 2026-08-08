"""認証・認可の共通処理(P003 4.3)。

`request.state.user` にログイン中ユーザーを設定する。
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from . import db
from .errors import ApiError
from .services import auth_service

COOKIE_NAME = "sid"


def db_path_of(request) -> str | None:
    return getattr(request.app.state, "db_path", None)


@contextmanager
def open_conn(request) -> Iterator[sqlite3.Connection]:
    """リクエスト単位のDB接続(P003 2.2)。"""
    conn = db.connect(db_path_of(request))
    try:
        yield conn
    finally:
        conn.close()


def session_id_of(request) -> str | None:
    return request.cookies.get(COOKIE_NAME)


def require_login(request) -> dict:
    """セッションが有効であること。不成立なら 401 `UNAUTHENTICATED`。"""
    user = getattr(request.state, "user", None)
    if user is not None:
        return user
    with open_conn(request) as conn:
        with db.transaction(conn):
            user = auth_service.resolve_session(conn, session_id_of(request))
    if user is None:
        raise auth_service.unauthenticated()
    request.state.user = user
    return user


def require_admin(request) -> dict:
    """加えて `role == 'admin'`。不成立なら 403 `FORBIDDEN`。"""
    user = require_login(request)
    if user["role"] != "admin":
        raise forbidden()
    return user


def require_owner_or_admin(request, owner_user_id: str) -> dict:
    """予約者本人または管理者。不成立なら 403 `FORBIDDEN`。"""
    user = require_login(request)
    if user["user_id"] != owner_user_id and user["role"] != "admin":
        raise forbidden()
    return user


def forbidden() -> ApiError:
    return ApiError(403, "FORBIDDEN", "この操作を行う権限がありません。")
