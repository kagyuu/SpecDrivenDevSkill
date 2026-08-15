from datetime import datetime

from app.repositories.reservations import (
    create_reservation,
    delete_reservation,
    find_conflicting,
    get_by_id,
    list_by_range,
    list_by_user,
    update_reservation,
)
from app.repositories.users import get_user_by_employee_id


def _insert_room(conn, name="会議室A", capacity=10):
    cursor = conn.execute(
        """
        INSERT INTO rooms (name, capacity, equipment_json, description, is_active, created_at, updated_at)
        VALUES (?, ?, '[]', NULL, 1, '2026-08-11T00:00:00+00:00', '2026-08-11T00:00:00+00:00')
        """,
        (name, capacity),
    )
    conn.commit()
    return cursor.lastrowid


def test_create_reservation_then_get_by_id(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")

    reservation_id = create_reservation(
        db_conn,
        room_id=room_id,
        user_id=user.id,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="定例MTG",
        expected_attendees=3,
        notes=None,
        participant_ids=[],
        created_at="2026-08-11T00:00:00+00:00",
    )

    reservation = get_by_id(db_conn, reservation_id)
    assert reservation is not None
    assert reservation.title == "定例MTG"
    assert reservation.room_name == "会議室A"
    assert reservation.user_name == "一般花子"


def test_find_conflicting_detects_overlap_but_not_back_to_back(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")
    create_reservation(
        db_conn,
        room_id=room_id,
        user_id=user.id,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="既存予約",
        expected_attendees=None,
        notes=None,
        participant_ids=[],
        created_at="2026-08-11T00:00:00+00:00",
    )

    overlapping = find_conflicting(db_conn, room_id, "2026-08-12", "10:30", "11:30", exclude_id=None)
    assert len(overlapping) == 1

    back_to_back = find_conflicting(db_conn, room_id, "2026-08-12", "11:00", "12:00", exclude_id=None)
    assert back_to_back == []


def test_find_conflicting_excludes_given_id(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")
    reservation_id = create_reservation(
        db_conn,
        room_id=room_id,
        user_id=user.id,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="既存予約",
        expected_attendees=None,
        notes=None,
        participant_ids=[],
        created_at="2026-08-11T00:00:00+00:00",
    )

    # 自分自身と全く同じ時間帯でも、exclude_idを渡せば重複候補から除外される。
    conflicts = find_conflicting(db_conn, room_id, "2026-08-12", "10:00", "11:00", exclude_id=reservation_id)
    assert conflicts == []


def test_list_by_user_upcoming_and_past(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")

    create_reservation(
        db_conn, room_id=room_id, user_id=user.id, date="2026-08-20", start_time="10:00", end_time="11:00",
        title="未来の予約", expected_attendees=None, notes=None, participant_ids=[], created_at="2026-08-11T00:00:00+00:00",
    )
    create_reservation(
        db_conn, room_id=room_id, user_id=user.id, date="2026-08-01", start_time="10:00", end_time="11:00",
        title="過去の予約", expected_attendees=None, notes=None, participant_ids=[], created_at="2026-08-01T00:00:00+00:00",
    )

    now = datetime.fromisoformat("2026-08-11T09:00:00")

    upcoming = list_by_user(db_conn, user.id, now=now, period="upcoming")
    assert [r.title for r in upcoming] == ["未来の予約"]

    past = list_by_user(db_conn, user.id, now=now, period="past")
    assert [r.title for r in past] == ["過去の予約"]


def test_list_by_range_filters_by_room(db_conn):
    room_a = _insert_room(db_conn, name="会議室A")
    room_b = _insert_room(db_conn, name="会議室B")
    user = get_user_by_employee_id(db_conn, "user001")

    create_reservation(
        db_conn, room_id=room_a, user_id=user.id, date="2026-08-12", start_time="10:00", end_time="11:00",
        title="A会議室予約", expected_attendees=None, notes=None, participant_ids=[], created_at="2026-08-11T00:00:00+00:00",
    )
    create_reservation(
        db_conn, room_id=room_b, user_id=user.id, date="2026-08-12", start_time="10:00", end_time="11:00",
        title="B会議室予約", expected_attendees=None, notes=None, participant_ids=[], created_at="2026-08-11T00:00:00+00:00",
    )

    only_a = list_by_range(db_conn, "2026-08-12", "2026-08-12", room_id=room_a)
    assert [r.title for r in only_a] == ["A会議室予約"]

    both = list_by_range(db_conn, "2026-08-12", "2026-08-12", room_id=None)
    assert len(both) == 2


def test_update_reservation_changes_fields(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")
    reservation_id = create_reservation(
        db_conn, room_id=room_id, user_id=user.id, date="2026-08-12", start_time="10:00", end_time="11:00",
        title="旧件名", expected_attendees=None, notes=None, participant_ids=[], created_at="2026-08-11T00:00:00+00:00",
    )

    update_reservation(
        db_conn, reservation_id, room_id=room_id, date="2026-08-12", start_time="10:00", end_time="11:00",
        title="新件名", expected_attendees=5, notes="更新後の備考", participant_ids=[],
        updated_at="2026-08-11T01:00:00+00:00",
    )

    updated = get_by_id(db_conn, reservation_id)
    assert updated.title == "新件名"
    assert updated.expected_attendees == 5
    assert updated.notes == "更新後の備考"


def test_update_reservation_does_not_conflict_with_its_own_unchanged_slot(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")
    reservation_id = create_reservation(
        db_conn, room_id=room_id, user_id=user.id, date="2026-08-12", start_time="10:00", end_time="11:00",
        title="旧件名", expected_attendees=None, notes=None, participant_ids=[], created_at="2026-08-11T00:00:00+00:00",
    )

    # exclude_id に自分自身を渡せば、自分の現在の枠と全く同じ時間帯でも重複としない。
    conflicts = find_conflicting(db_conn, room_id, "2026-08-12", "10:00", "11:00", exclude_id=reservation_id)
    assert conflicts == []


# ※CR-001により追加。Repository層は常に実値を返す(マスキングはRouter層の責務、
# docs/P003-backend-spec.md 「internal_memo のマスキング」参照)。


def test_create_reservation_persists_internal_memo(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")

    reservation_id = create_reservation(
        db_conn,
        room_id=room_id,
        user_id=user.id,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="定例MTG",
        expected_attendees=3,
        notes=None,
        participant_ids=[],
        created_at="2026-08-11T00:00:00+00:00",
        internal_memo="非公開メモ",
    )

    reservation = get_by_id(db_conn, reservation_id)
    assert reservation.internal_memo == "非公開メモ"


def test_create_reservation_without_internal_memo_defaults_to_none(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")

    reservation_id = create_reservation(
        db_conn,
        room_id=room_id,
        user_id=user.id,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="定例MTG",
        expected_attendees=None,
        notes=None,
        participant_ids=[],
        created_at="2026-08-11T00:00:00+00:00",
    )

    reservation = get_by_id(db_conn, reservation_id)
    assert reservation.internal_memo is None


def test_update_reservation_changes_internal_memo(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")
    reservation_id = create_reservation(
        db_conn, room_id=room_id, user_id=user.id, date="2026-08-12", start_time="10:00", end_time="11:00",
        title="旧件名", expected_attendees=None, notes=None, participant_ids=[], created_at="2026-08-11T00:00:00+00:00",
        internal_memo="旧メモ",
    )

    update_reservation(
        db_conn, reservation_id, room_id=room_id, date="2026-08-12", start_time="10:00", end_time="11:00",
        title="新件名", expected_attendees=5, notes="更新後の備考", participant_ids=[],
        updated_at="2026-08-11T01:00:00+00:00", internal_memo="新メモ",
    )

    updated = get_by_id(db_conn, reservation_id)
    assert updated.internal_memo == "新メモ"


def test_delete_reservation_removes_it_and_its_participants(db_conn):
    room_id = _insert_room(db_conn)
    user = get_user_by_employee_id(db_conn, "user001")
    other = get_user_by_employee_id(db_conn, "user002")
    reservation_id = create_reservation(
        db_conn, room_id=room_id, user_id=user.id, date="2026-08-12", start_time="10:00", end_time="11:00",
        title="削除対象", expected_attendees=None, notes=None, participant_ids=[other.id],
        created_at="2026-08-11T00:00:00+00:00",
    )

    delete_reservation(db_conn, reservation_id)

    assert get_by_id(db_conn, reservation_id) is None
    remaining_participants = db_conn.execute(
        "SELECT COUNT(*) FROM reservation_participants WHERE reservation_id = ?", (reservation_id,)
    ).fetchone()[0]
    assert remaining_participants == 0
