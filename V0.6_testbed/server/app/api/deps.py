"""認証・認可・DB接続のための依存関数 (docs/P003-backend-spec.md §1, §4)。

★deviation★ FastAPIの `Depends` の代わりに、Starlette上ではハンドラから明示的に
呼び出すプレーンな関数として実装する(docs/P101-impl-context.md参照)。
"""
from __future__ import annotations

import sqlite3

from starlette.requests import Request

from app.core.exceptions import AuthRequiredError, ForbiddenError
from app.db.connection import get_connection
from app.services import auth_service

SESSION_COOKIE_NAME = "session_id"


def get_conn(request: Request) -> sqlite3.Connection:
    db_path = getattr(request.app.state, "db_path", None)
    return get_connection(db_path)


def require_auth(request: Request, conn: sqlite3.Connection) -> sqlite3.Row:
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    user = auth_service.resolve_current_user(conn, session_id)
    if user is None:
        raise AuthRequiredError("認証が必要です")
    return user


def require_admin(request: Request, conn: sqlite3.Connection) -> sqlite3.Row:
    user = require_auth(request, conn)
    if user["role"] != "admin":
        raise ForbiddenError("管理者権限が必要です")
    return user
