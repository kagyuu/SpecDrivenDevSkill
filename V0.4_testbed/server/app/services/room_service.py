"""会議室Service層 (docs/P003-backend-spec.md §7.5〜§7.7)."""
from __future__ import annotations

import sqlite3

from app.core.exceptions import NotFoundError, ValidationError
from app.core.validators import validate_capacity, validate_room_name
from app.repositories import room_repository


def create(conn: sqlite3.Connection, data: dict) -> sqlite3.Row:
    if not validate_room_name(data.get("name")):
        raise ValidationError("会議室名は1〜50文字で入力してください",
                               details=[{"field": "name", "reason": "invalid length"}])
    if not validate_capacity(data.get("capacity")):
        raise ValidationError("収容人数は1以上の整数で入力してください",
                               details=[{"field": "capacity", "reason": "must be >= 1"}])
    if room_repository.find_by_name_active(conn, data["name"]) is not None:
        raise ValidationError("同名の会議室が既に登録されています",
                               details=[{"field": "name", "reason": "duplicate"}])
    equipment = data.get("equipment") or []
    equipment_str = ",".join(equipment) if isinstance(equipment, list) else str(equipment)
    return room_repository.insert(conn, data["name"], data["capacity"], equipment_str,
                                   data.get("is_active", True))


def update(conn: sqlite3.Connection, room_id: int, data: dict) -> sqlite3.Row:
    existing = room_repository.find(conn, room_id)
    if existing is None:
        raise NotFoundError("会議室が見つかりません")
    if not validate_room_name(data.get("name")):
        raise ValidationError("会議室名は1〜50文字で入力してください",
                               details=[{"field": "name", "reason": "invalid length"}])
    if not validate_capacity(data.get("capacity")):
        raise ValidationError("収容人数は1以上の整数で入力してください",
                               details=[{"field": "capacity", "reason": "must be >= 1"}])
    duplicate = room_repository.find_by_name_active(conn, data["name"])
    if duplicate is not None and duplicate["id"] != room_id:
        raise ValidationError("同名の会議室が既に登録されています",
                               details=[{"field": "name", "reason": "duplicate"}])
    equipment = data.get("equipment") or []
    equipment_str = ",".join(equipment) if isinstance(equipment, list) else str(equipment)
    return room_repository.update(conn, room_id, data["name"], data["capacity"], equipment_str,
                                   data.get("is_active", True))


def deactivate(conn: sqlite3.Connection, room_id: int) -> sqlite3.Row:
    result = room_repository.set_active(conn, room_id, False)
    if result is None:
        raise NotFoundError("会議室が見つかりません")
    return result
