from app.repositories.rooms import (
    create_room,
    deactivate_room,
    get_room_by_id,
    list_active_rooms,
    list_rooms,
    update_room,
)


def _insert_room(conn, name, capacity, is_active):
    cursor = conn.execute(
        """
        INSERT INTO rooms (name, capacity, equipment_json, description, is_active, created_at, updated_at)
        VALUES (?, ?, '[]', NULL, ?, '2026-08-11T00:00:00+00:00', '2026-08-11T00:00:00+00:00')
        """,
        (name, capacity, 1 if is_active else 0),
    )
    conn.commit()
    return cursor.lastrowid


def test_list_active_rooms_excludes_inactive(db_conn):
    _insert_room(db_conn, "会議室A", 10, is_active=True)
    _insert_room(db_conn, "会議室B(無効)", 4, is_active=False)

    rooms = list_active_rooms(db_conn)

    names = [room.name for room in rooms]
    assert "会議室A" in names
    assert "会議室B(無効)" not in names


def test_list_active_rooms_empty_when_none(db_conn):
    assert list_active_rooms(db_conn) == []


def test_get_room_by_id_returns_room_regardless_of_active_state(db_conn):
    # ※U002-T4にもとづき追加(get_room_by_id自体の追加理由はapp/repositories/rooms.py冒頭コメント参照)。
    active_id = _insert_room(db_conn, "会議室A", 10, is_active=True)
    inactive_id = _insert_room(db_conn, "会議室B(無効)", 4, is_active=False)

    active_room = get_room_by_id(db_conn, active_id)
    assert active_room is not None
    assert active_room.is_active is True

    inactive_room = get_room_by_id(db_conn, inactive_id)
    assert inactive_room is not None
    assert inactive_room.is_active is False


def test_get_room_by_id_returns_none_when_missing(db_conn):
    assert get_room_by_id(db_conn, 9999) is None


def test_create_room_then_get(db_conn):
    room_id = create_room(
        db_conn,
        name="会議室C",
        capacity=6,
        equipment=["プロジェクタ"],
        description="窓あり",
        is_active=True,
        created_at="2026-08-11T00:00:00+00:00",
    )

    room = get_room_by_id(db_conn, room_id)
    assert room.name == "会議室C"
    assert room.equipment == ["プロジェクタ"]


def test_update_room_changes_fields(db_conn):
    room_id = create_room(
        db_conn, name="会議室C", capacity=6, equipment=[], description=None, is_active=True,
        created_at="2026-08-11T00:00:00+00:00",
    )

    update_room(
        db_conn, room_id, name="会議室C(改)", capacity=8, equipment=["ホワイトボード"], description="改装後",
        is_active=True, updated_at="2026-08-11T01:00:00+00:00",
    )

    room = get_room_by_id(db_conn, room_id)
    assert room.name == "会議室C(改)"
    assert room.capacity == 8
    assert room.equipment == ["ホワイトボード"]


def test_deactivate_room_sets_inactive_but_keeps_row(db_conn):
    room_id = create_room(
        db_conn, name="会議室D", capacity=4, equipment=[], description=None, is_active=True,
        created_at="2026-08-11T00:00:00+00:00",
    )

    deactivate_room(db_conn, room_id, updated_at="2026-08-11T01:00:00+00:00")

    assert room_id not in [r.id for r in list_active_rooms(db_conn)]
    assert room_id in [r.id for r in list_rooms(db_conn, include_inactive=True)]
    assert get_room_by_id(db_conn, room_id) is not None
