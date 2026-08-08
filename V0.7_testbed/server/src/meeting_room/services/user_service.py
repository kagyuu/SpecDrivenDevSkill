"""ユーザーの業務ルール(P002 5.6 / P003 6.3)。"""

from __future__ import annotations

import sqlite3

from .. import db, security
from ..errors import ApiError
from ..repositories import sessions_repo, users_repo

SCOPE_MANAGEMENT = "management"
SCOPE_ATTENDEE_CANDIDATES = "attendee_candidates"

DUPLICATE_MESSAGE = "この社員IDはすでに登録されています。"
NOT_FOUND_MESSAGE = "対象のデータが見つかりません。削除された可能性があります。"
SELF_DEACTIVATE_MESSAGE = "自分自身を無効化することはできません。"
# ★FIXME★ 最後の有効な管理者を保護するときの文言はP002・P003に明記がないため、Agentの想定で補った
LAST_ADMIN_MESSAGE = "最後の有効な管理者を無効化または一般に変更することはできません。"


def list_users(
    conn: sqlite3.Connection, user: dict, scope: str, include_inactive: bool = True
) -> list[dict]:
    """API-08。`scope` により2経路に分岐する(P003 6.3)。認可はハンドラ側で適用済み。"""
    if scope == SCOPE_ATTENDEE_CANDIDATES:
        # `role`・`is_active` を SELECT 句のレベルで含めない
        return users_repo.list_active_id_and_name(conn)
    return users_repo.list_users(conn, include_inactive=include_inactive)


def create_user(conn: sqlite3.Connection, payload) -> dict:
    """API-09。無効化済みの同一IDも重複として扱う。"""
    now = security.now_utc()
    with db.transaction(conn):
        if users_repo.find_by_id(conn, payload.user_id) is not None:
            raise ApiError(409, "DUPLICATE_KEY", DUPLICATE_MESSAGE)
        users_repo.insert(
            conn,
            payload.user_id,
            payload.name,
            security.hash_password(payload.password),
            payload.role,
            payload.is_active,
            now,
        )
    return users_repo.find_by_id(conn, payload.user_id)


def _is_last_active_admin(conn: sqlite3.Connection, target: dict) -> bool:
    if target["role"] != "admin" or not target["is_active"]:
        return False
    return users_repo.count_active_admins(conn, exclude_user_id=target["user_id"]) == 0


def update_user(conn: sqlite3.Connection, user_id: str, payload) -> dict:
    """API-10。`user_id` は変更不可。`password` 省略時はハッシュを更新しない。"""
    now = security.now_utc()
    with db.transaction(conn):
        target = users_repo.find_by_id(conn, user_id)
        if target is None:
            raise ApiError(404, "NOT_FOUND", NOT_FOUND_MESSAGE)
        demoting = payload.role == "general"
        deactivating = payload.is_active is False
        if (demoting or deactivating) and _is_last_active_admin(conn, target):
            raise ApiError(409, "CONSTRAINT_VIOLATION", LAST_ADMIN_MESSAGE)
        password_hash = (
            security.hash_password(payload.password) if payload.password else None
        )
        users_repo.update(
            conn, user_id, payload.name, payload.role, payload.is_active, now,
            password_hash=password_hash,
        )
        # 権限変更または無効化があればセッションを全削除する(P003 4.3)
        if target["role"] != payload.role or (target["is_active"] and deactivating):
            sessions_repo.delete_by_user(conn, user_id)
    return users_repo.find_by_id(conn, user_id)


def deactivate_user(conn: sqlite3.Connection, actor: dict, target_id: str) -> None:
    """API-11。自分自身・最後の有効な管理者は無効化できない。既に無効なら何もしない(冪等)。"""
    now = security.now_utc()
    with db.transaction(conn):
        target = users_repo.find_by_id(conn, target_id)
        if target is None:
            raise ApiError(404, "NOT_FOUND", NOT_FOUND_MESSAGE)
        if not target["is_active"]:
            return  # 冪等(P002 5.6 API-11)
        if actor["user_id"] == target_id:
            raise ApiError(409, "CONSTRAINT_VIOLATION", SELF_DEACTIVATE_MESSAGE)
        if _is_last_active_admin(conn, target):
            raise ApiError(409, "CONSTRAINT_VIOLATION", LAST_ADMIN_MESSAGE)
        users_repo.set_active(conn, target_id, False, now)
        sessions_repo.delete_by_user(conn, target_id)
