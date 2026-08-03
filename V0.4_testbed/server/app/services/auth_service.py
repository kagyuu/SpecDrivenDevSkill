"""認証Service層 (docs/P003-backend-spec.md §2)."""
from __future__ import annotations

import sqlite3

from app.core.exceptions import InvalidCredentialsError
from app.core.password import verify_password
from app.repositories import session_repository, user_repository


def login(conn: sqlite3.Connection, employee_id: str, password: str) -> tuple[sqlite3.Row, str]:
    """ログイン処理順序 (docs/P003-backend-spec.md §2 手順1〜4)."""
    user = user_repository.find_by_employee_id(conn, employee_id)
    if user is None or not user["is_active"]:
        # 存在しない場合と無効化済みの場合を区別しない(アカウント存在の推測防止)
        raise InvalidCredentialsError("社員IDまたはパスワードが正しくありません")
    if not verify_password(password, user["password_hash"]):
        raise InvalidCredentialsError("社員IDまたはパスワードが正しくありません")
    session_id = session_repository.create(conn, user["id"])
    return user, session_id


def resolve_current_user(conn: sqlite3.Connection, session_id: str | None) -> sqlite3.Row | None:
    """セッションからユーザーを解決する。無効化済みユーザーは遅延失効させる。"""
    if not session_id:
        return None
    session = session_repository.find_valid(conn, session_id)
    if session is None:
        return None
    user = user_repository.find_by_id(conn, session["user_id"])
    if user is None or not user["is_active"]:
        session_repository.delete(conn, session_id)
        return None
    return user


def logout(conn: sqlite3.Connection, session_id: str | None) -> None:
    """存在しなくても例外にしない(冪等)。"""
    if session_id:
        session_repository.delete(conn, session_id)
