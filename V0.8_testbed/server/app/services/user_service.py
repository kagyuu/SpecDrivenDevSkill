"""User Service layer (U005-T1, docs/P007-impl-direction/U005-user-management-and-hardening.md).

Validation per docs/P002-frontend-spec.md 3.7節. Self-deactivation
forbidden / last-admin-protected judgment order per
docs/P003-backend-spec.md 4.11〜4.11.2節. Does not touch
app/services/auth_service.py (this task's own 実装してはいけないこと).
"""

from __future__ import annotations

import re
import sqlite3

from app.exceptions import (
    LastAdminProtectedError,
    NotFoundError,
    SelfDeactivationForbiddenError,
    ValidationError,
)
from app.repositories import session_repository, user_repository
from app.repositories.user_repository import UserRow
from app.security.password import hash_password

_EMPLOYEE_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{4,20}$")
_NAME_MAX_LENGTH = 50
_PASSWORD_MIN_LENGTH = 8


def list_users(conn: sqlite3.Connection, include_inactive: bool = False) -> list[UserRow]:
    return user_repository.find_all(conn, include_inactive=include_inactive)


def _validate_common(name: str, password: str | None) -> dict[str, str]:
    fields: dict[str, str] = {}
    if not name or not name.strip():
        fields["name"] = "氏名を入力してください"
    elif len(name) > _NAME_MAX_LENGTH:
        fields["name"] = "氏名は50文字以内で入力してください"

    if password is not None and len(password) < _PASSWORD_MIN_LENGTH:
        fields["password"] = "パスワードは8文字以上で入力してください"

    return fields


def create(
    conn: sqlite3.Connection, employee_id: str, name: str, password: str, role: str
) -> UserRow:
    fields = _validate_common(name, password)

    if not _EMPLOYEE_ID_PATTERN.match(employee_id or ""):
        fields["employee_id"] = "社員IDを入力してください"
    elif user_repository.find_by_id(conn, employee_id) is not None:
        fields["employee_id"] = "この社員IDは既に登録されています"

    if fields:
        raise ValidationError(fields=fields)

    return user_repository.create(conn, employee_id, name, hash_password(password), role)


def update(
    conn: sqlite3.Connection,
    user_id: str,
    name: str,
    password: str | None,
    role: str,
    is_active: bool,
    requesting_user_id: str,
) -> UserRow:
    """docs/P003-backend-spec.md 4.11〜4.11.2節の判定順序:
    1. 対象が自分自身かつ is_active=false への変更 -> SelfDeactivationForbiddenError
    2. 対象が管理者かつ is_active=false への変更 -> 更新後に有効な管理者が0人になるなら
       LastAdminProtectedError
    無効化が成功した場合、同一トランザクションで該当ユーザーの全セッションを削除する。
    """
    existing = user_repository.find_by_id(conn, user_id)
    if existing is None:
        raise NotFoundError("ユーザーが見つかりません")

    fields = _validate_common(name, password)
    if fields:
        raise ValidationError(fields=fields)

    is_deactivating = existing["is_active"] == 1 and not is_active
    if is_deactivating:
        if user_id == requesting_user_id:
            raise SelfDeactivationForbiddenError()
        if existing["role"] == "admin":
            remaining_admins = user_repository.count_active_admins(conn, exclude_user_id=user_id)
            if remaining_admins == 0:
                raise LastAdminProtectedError()

    password_hash = hash_password(password) if password is not None else None
    updated = user_repository.update(conn, user_id, name, password_hash, role, is_active)
    assert updated is not None  # existence already confirmed above

    if is_deactivating:
        session_repository.delete_by_user_id(conn, user_id)

    return updated


def deactivate(conn: sqlite3.Connection, user_id: str, requesting_user_id: str) -> UserRow:
    """`update`の is_active=False 版として同じ検証ロジックを再利用する(このタスクの
    実装内容のとおり)。既存の氏名・権限・パスワードは変更しない。"""
    existing = user_repository.find_by_id(conn, user_id)
    if existing is None:
        raise NotFoundError("ユーザーが見つかりません")

    return update(
        conn,
        user_id,
        existing["name"],
        None,
        existing["role"],
        False,
        requesting_user_id,
    )
