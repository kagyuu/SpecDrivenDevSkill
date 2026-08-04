"""予約Service層 (docs/P003-backend-spec.md §4, §7.9〜§7.13).

U003-4: create, list_for_calendar
U004-3: get_detail, list_mine, update, delete, check_editable
U007-1: attendee_count の値域検証・収容人数チェック (CR-003)
"""
from __future__ import annotations

import sqlite3

from app.core.datetime_utils import is_future_or_today
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.validators import (validate_attendee_count, validate_notes, validate_time_range,
                                  validate_title)
from app.repositories import reservation_repository, room_repository, user_repository


def _validate_common(data: dict) -> None:
    if not validate_time_range(data.get("start_time", ""), data.get("end_time", "")):
        raise ValidationError("終了時刻は開始時刻より後である必要があります",
                               details=[{"field": "end_time", "reason": "must be after start_time"}])
    if not validate_title(data.get("title", "")):
        raise ValidationError("件名は1〜100文字で入力してください",
                               details=[{"field": "title", "reason": "invalid length"}])
    if not validate_notes(data.get("notes")):
        raise ValidationError("備考は500文字以内で入力してください",
                               details=[{"field": "notes", "reason": "too long"}])
    if not is_future_or_today(data.get("date", "")):
        raise ValidationError("過去日付は指定できません",
                               details=[{"field": "date", "reason": "must be today or later"}])
    # CR-003: 参加予定人数の値域検証(会議室の収容人数との比較は _check_room_and_participants で行う)
    if not validate_attendee_count(data.get("attendee_count")):
        raise ValidationError("参加予定人数は1以上の整数で入力してください",
                               details=[{"field": "attendee_count", "reason": "must be a positive integer"}])


def _check_room_and_participants(conn: sqlite3.Connection, data: dict) -> None:
    room = room_repository.find(conn, data["room_id"])
    if room is None:
        raise NotFoundError("会議室が見つかりません")
    if not room["is_active"]:
        raise ValidationError("無効化された会議室は予約できません",
                               details=[{"field": "room_id", "reason": "inactive"}])
    # CR-003: 参加予定人数が会議室の収容人数を超えないこと (docs/P003-backend-spec.md §7.11)。
    # 予約と会議室の2エンティティにまたがる検証のため、会議室レコードを取得済みの
    # Service層に置く。収容人数と等しい値は許容する。
    attendee_count = data.get("attendee_count")
    if attendee_count is not None and attendee_count > room["capacity"]:
        raise ValidationError(
            f"参加予定人数が会議室の収容人数({room['capacity']}名)を超えています",
            details=[{"field": "attendee_count", "reason": "exceeds room capacity"}])
    for participant_id in data.get("participant_ids", []):
        if user_repository.find_by_id(conn, participant_id) is None:
            raise NotFoundError(f"参加者ID {participant_id} が見つかりません")


def create(conn: sqlite3.Connection, data: dict, current_user) -> dict:
    _validate_common(data)
    _check_room_and_participants(conn, data)
    reservation_id = reservation_repository.insert_with_participants(conn, data, current_user["id"])
    return reservation_repository.find_with_detail(conn, reservation_id)


def list_for_calendar(conn: sqlite3.Connection, date_from: str, date_to: str,
                       room_ids: list[int] | None = None):
    return reservation_repository.list_by_range(conn, date_from, date_to, room_ids)


def get_detail(conn: sqlite3.Connection, reservation_id: int) -> dict:
    detail = reservation_repository.find_with_detail(conn, reservation_id)
    if detail is None:
        raise NotFoundError("予約が見つかりません")
    return detail


def list_mine(conn: sqlite3.Connection, current_user_id: int, period: str = "upcoming"):
    return reservation_repository.list_by_creator(conn, current_user_id, period)


def check_editable(reservation: dict, current_user) -> None:
    if reservation["created_by"]["id"] != current_user["id"] and current_user["role"] != "admin":
        raise ForbiddenError("この予約を編集する権限がありません")


def update(conn: sqlite3.Connection, reservation_id: int, data: dict, current_user) -> dict:
    existing = reservation_repository.find_with_detail(conn, reservation_id)
    if existing is None:
        raise NotFoundError("予約が見つかりません")
    check_editable(existing, current_user)
    _validate_common(data)
    _check_room_and_participants(conn, data)
    reservation_repository.update_with_participants(conn, reservation_id, data)
    return reservation_repository.find_with_detail(conn, reservation_id)


def delete(conn: sqlite3.Connection, reservation_id: int, current_user) -> None:
    existing = reservation_repository.find_with_detail(conn, reservation_id)
    if existing is None:
        raise NotFoundError("予約が見つかりません")
    check_editable(existing, current_user)
    reservation_repository.delete(conn, reservation_id)
