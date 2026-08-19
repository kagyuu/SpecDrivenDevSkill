from datetime import datetime

from app.repositories.sessions import (
    create_session,
    delete_session,
    get_session,
    is_session_valid,
)
from app.repositories.users import get_user_by_employee_id


def test_create_and_get_session(db_conn):
    user = get_user_by_employee_id(db_conn, "user001")
    create_session(
        db_conn,
        token="tok-123",
        user_id=user.id,
        created_at="2026-08-11T09:00:00+00:00",
        expires_at="2026-08-11T17:00:00+00:00",
    )

    session = get_session(db_conn, "tok-123")
    assert session is not None
    assert session.user_id == user.id


def test_delete_session_removes_it(db_conn):
    user = get_user_by_employee_id(db_conn, "user001")
    create_session(
        db_conn,
        token="tok-456",
        user_id=user.id,
        created_at="2026-08-11T09:00:00+00:00",
        expires_at="2026-08-11T17:00:00+00:00",
    )

    delete_session(db_conn, "tok-456")

    assert get_session(db_conn, "tok-456") is None


def test_is_session_valid_before_and_after_expiry(db_conn):
    user = get_user_by_employee_id(db_conn, "user001")
    create_session(
        db_conn,
        token="tok-789",
        user_id=user.id,
        created_at="2026-08-11T09:00:00+00:00",
        expires_at="2026-08-11T17:00:00+00:00",
    )
    session = get_session(db_conn, "tok-789")

    before_expiry = datetime.fromisoformat("2026-08-11T10:00:00+00:00")
    after_expiry = datetime.fromisoformat("2026-08-11T18:00:00+00:00")

    assert is_session_valid(session, now=before_expiry) is True
    assert is_session_valid(session, now=after_expiry) is False
