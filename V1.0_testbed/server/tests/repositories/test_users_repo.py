import sqlite3

import pytest

from app.repositories.users import (
    create_user,
    deactivate_user,
    get_user_by_employee_id,
    get_user_by_id,
    list_users,
    update_user,
)


def test_get_user_by_employee_id_returns_correct_role(db_conn):
    admin = get_user_by_employee_id(db_conn, "admin001")
    assert admin is not None
    assert admin.role == "admin"
    assert admin.is_admin is True

    general = get_user_by_employee_id(db_conn, "user001")
    assert general is not None
    assert general.role == "general"
    assert general.is_admin is False


def test_get_user_by_employee_id_unknown_returns_none(db_conn):
    assert get_user_by_employee_id(db_conn, "no_such_user") is None


def test_get_user_by_id_round_trip(db_conn):
    admin = get_user_by_employee_id(db_conn, "admin001")
    fetched = get_user_by_id(db_conn, admin.id)
    assert fetched is not None
    assert fetched.employee_id == "admin001"


def test_create_user_appears_in_list_users(db_conn):
    user_id = create_user(
        db_conn,
        employee_id="user003",
        name="新人太郎",
        password_hash="hashed",
        role="general",
        is_active=True,
        created_at="2026-08-11T00:00:00+00:00",
    )

    users = list_users(db_conn)
    assert user_id in [u.id for u in users]


def test_create_user_duplicate_employee_id_raises_integrity_error(db_conn):
    create_user(
        db_conn, employee_id="user003", name="新人太郎", password_hash="hashed", role="general",
        is_active=True, created_at="2026-08-11T00:00:00+00:00",
    )
    with pytest.raises(sqlite3.IntegrityError):
        create_user(
            db_conn, employee_id="user003", name="別の人", password_hash="hashed2", role="general",
            is_active=True, created_at="2026-08-11T00:00:00+00:00",
        )


def test_update_user_changes_fields(db_conn):
    user_id = create_user(
        db_conn, employee_id="user003", name="新人太郎", password_hash="hashed", role="general",
        is_active=True, created_at="2026-08-11T00:00:00+00:00",
    )

    update_user(db_conn, user_id, name="改名太郎", role="admin", is_active=True, updated_at="2026-08-11T01:00:00+00:00")

    updated = get_user_by_id(db_conn, user_id)
    assert updated.name == "改名太郎"
    assert updated.role == "admin"


def test_deactivate_user_sets_inactive_but_keeps_row(db_conn):
    user_id = create_user(
        db_conn, employee_id="user003", name="新人太郎", password_hash="hashed", role="general",
        is_active=True, created_at="2026-08-11T00:00:00+00:00",
    )

    deactivate_user(db_conn, user_id, updated_at="2026-08-11T01:00:00+00:00")

    fetched = get_user_by_id(db_conn, user_id)
    assert fetched is not None
    assert fetched.is_active is False
