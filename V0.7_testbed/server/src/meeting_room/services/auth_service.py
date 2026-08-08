"""ログイン・ログアウト・セッション解決(P003 2.2 / 4.3 / 6.1)。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from .. import config, security
from ..errors import ApiError
from ..repositories import sessions_repo, users_repo

#: ログイン失敗時の共通メッセージ(P002 3.1。3ケースとも同一文言)
AUTH_FAILED_MESSAGE = "ユーザーIDまたはパスワードが正しくありません。"

_TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def parse_ts(text: str) -> datetime:
    return datetime.strptime(text, _TS_FORMAT).replace(tzinfo=timezone.utc)


def format_ts(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime(_TS_FORMAT)


def shift(text: str, seconds: int) -> str:
    """時刻文字列を秒単位でずらす(現在時刻の取得は `security.now_utc()` に集約)。"""
    return format_ts(parse_ts(text) + timedelta(seconds=seconds))


def auth_failed() -> ApiError:
    return ApiError(401, "AUTH_FAILED", AUTH_FAILED_MESSAGE)


def unauthenticated() -> ApiError:
    return ApiError(
        401, "UNAUTHENTICATED", "セッションの有効期限が切れました。再度ログインしてください。"
    )


def login(conn: sqlite3.Connection, user_id: str, password: str) -> tuple[str, dict]:
    """API-01。戻り値は `(session_id, user)`。失敗理由は区別しない(P002 3.1)。"""
    now = security.now_utc()
    # 1) 期限切れセッションの掃除
    sessions_repo.delete_expired(conn, now, shift(now, -config.SESSION_IDLE_SECONDS))
    # 2) ユーザー検索
    user = users_repo.find_by_id_with_hash(conn, user_id)
    # 3) 行が無い場合もダミー検証を1回実行して応答時間差を減らす(P003 6.1)
    if user is None:
        security.verify_password(password, security.DUMMY_PASSWORD_HASH)
        raise auth_failed()
    if not security.verify_password(password, user["password_hash"]):
        raise auth_failed()
    if not user["is_active"]:
        raise auth_failed()
    # 4) セッション発行
    session_id = security.new_session_id()
    sessions_repo.create(
        conn,
        session_id,
        user["user_id"],
        created_at=now,
        last_accessed_at=now,
        expires_at=shift(now, config.SESSION_ABSOLUTE_SECONDS),
    )
    return session_id, {k: user[k] for k in ("user_id", "name", "role", "is_active")}


def logout(conn: sqlite3.Connection, session_id: str | None) -> None:
    """API-02。存在しないセッションでも例外にしない。"""
    if session_id:
        sessions_repo.delete(conn, session_id)


def resolve_session(conn: sqlite3.Connection, session_id: str | None) -> dict | None:
    """有効なセッションならユーザーを返し、`last_accessed_at` を更新する(P003 4.3)。

    不成立(期限切れ・無操作超過・所有ユーザーが無効)なら該当行を削除して `None` を返す。
    """
    if not session_id:
        return None
    session = sessions_repo.find(conn, session_id)
    if session is None:
        return None
    now = security.now_utc()
    idle_deadline = shift(session["last_accessed_at"], config.SESSION_IDLE_SECONDS)
    user = users_repo.find_by_id(conn, session["user_id"])
    valid = (
        session["expires_at"] > now
        and idle_deadline > now
        and user is not None
        and user["is_active"]
    )
    if not valid:
        sessions_repo.delete(conn, session_id)
        return None
    sessions_repo.touch(conn, session_id, now)
    return user
