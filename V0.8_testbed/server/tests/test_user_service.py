"""Unit tests for U005-T1 (docs/P007-impl-direction/U005-user-management-and-hardening.md).

Target: app/services/user_service.py
"""

from __future__ import annotations

import sqlite3

import pytest

from app.db.migration import apply_pending_migrations
from app.exceptions import LastAdminProtectedError, SelfDeactivationForbiddenError, ValidationError
from app.security.password import verify_password
from app.services import auth_service, user_service


@pytest.fixture()
def conn() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    apply_pending_migrations(connection)
    return connection


def test_create_user_succeeds(conn: sqlite3.Connection):
    user = user_service.create(conn, "u001", "一般 太郎", "Password1!", "general")

    assert user["user_id"] == "u001"
    assert user["role"] == "general"
    assert verify_password("Password1!", user["password_hash"]) is True


def test_list_users_returns_created_user(conn: sqlite3.Connection):
    user_service.create(conn, "u001", "一般 太郎", "Password1!", "general")

    users = user_service.list_users(conn)

    assert any(u["user_id"] == "u001" for u in users)


def test_update_user_without_password_keeps_existing_hash(conn: sqlite3.Connection):
    created = user_service.create(conn, "u001", "一般 太郎", "Password1!", "general")

    updated = user_service.update(conn, "u001", "一般 次郎", None, "general", True, "admin")

    assert updated["name"] == "一般 次郎"
    assert updated["password_hash"] == created["password_hash"]


def test_deactivate_user_succeeds_and_removes_sessions(conn: sqlite3.Connection):
    user_service.create(conn, "u001", "一般 太郎", "Password1!", "general")
    session = auth_service.login(conn, "u001", "Password1!")

    deactivated = user_service.deactivate(conn, "u001", "admin")

    assert deactivated["is_active"] == 0
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM sessions WHERE session_id = ?", (session["session_id"],)
    ).fetchone()
    assert row["n"] == 0


def test_create_with_duplicate_employee_id_raises_validation_error(conn: sqlite3.Connection):
    user_service.create(conn, "u001", "一般 太郎", "Password1!", "general")

    with pytest.raises(ValidationError) as excinfo:
        user_service.create(conn, "u001", "別 太郎", "Password1!", "general")

    assert "employee_id" in excinfo.value.fields


def test_create_with_invalid_employee_id_format_raises_validation_error(conn: sqlite3.Connection):
    with pytest.raises(ValidationError) as excinfo:
        user_service.create(conn, "ab", "太郎", "Password1!", "general")

    assert "employee_id" in excinfo.value.fields


def test_create_with_short_password_raises_validation_error(conn: sqlite3.Connection):
    with pytest.raises(ValidationError) as excinfo:
        user_service.create(conn, "u002", "太郎", "short1", "general")

    assert "password" in excinfo.value.fields


def test_self_deactivation_raises_forbidden(conn: sqlite3.Connection):
    with pytest.raises(SelfDeactivationForbiddenError):
        user_service.update(conn, "admin", "システム管理者", None, "admin", False, "admin")


def test_deactivating_last_active_admin_raises_last_admin_protected(conn: sqlite3.Connection):
    with pytest.raises(LastAdminProtectedError):
        user_service.update(conn, "admin", "システム管理者", None, "admin", False, "some-other-user")


def test_deactivating_one_of_two_admins_succeeds(conn: sqlite3.Connection):
    user_service.create(conn, "admin2", "管理者2", "Password1!", "admin")

    deactivated = user_service.update(
        conn, "admin2", "管理者2", None, "admin", False, "admin"
    )

    assert deactivated["is_active"] == 0
    # The remaining admin ("admin") is still active - protection did not
    # (incorrectly) block this because two admins existed before the call.
    remaining = conn.execute(
        "SELECT COUNT(*) AS n FROM users WHERE role = 'admin' AND is_active = 1"
    ).fetchone()
    assert remaining["n"] == 1
