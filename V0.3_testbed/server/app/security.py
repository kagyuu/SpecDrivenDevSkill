"""パスワードハッシュ・セッション管理。docs/03-backend-spec.md 3章に対応。"""
import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

SESSION_LIFETIME = timedelta(hours=8)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, hex_digest = hashed.split(":", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return secrets.compare_digest(digest.hex(), hex_digest)


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    session_id = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires = now + SESSION_LIFETIME
    conn.execute(
        "INSERT INTO sessions (session_id, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (session_id, user_id, now.isoformat(), expires.isoformat()),
    )
    conn.commit()
    return session_id


def get_session_user(conn: sqlite3.Connection, session_id: str):
    row = conn.execute(
        "SELECT s.expires_at, u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        return None
    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        delete_session(conn, session_id)
        return None
    return row


def delete_session(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
