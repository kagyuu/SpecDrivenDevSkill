"""Unit tests for U003-T1 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md).

Target: app/repositories/reservation_repository.py

U004-T1 appends tests for find_by_id/update/delete/
find_by_organizer_or_participant/replace_participants at the end of this
file, per that task's own 作成・編集対象ファイル ("test_reservation_repository.py
(追加テスト)").
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from app.db.migration import apply_pending_migrations
from app.repositories import reservation_repository, room_repository


def _fresh_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    apply_pending_migrations(conn)
    return conn


@pytest.fixture()
def conn() -> sqlite3.Connection:
    return _fresh_connection()


@pytest.fixture()
def room_id(conn: sqlite3.Connection) -> int:
    room = room_repository.create(conn, "会議室A", 8, [], None)
    return room["room_id"]


def _create(
    conn: sqlite3.Connection,
    room_id: int,
    start: str,
    end: str,
    organizer_user_id: str = "admin",
    title: str = "定例会議",
) -> int:
    with reservation_repository.begin_immediate_transaction(conn):
        reservation_repository.create(
            conn, room_id, organizer_user_id, title, start, end, None, None, []
        )
    row = conn.execute(
        "SELECT reservation_id FROM reservations ORDER BY reservation_id DESC LIMIT 1"
    ).fetchone()
    return row["reservation_id"]


def test_create_with_no_overlap_succeeds(conn: sqlite3.Connection, room_id: int):
    reservation_id = _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")

    assert reservation_id is not None
    assert reservation_repository.find_overlapping(
        conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00"
    ) == [reservation_id]


def test_adjacent_reservations_sharing_an_endpoint_do_not_overlap(
    conn: sqlite3.Connection, room_id: int
):
    _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")

    # New reservation starts exactly when the existing one ends - touching,
    # not overlapping (docs/P003-backend-spec.md uses a strict inequality).
    overlapping = reservation_repository.find_overlapping(
        conn, room_id, "2026-08-10T11:00:00", "2026-08-10T12:00:00"
    )
    assert overlapping == []


@pytest.mark.parametrize(
    ("new_start", "new_end"),
    [
        ("2026-08-10T10:00:00", "2026-08-10T11:00:00"),  # exact match
        ("2026-08-10T09:30:00", "2026-08-10T10:30:00"),  # overlaps the front
        ("2026-08-10T10:30:00", "2026-08-10T11:30:00"),  # overlaps the back
        ("2026-08-10T09:00:00", "2026-08-10T12:00:00"),  # encloses the existing one
        ("2026-08-10T10:15:00", "2026-08-10T10:45:00"),  # contained within it
    ],
)
def test_overlapping_time_ranges_are_detected(
    conn: sqlite3.Connection, room_id: int, new_start: str, new_end: str
):
    existing_id = _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")

    overlapping = reservation_repository.find_overlapping(conn, room_id, new_start, new_end)

    assert overlapping == [existing_id]


def test_find_overlapping_excludes_given_reservation_id(conn: sqlite3.Connection, room_id: int):
    reservation_id = _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")

    overlapping = reservation_repository.find_overlapping(
        conn,
        room_id,
        "2026-08-10T10:00:00",
        "2026-08-10T11:00:00",
        exclude_reservation_id=reservation_id,
    )

    assert overlapping == []


def test_find_by_range_joins_room_and_organizer_names(conn: sqlite3.Connection, room_id: int):
    _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00", title="全体会議")

    results = reservation_repository.find_by_range(conn, "2026-08-10", "2026-08-10")

    assert len(results) == 1
    assert results[0]["room_name"] == "会議室A"
    assert results[0]["organizer_name"] == "システム管理者"
    assert results[0]["title"] == "全体会議"


def test_find_by_range_filters_by_room_ids(conn: sqlite3.Connection, room_id: int):
    other_room_id = room_repository.create(conn, "会議室B", 4, [], None)["room_id"]
    _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")
    _create(conn, other_room_id, "2026-08-10T13:00:00", "2026-08-10T14:00:00")

    results = reservation_repository.find_by_range(conn, "2026-08-10", "2026-08-10", [room_id])

    assert [r["room_id"] for r in results] == [room_id]


def test_concurrent_create_for_the_same_slot_never_double_books(tmp_path: Path):
    """同時実行テスト(重要): 2つのDBコネクションからほぼ同時に create を試みても、
    BEGIN IMMEDIATE による排他制御の結果 reservations テーブルに該当時間帯の行が
    1件しか残らないことを確認する(docs/P007-impl-direction/U003-reservation-core-and-calendar.md
    U003-T1 の完了条件)。

    Uses a real on-disk DB (not ":memory:") - each ":memory:" connection is
    an independent database, so it could never exhibit the SQLite
    file-locking behaviour being tested here.
    """
    db_path = tmp_path / "concurrency.db"
    setup_conn = sqlite3.connect(str(db_path))
    setup_conn.row_factory = sqlite3.Row
    apply_pending_migrations(setup_conn)
    room = room_repository.create(setup_conn, "会議室C", 8, [], None)
    room_id_value = room["room_id"]
    setup_conn.close()

    start, end = "2026-08-10T10:00:00", "2026-08-10T11:00:00"
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()

    def attempt() -> None:
        thread_conn = sqlite3.connect(str(db_path), timeout=10)
        thread_conn.row_factory = sqlite3.Row
        thread_conn.execute("PRAGMA foreign_keys = ON")
        try:
            barrier.wait()  # maximize the chance both threads race for the lock
            with reservation_repository.begin_immediate_transaction(thread_conn):
                overlapping = reservation_repository.find_overlapping(
                    thread_conn, room_id_value, start, end
                )
                if overlapping:
                    # Mirrors what U003-T2's Service layer will do with the
                    # real ReservationConflictError - this Repository-layer
                    # test only needs to prove the *primitives* make this
                    # possible, per this task's own scope boundary.
                    raise RuntimeError("conflict detected")
                reservation_repository.create(
                    thread_conn, room_id_value, "admin", "競合テスト", start, end, None, None, []
                )
            with outcomes_lock:
                outcomes.append("success")
        except Exception:
            with outcomes_lock:
                outcomes.append("failed")
        finally:
            thread_conn.close()

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)

    assert outcomes.count("success") == 1
    assert outcomes.count("failed") == 1

    verify_conn = sqlite3.connect(str(db_path))
    count = verify_conn.execute(
        "SELECT COUNT(*) AS n FROM reservations WHERE room_id = ?", (room_id_value,)
    ).fetchone()[0]
    verify_conn.close()
    assert count == 1


# --- U004-T1 additions ---------------------------------------------------


def test_find_by_id_returns_detail_with_participants(conn: sqlite3.Connection, room_id: int):
    reservation_id = _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")
    reservation_repository.add_participants(conn, reservation_id, ["admin"])

    detail = reservation_repository.find_by_id(conn, reservation_id)

    assert detail is not None
    assert detail["room_name"] == "会議室A"
    assert detail["organizer_name"] == "システム管理者"
    assert detail["participants"] == [{"employee_id": "admin", "name": "システム管理者"}]


def test_find_by_id_returns_none_for_missing_reservation(conn: sqlite3.Connection):
    assert reservation_repository.find_by_id(conn, 9999) is None


def test_update_changes_reservation_fields(conn: sqlite3.Connection, room_id: int):
    reservation_id = _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")

    updated = reservation_repository.update(
        conn, reservation_id, room_id, "変更後タイトル", "2026-08-10T13:00:00", "2026-08-10T14:00:00", 5, "メモ"
    )

    assert updated is True
    detail = reservation_repository.find_by_id(conn, reservation_id)
    assert detail["title"] == "変更後タイトル"
    assert detail["start_datetime"] == "2026-08-10T13:00:00"
    assert detail["attendee_count"] == 5


def test_update_nonexistent_reservation_returns_false(conn: sqlite3.Connection, room_id: int):
    updated = reservation_repository.update(
        conn, 9999, room_id, "x", "2026-08-10T10:00:00", "2026-08-10T11:00:00", None, None
    )

    assert updated is False


def test_replace_participants_removes_old_and_inserts_new(conn: sqlite3.Connection, room_id: int):
    reservation_id = _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")
    reservation_repository.add_participants(conn, reservation_id, ["admin"])

    reservation_repository.replace_participants(conn, reservation_id, [])

    assert reservation_repository.find_participants(conn, reservation_id) == []


def test_delete_removes_reservation_and_its_participants(conn: sqlite3.Connection, room_id: int):
    reservation_id = _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")
    reservation_repository.add_participants(conn, reservation_id, ["admin"])

    deleted = reservation_repository.delete(conn, reservation_id)

    assert deleted is True
    assert reservation_repository.find_by_id(conn, reservation_id) is None
    assert reservation_repository.find_participants(conn, reservation_id) == []


def test_delete_nonexistent_reservation_returns_false(conn: sqlite3.Connection):
    assert reservation_repository.delete(conn, 9999) is False


def test_find_by_organizer_or_participant_includes_both_roles(conn: sqlite3.Connection, room_id: int):
    organizer_reservation_id = _create(
        conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00", organizer_user_id="admin"
    )
    # A second reservation organized by someone else, but "admin" participates in it.
    other_room_id = room_repository.create(conn, "会議室B", 4, [], None)["room_id"]
    with reservation_repository.begin_immediate_transaction(conn):
        reservation_repository.create(
            conn, other_room_id, "admin", "他人主催", "2026-08-12T09:00:00", "2026-08-12T10:00:00", None, None, []
        )
    participant_reservation_id = conn.execute(
        "SELECT reservation_id FROM reservations WHERE title = '他人主催'"
    ).fetchone()["reservation_id"]
    # Re-seed as organized by a different user, with admin only as participant.
    conn.execute(
        "INSERT INTO users (user_id, name, password_hash, role, is_active, created_at, updated_at) "
        "VALUES ('other-organizer', '他人', 'x', 'general', 1, datetime('now'), datetime('now'))"
    )
    conn.execute(
        "UPDATE reservations SET organizer_user_id = 'other-organizer' WHERE reservation_id = ?",
        (participant_reservation_id,),
    )
    reservation_repository.add_participants(conn, participant_reservation_id, ["admin"])
    conn.commit()

    results = reservation_repository.find_by_organizer_or_participant(conn, "admin", period="all")

    ids = {row["reservation_id"] for row in results}
    assert ids == {organizer_reservation_id, participant_reservation_id}


def test_find_by_organizer_or_participant_filters_by_period(conn: sqlite3.Connection, room_id: int):
    past_id = _create(conn, room_id, "2020-01-01T10:00:00", "2020-01-01T11:00:00", title="過去の予約")
    future_id = _create(conn, room_id, "2099-01-01T10:00:00", "2099-01-01T11:00:00", title="未来の予約")

    upcoming = reservation_repository.find_by_organizer_or_participant(conn, "admin", period="upcoming")
    past = reservation_repository.find_by_organizer_or_participant(conn, "admin", period="past")
    everything = reservation_repository.find_by_organizer_or_participant(conn, "admin", period="all")

    assert [row["reservation_id"] for row in upcoming] == [future_id]
    assert [row["reservation_id"] for row in past] == [past_id]
    assert {row["reservation_id"] for row in everything} == {past_id, future_id}


# --- U003-T7/U004-T6 additions (CR-001: docs/P901-cr-direction/CR-001.md) ---


def test_create_stores_meeting_url(conn: sqlite3.Connection, room_id: int):
    with reservation_repository.begin_immediate_transaction(conn):
        reservation_repository.create(
            conn,
            room_id,
            "admin",
            "オンライン会議",
            "2026-08-10T10:00:00",
            "2026-08-10T11:00:00",
            None,
            None,
            [],
            "https://example.com/meeting/123",
        )
    row = conn.execute(
        "SELECT reservation_id FROM reservations ORDER BY reservation_id DESC LIMIT 1"
    ).fetchone()

    detail = reservation_repository.find_by_id(conn, row["reservation_id"])

    assert detail["meeting_url"] == "https://example.com/meeting/123"


def test_create_without_meeting_url_stores_none(conn: sqlite3.Connection, room_id: int):
    reservation_id = _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")

    detail = reservation_repository.find_by_id(conn, reservation_id)

    assert detail["meeting_url"] is None


def test_update_changes_meeting_url(conn: sqlite3.Connection, room_id: int):
    reservation_id = _create(conn, room_id, "2026-08-10T10:00:00", "2026-08-10T11:00:00")

    reservation_repository.update(
        conn,
        reservation_id,
        room_id,
        "定例会議",
        "2026-08-10T10:00:00",
        "2026-08-10T11:00:00",
        None,
        None,
        "https://example.com/meeting/updated",
    )

    detail = reservation_repository.find_by_id(conn, reservation_id)
    assert detail["meeting_url"] == "https://example.com/meeting/updated"


def test_update_with_none_clears_meeting_url(conn: sqlite3.Connection, room_id: int):
    with reservation_repository.begin_immediate_transaction(conn):
        reservation_repository.create(
            conn,
            room_id,
            "admin",
            "オンライン会議",
            "2026-08-10T10:00:00",
            "2026-08-10T11:00:00",
            None,
            None,
            [],
            "https://example.com/meeting/123",
        )
    reservation_id = conn.execute(
        "SELECT reservation_id FROM reservations ORDER BY reservation_id DESC LIMIT 1"
    ).fetchone()["reservation_id"]

    reservation_repository.update(
        conn,
        reservation_id,
        room_id,
        "定例会議",
        "2026-08-10T10:00:00",
        "2026-08-10T11:00:00",
        None,
        None,
        None,
    )

    detail = reservation_repository.find_by_id(conn, reservation_id)
    assert detail["meeting_url"] is None


def test_find_by_range_does_not_include_meeting_url(conn: sqlite3.Connection, room_id: int):
    """docs/P002-frontend-spec.md 4.6節: 一覧レスポンスは意図的にmeeting_urlを
    含めない(CR-001)。回帰防止。"""
    with reservation_repository.begin_immediate_transaction(conn):
        reservation_repository.create(
            conn,
            room_id,
            "admin",
            "オンライン会議",
            "2026-08-10T10:00:00",
            "2026-08-10T11:00:00",
            None,
            None,
            [],
            "https://example.com/meeting/123",
        )

    results = reservation_repository.find_by_range(conn, "2026-08-10", "2026-08-10")

    assert len(results) == 1
    assert "meeting_url" not in results[0]
