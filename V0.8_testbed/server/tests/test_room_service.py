"""Unit tests for U002-T1 (docs/P007-impl-direction/U002-room-management.md).

Target: app/services/room_service.py
"""

from __future__ import annotations

import sqlite3

import pytest

from app.db.migration import apply_pending_migrations
from app.exceptions import NotFoundError, ValidationError
from app.services import room_service


@pytest.fixture()
def conn() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    apply_pending_migrations(connection)
    return connection


def test_create_and_list_rooms(conn: sqlite3.Connection):
    room = room_service.create(conn, "会議室A", 8, ["プロジェクター"], "3階")

    assert room["room_id"] is not None
    assert room["equipment"] == ["プロジェクター"]
    assert room["is_active"] == 1

    rooms = room_service.list_rooms(conn)
    assert [r["name"] for r in rooms] == ["会議室A"]


def test_list_rooms_excludes_inactive_by_default(conn: sqlite3.Connection):
    room = room_service.create(conn, "会議室B", 4, [], None)
    room_service.deactivate(conn, room["room_id"])

    assert room_service.list_rooms(conn) == []
    assert len(room_service.list_rooms(conn, include_inactive=True)) == 1


def test_update_room(conn: sqlite3.Connection):
    room = room_service.create(conn, "会議室C", 6, [], None)

    updated = room_service.update(
        conn, room["room_id"], "会議室C改", 10, ["ホワイトボード"], "更新後", True
    )

    assert updated["name"] == "会議室C改"
    assert updated["capacity"] == 10
    assert updated["equipment"] == ["ホワイトボード"]


def test_deactivate_room(conn: sqlite3.Connection):
    room = room_service.create(conn, "会議室D", 2, [], None)

    deactivated = room_service.deactivate(conn, room["room_id"])

    assert deactivated["is_active"] == 0


def test_create_with_blank_name_raises_validation_error(conn: sqlite3.Connection):
    with pytest.raises(ValidationError) as excinfo:
        room_service.create(conn, "", 5, [], None)

    assert "name" in excinfo.value.fields


def test_create_with_zero_capacity_raises_validation_error(conn: sqlite3.Connection):
    with pytest.raises(ValidationError) as excinfo:
        room_service.create(conn, "会議室E", 0, [], None)

    assert "capacity" in excinfo.value.fields


def test_create_with_negative_capacity_raises_validation_error(conn: sqlite3.Connection):
    with pytest.raises(ValidationError) as excinfo:
        room_service.create(conn, "会議室F", -1, [], None)

    assert "capacity" in excinfo.value.fields


def test_create_with_201_char_description_raises_validation_error(conn: sqlite3.Connection):
    with pytest.raises(ValidationError) as excinfo:
        room_service.create(conn, "会議室G", 5, [], "x" * 201)

    assert "description" in excinfo.value.fields


def test_update_nonexistent_room_raises_not_found(conn: sqlite3.Connection):
    with pytest.raises(NotFoundError):
        room_service.update(conn, 9999, "名前", 1, [], None, True)


def test_deactivate_nonexistent_room_raises_not_found(conn: sqlite3.Connection):
    with pytest.raises(NotFoundError):
        room_service.deactivate(conn, 9999)
