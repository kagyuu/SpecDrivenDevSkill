"""Unit tests for U001-T3 (docs/P007-impl-direction/U001-foundation-and-auth.md).

Target: app/services/auth_service.py login() / get_current_user() / logout()

Uses an in-memory DB set up via app/db/migration.py (U001-T2, already
implemented and tested) so the seeded admin user (docs/migrations/002_seed_admin.sql,
user_id="admin", password "ChangeMe123!") is available as a real active user
without needing app/repositories/user_repository.py write methods, which do
not exist yet (full user CRUD is U005-T1's job).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from app.db.migration import apply_pending_migrations
from app.services import auth_service
from app.services.auth_service import InvalidCredentialsError, UnauthorizedError


@pytest.fixture()
def conn() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    apply_pending_migrations(connection)
    return connection


def test_login_succeeds_with_correct_credentials(conn: sqlite3.Connection):
    session = auth_service.login(conn, "admin", "ChangeMe123!")

    assert session["user_id"] == "admin"
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM sessions WHERE session_id = ?",
        (session["session_id"],),
    ).fetchone()
    assert row["n"] == 1


def test_login_fails_with_wrong_password(conn: sqlite3.Connection):
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(conn, "admin", "wrong-password")


def test_login_fails_with_unknown_employee_id(conn: sqlite3.Connection):
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(conn, "no-such-user", "ChangeMe123!")


def test_login_fails_for_deactivated_user(conn: sqlite3.Connection):
    # app/repositories/user_repository.py has no write methods yet (U005-T1's
    # job), so deactivate directly via SQL for this test - mirrors how
    # test_migration.py deals with the same not-yet-implemented boundary.
    conn.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", ("admin",))
    conn.commit()

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(conn, "admin", "ChangeMe123!")


def test_get_current_user_returns_user_for_valid_session(conn: sqlite3.Connection):
    session = auth_service.login(conn, "admin", "ChangeMe123!")

    user = auth_service.get_current_user(conn, session["session_id"])

    assert user["user_id"] == "admin"


def test_get_current_user_raises_for_missing_session_id(conn: sqlite3.Connection):
    with pytest.raises(UnauthorizedError):
        auth_service.get_current_user(conn, None)


def test_get_current_user_raises_for_unknown_session_id(conn: sqlite3.Connection):
    with pytest.raises(UnauthorizedError):
        auth_service.get_current_user(conn, "does-not-exist")


def test_get_current_user_raises_for_expired_session(conn: sqlite3.Connection):
    session = auth_service.login(conn, "admin", "ChangeMe123!")
    expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    conn.execute(
        "UPDATE sessions SET expires_at = ? WHERE session_id = ?",
        (expired, session["session_id"]),
    )
    conn.commit()

    with pytest.raises(UnauthorizedError):
        auth_service.get_current_user(conn, session["session_id"])


def test_logout_deletes_session_and_get_current_user_then_fails(
    conn: sqlite3.Connection,
):
    session = auth_service.login(conn, "admin", "ChangeMe123!")

    auth_service.logout(conn, session["session_id"])

    with pytest.raises(UnauthorizedError):
        auth_service.get_current_user(conn, session["session_id"])


def test_logout_is_idempotent_for_unknown_session_id(conn: sqlite3.Connection):
    # Must not raise (docs/P003-backend-spec.md 4.2節 / this task's 実装内容).
    auth_service.logout(conn, "does-not-exist")


def test_logout_is_idempotent_for_none_session_id(conn: sqlite3.Connection):
    auth_service.logout(conn, None)
