"""Unit tests for U003-T2 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md).

Target: app/services/reservation_service.py

U004-T1 appends tests for get_reservation/update_reservation/
cancel_reservation/list_my_reservations at the end of this file, per that
task's own 作成・編集対象ファイル ("test_reservation_service.py(追加テスト)").
"""

from __future__ import annotations

import sqlite3

import pytest

from app.db.migration import apply_pending_migrations
from app.exceptions import ForbiddenError, NotFoundError, ReservationConflictError, ValidationError
from app.repositories import room_repository
from app.services import reservation_service


@pytest.fixture()
def conn() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    apply_pending_migrations(connection)
    return connection


@pytest.fixture()
def room_id(conn: sqlite3.Connection) -> int:
    return room_repository.create(conn, "会議室A", 4, [], None)["room_id"]


@pytest.fixture()
def general_user_id(conn: sqlite3.Connection) -> str:
    conn.execute(
        "INSERT INTO users (user_id, name, password_hash, role, is_active, created_at, updated_at) "
        "VALUES ('u001', '一般 太郎', 'x', 'general', 1, datetime('now'), datetime('now'))"
    )
    conn.commit()
    return "u001"


@pytest.fixture()
def second_admin_id(conn: sqlite3.Connection) -> str:
    conn.execute(
        "INSERT INTO users (user_id, name, password_hash, role, is_active, created_at, updated_at) "
        "VALUES ('admin2', '管理者2', 'x', 'admin', 1, datetime('now'), datetime('now'))"
    )
    conn.commit()
    return "admin2"


def test_create_reservation_succeeds(conn: sqlite3.Connection, room_id: int):
    result = reservation_service.create_reservation(
        conn,
        room_id,
        "2026-08-10",
        "10:00",
        "11:00",
        "定例会議",
        [],
        3,
        "資料持参",
        "admin",
    )

    assert result["room_id"] == room_id
    assert result["organizer_user_id"] == "admin"
    assert result["organizer_name"] == "システム管理者"
    assert result["editable"] is True
    assert result["attendee_count"] == 3


def test_list_reservations_returns_created_reservation(conn: sqlite3.Connection, room_id: int):
    reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    results = reservation_service.list_reservations(conn, "2026-08-10", "2026-08-10")

    assert len(results) == 1
    assert results[0]["title"] == "定例会議"


def test_list_participant_candidates_returns_active_users(conn: sqlite3.Connection):
    candidates = reservation_service.list_participant_candidates(conn)

    assert {"employee_id": "admin", "name": "システム管理者"} in candidates


def test_create_reservation_with_blank_title_raises_validation_error(
    conn: sqlite3.Connection, room_id: int
):
    with pytest.raises(ValidationError) as excinfo:
        reservation_service.create_reservation(
            conn, room_id, "2026-08-10", "10:00", "11:00", "", [], None, None, "admin"
        )
    assert "title" in excinfo.value.fields


def test_create_reservation_with_101_char_title_raises_validation_error(
    conn: sqlite3.Connection, room_id: int
):
    with pytest.raises(ValidationError) as excinfo:
        reservation_service.create_reservation(
            conn, room_id, "2026-08-10", "10:00", "11:00", "x" * 101, [], None, None, "admin"
        )
    assert "title" in excinfo.value.fields


def test_create_reservation_with_end_before_start_raises_validation_error(
    conn: sqlite3.Connection, room_id: int
):
    with pytest.raises(ValidationError) as excinfo:
        reservation_service.create_reservation(
            conn, room_id, "2026-08-10", "11:00", "10:00", "件名", [], None, None, "admin"
        )
    assert "end_time" in excinfo.value.fields


def test_create_reservation_exceeding_capacity_raises_validation_error(
    conn: sqlite3.Connection, room_id: int
):
    with pytest.raises(ValidationError) as excinfo:
        reservation_service.create_reservation(
            conn, room_id, "2026-08-10", "10:00", "11:00", "件名", [], 5, None, "admin"
        )
    assert "attendee_count" in excinfo.value.fields
    assert "4名" in excinfo.value.fields["attendee_count"]


def test_create_reservation_with_nonexistent_room_raises_not_found(conn: sqlite3.Connection):
    with pytest.raises(NotFoundError):
        reservation_service.create_reservation(
            conn, 9999, "2026-08-10", "10:00", "11:00", "件名", [], None, None, "admin"
        )


def test_create_reservation_for_inactive_room_raises_not_found(
    conn: sqlite3.Connection, room_id: int
):
    room_repository.deactivate(conn, room_id)

    with pytest.raises(NotFoundError):
        reservation_service.create_reservation(
            conn, room_id, "2026-08-10", "10:00", "11:00", "件名", [], None, None, "admin"
        )


def test_create_reservation_with_overlapping_time_raises_conflict(
    conn: sqlite3.Connection, room_id: int
):
    reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "既存予約", [], None, None, "admin"
    )

    with pytest.raises(ReservationConflictError):
        reservation_service.create_reservation(
            conn, room_id, "2026-08-10", "10:30", "11:30", "新規予約", [], None, None, "admin"
        )


# --- U004-T1 additions ---------------------------------------------------


def test_get_reservation_is_editable_for_organizer(conn: sqlite3.Connection, room_id: int):
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    detail = reservation_service.get_reservation(conn, created["reservation_id"], "admin")

    assert detail["editable"] is True
    assert detail["title"] == "定例会議"


def test_get_reservation_is_read_only_for_unrelated_general_user(
    conn: sqlite3.Connection, room_id: int, general_user_id: str
):
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    detail = reservation_service.get_reservation(conn, created["reservation_id"], general_user_id)

    assert detail["editable"] is False


def test_get_reservation_is_editable_for_admin_even_if_not_organizer(
    conn: sqlite3.Connection, room_id: int, second_admin_id: str
):
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    detail = reservation_service.get_reservation(conn, created["reservation_id"], second_admin_id)

    assert detail["editable"] is True


def test_get_reservation_raises_not_found_for_missing_id(conn: sqlite3.Connection):
    with pytest.raises(NotFoundError):
        reservation_service.get_reservation(conn, 9999, "admin")


def test_update_reservation_by_organizer_succeeds(conn: sqlite3.Connection, room_id: int):
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    updated = reservation_service.update_reservation(
        conn, created["reservation_id"], room_id, "2026-08-10", "13:00", "14:00", "変更後", [], None, None, "admin"
    )

    assert updated["title"] == "変更後"
    assert updated["start_time"] == "13:00"


def test_update_reservation_by_unrelated_user_raises_forbidden(
    conn: sqlite3.Connection, room_id: int, general_user_id: str
):
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    with pytest.raises(ForbiddenError):
        reservation_service.update_reservation(
            conn,
            created["reservation_id"],
            room_id,
            "2026-08-10",
            "13:00",
            "14:00",
            "変更後",
            [],
            None,
            None,
            general_user_id,
        )


def test_update_reservation_to_same_slot_it_already_occupies_does_not_conflict(
    conn: sqlite3.Connection, room_id: int
):
    """docs/P007-impl-direction/U004-reservation-detail-and-mylist.md U004-T1
    の異常系項目: 「自分自身の予約を同じ時間帯に更新しても重複エラーにならない
    こと(除外ロジックの確認)」。"""
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    updated = reservation_service.update_reservation(
        conn,
        created["reservation_id"],
        room_id,
        "2026-08-10",
        "10:00",
        "11:00",
        "定例会議(更新)",
        [],
        None,
        None,
        "admin",
    )

    assert updated["title"] == "定例会議(更新)"


def test_update_nonexistent_reservation_raises_not_found(conn: sqlite3.Connection, room_id: int):
    with pytest.raises(NotFoundError):
        reservation_service.update_reservation(
            conn, 9999, room_id, "2026-08-10", "10:00", "11:00", "x", [], None, None, "admin"
        )


def test_cancel_reservation_by_organizer_removes_it(conn: sqlite3.Connection, room_id: int):
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    reservation_service.cancel_reservation(conn, created["reservation_id"], "admin")

    with pytest.raises(NotFoundError):
        reservation_service.get_reservation(conn, created["reservation_id"], "admin")


def test_cancel_reservation_by_unrelated_user_raises_forbidden(
    conn: sqlite3.Connection, room_id: int, general_user_id: str
):
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    with pytest.raises(ForbiddenError):
        reservation_service.cancel_reservation(conn, created["reservation_id"], general_user_id)


def test_cancel_nonexistent_reservation_raises_not_found(conn: sqlite3.Connection):
    with pytest.raises(NotFoundError):
        reservation_service.cancel_reservation(conn, 9999, "admin")


def test_list_my_reservations_filters_by_period(conn: sqlite3.Connection, room_id: int):
    reservation_service.create_reservation(
        conn, room_id, "2020-01-01", "10:00", "11:00", "過去の予約", [], None, None, "admin"
    )
    reservation_service.create_reservation(
        conn, room_id, "2099-01-01", "10:00", "11:00", "未来の予約", [], None, None, "admin"
    )

    upcoming = reservation_service.list_my_reservations(conn, "admin", "upcoming")
    past = reservation_service.list_my_reservations(conn, "admin", "past")
    everything = reservation_service.list_my_reservations(conn, "admin", "all")

    assert [item["title"] for item in upcoming] == ["未来の予約"]
    assert [item["title"] for item in past] == ["過去の予約"]
    assert len(everything) == 2


# --- U003-T7/U004-T6 additions (CR-001: docs/P901-cr-direction/CR-001.md) ---


def test_create_reservation_with_valid_meeting_url_succeeds(conn: sqlite3.Connection, room_id: int):
    result = reservation_service.create_reservation(
        conn,
        room_id,
        "2026-08-10",
        "10:00",
        "11:00",
        "定例会議",
        [],
        None,
        None,
        "admin",
        "https://example.com/meeting/123",
    )

    assert result["meeting_url"] == "https://example.com/meeting/123"


def test_create_reservation_without_meeting_url_stores_none(conn: sqlite3.Connection, room_id: int):
    result = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    assert result["meeting_url"] is None


def test_create_reservation_with_empty_string_meeting_url_stores_none(
    conn: sqlite3.Connection, room_id: int
):
    result = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin", ""
    )

    assert result["meeting_url"] is None


def test_create_reservation_with_exactly_500_char_meeting_url_succeeds(
    conn: sqlite3.Connection, room_id: int
):
    url = "https://example.com/" + "a" * (500 - len("https://example.com/"))
    assert len(url) == 500

    result = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin", url
    )

    assert result["meeting_url"] == url


@pytest.mark.parametrize(
    "meeting_url",
    [
        "ftp://example.com/meeting",
        "example.com/meeting",  # スキームなし
    ],
)
def test_create_reservation_with_invalid_scheme_raises_validation_error(
    conn: sqlite3.Connection, room_id: int, meeting_url: str
):
    with pytest.raises(ValidationError) as excinfo:
        reservation_service.create_reservation(
            conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin", meeting_url
        )
    assert "meeting_url" in excinfo.value.fields


def test_create_reservation_with_501_char_meeting_url_raises_validation_error(
    conn: sqlite3.Connection, room_id: int
):
    url = "https://example.com/" + "a" * (501 - len("https://example.com/"))
    assert len(url) == 501

    with pytest.raises(ValidationError) as excinfo:
        reservation_service.create_reservation(
            conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin", url
        )
    assert "meeting_url" in excinfo.value.fields


def test_get_reservation_includes_meeting_url(conn: sqlite3.Connection, room_id: int):
    created = reservation_service.create_reservation(
        conn,
        room_id,
        "2026-08-10",
        "10:00",
        "11:00",
        "定例会議",
        [],
        None,
        None,
        "admin",
        "https://example.com/meeting/123",
    )

    detail = reservation_service.get_reservation(conn, created["reservation_id"], "admin")

    assert detail["meeting_url"] == "https://example.com/meeting/123"


def test_update_reservation_changes_meeting_url(conn: sqlite3.Connection, room_id: int):
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    updated = reservation_service.update_reservation(
        conn,
        created["reservation_id"],
        room_id,
        "2026-08-10",
        "10:00",
        "11:00",
        "定例会議",
        [],
        None,
        None,
        "admin",
        "https://example.com/meeting/updated",
    )

    assert updated["meeting_url"] == "https://example.com/meeting/updated"


def test_update_reservation_with_empty_string_clears_meeting_url(
    conn: sqlite3.Connection, room_id: int
):
    created = reservation_service.create_reservation(
        conn,
        room_id,
        "2026-08-10",
        "10:00",
        "11:00",
        "定例会議",
        [],
        None,
        None,
        "admin",
        "https://example.com/meeting/123",
    )

    updated = reservation_service.update_reservation(
        conn,
        created["reservation_id"],
        room_id,
        "2026-08-10",
        "10:00",
        "11:00",
        "定例会議",
        [],
        None,
        None,
        "admin",
        "",
    )

    assert updated["meeting_url"] is None


def test_update_reservation_with_invalid_meeting_url_raises_validation_error(
    conn: sqlite3.Connection, room_id: int
):
    created = reservation_service.create_reservation(
        conn, room_id, "2026-08-10", "10:00", "11:00", "定例会議", [], None, None, "admin"
    )

    with pytest.raises(ValidationError) as excinfo:
        reservation_service.update_reservation(
            conn,
            created["reservation_id"],
            room_id,
            "2026-08-10",
            "10:00",
            "11:00",
            "定例会議",
            [],
            None,
            None,
            "admin",
            "ftp://example.com/meeting",
        )
    assert "meeting_url" in excinfo.value.fields
