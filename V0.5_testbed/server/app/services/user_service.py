"""ユーザーService層 (docs/P003-backend-spec.md §7.15〜§7.17)."""
from __future__ import annotations

import sqlite3

from app.core.exceptions import NotFoundError, ValidationError
from app.core.password import hash_password
from app.core.validators import (
    validate_employee_id,
    validate_password_policy,
    validate_role,
    validate_user_name,
)
from app.repositories import user_repository


def create(conn: sqlite3.Connection, data: dict) -> sqlite3.Row:
    if not validate_employee_id(data.get("employee_id", "")):
        raise ValidationError("社員IDは半角英数字1〜20文字で入力してください",
                               details=[{"field": "employee_id", "reason": "invalid format"}])
    if not validate_user_name(data.get("name", "")):
        raise ValidationError("氏名は1〜50文字で入力してください",
                               details=[{"field": "name", "reason": "invalid length"}])
    if not validate_role(data.get("role")):
        raise ValidationError("権限はgeneralまたはadminを指定してください",
                               details=[{"field": "role", "reason": "invalid"}])
    if not validate_password_policy(data.get("initial_password", "")):
        raise ValidationError("初期パスワードは8文字以上、英字・数字を含めてください",
                               details=[{"field": "initial_password", "reason": "policy violation"}])
    if user_repository.find_by_employee_id(conn, data["employee_id"]) is not None:
        raise ValidationError("社員IDが既に使用されています",
                               details=[{"field": "employee_id", "reason": "duplicate"}])
    password_hash = hash_password(data["initial_password"])
    return user_repository.insert(conn, data["employee_id"], data["name"], password_hash,
                                   data["role"], data.get("is_active", True))


def update(conn: sqlite3.Connection, user_id: int, data: dict) -> sqlite3.Row:
    existing = user_repository.find_by_id(conn, user_id)
    if existing is None:
        raise NotFoundError("ユーザーが見つかりません")
    if not validate_user_name(data.get("name", "")):
        raise ValidationError("氏名は1〜50文字で入力してください",
                               details=[{"field": "name", "reason": "invalid length"}])
    if not validate_role(data.get("role")):
        raise ValidationError("権限はgeneralまたはadminを指定してください",
                               details=[{"field": "role", "reason": "invalid"}])
    new_password = data.get("new_password")
    new_password_hash = None
    if new_password:
        if not validate_password_policy(new_password):
            raise ValidationError("パスワードは8文字以上、英字・数字を含めてください",
                                   details=[{"field": "new_password", "reason": "policy violation"}])
        new_password_hash = hash_password(new_password)
    return user_repository.update(conn, user_id, data["name"], data["role"],
                                   data.get("is_active", True), new_password_hash)


def deactivate(conn: sqlite3.Connection, user_id: int, current_user_id: int) -> sqlite3.Row:
    if user_id == current_user_id:
        raise ValidationError("自分自身を無効化することはできません",
                               details=[{"field": "user_id", "reason": "self-deactivation not allowed"}])
    result = user_repository.set_active(conn, user_id, False)
    if result is None:
        raise NotFoundError("ユーザーが見つかりません")
    return result
