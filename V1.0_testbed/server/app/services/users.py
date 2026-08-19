"""ユーザーService層。docs/P003-backend-spec.md §5.11。"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from app.api.errors import ApiError
from app.repositories.users import (
    User,
    create_user,
    deactivate_user,
    get_user_by_id,
    list_users,
    update_user,
)
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.security.password import hash_password


def list_users_flow(conn: sqlite3.Connection) -> list[User]:
    return list_users(conn)


def create_user_flow(conn: sqlite3.Connection, payload: UserCreateRequest, now: datetime) -> User:
    password_hash = hash_password(payload.initial_password)
    try:
        user_id = create_user(
            conn,
            employee_id=payload.employee_id,
            name=payload.name,
            password_hash=password_hash,
            role=payload.role,
            is_active=payload.is_active,
            created_at=now.isoformat(),
        )
    except sqlite3.IntegrityError as exc:
        raise ApiError(409, "DUPLICATE_EMPLOYEE_ID", "この社員IDは既に登録されています") from exc
    return get_user_by_id(conn, user_id)


def update_user_flow(
    conn: sqlite3.Connection,
    user_id: int,
    payload: UserUpdateRequest,
    now: datetime,
) -> User:
    existing = get_user_by_id(conn, user_id)
    if existing is None:
        raise ApiError(404, "NOT_FOUND", "指定したユーザーが見つかりません")

    update_user(conn, user_id, name=payload.name, role=payload.role, is_active=payload.is_active, updated_at=now.isoformat())
    return get_user_by_id(conn, user_id)


def deactivate_user_flow(conn: sqlite3.Connection, user_id: int, current_user: User, now: datetime) -> None:
    if user_id == current_user.id:
        raise ApiError(400, "CANNOT_DEACTIVATE_SELF", "自分自身のアカウントは無効化できません")

    existing = get_user_by_id(conn, user_id)
    if existing is None:
        raise ApiError(404, "NOT_FOUND", "指定したユーザーが見つかりません")

    deactivate_user(conn, user_id, updated_at=now.isoformat())
