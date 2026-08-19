"""認証Service層。docs/P003-backend-spec.md §5.1〜§5.3。"""

from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta

from app.api.errors import ApiError
from app.repositories.sessions import create_session
from app.repositories.users import User, get_user_by_employee_id
from app.security.password import verify_password
from app.validation.auth import validate_login_input

SESSION_LIFETIME = timedelta(hours=8)


def _auth_failed() -> ApiError:
    # 社員ID・パスワードいずれの誤りでも同一メッセージ(ユーザー列挙防止)。
    # docs/P002-frontend-spec.md §3 S01。
    return ApiError(401, "AUTH_FAILED", "社員IDまたはパスワードが正しくありません")


def login(
    conn: sqlite3.Connection,
    employee_id: str,
    password: str,
    now: datetime,
) -> tuple[User, str, str]:
    validation_errors = validate_login_input(employee_id, password)
    if validation_errors:
        raise ApiError(400, "VALIDATION_ERROR", validation_errors[0])

    user = get_user_by_employee_id(conn, employee_id)
    if user is None:
        raise _auth_failed()
    if not verify_password(password, user.password_hash):
        raise _auth_failed()

    token = secrets.token_hex(32)
    created_at = now.isoformat()
    expires_at = (now + SESSION_LIFETIME).isoformat()
    create_session(conn, token=token, user_id=user.id, created_at=created_at, expires_at=expires_at)

    return user, token, expires_at
