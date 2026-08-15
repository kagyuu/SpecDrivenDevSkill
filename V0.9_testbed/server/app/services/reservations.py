"""予約Service層。docs/P003-backend-spec.md §5.6〜§5.9(バリデーション順序を含む)。"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Literal

from app.api.errors import ApiError
from app.repositories.reservations import (
    Reservation,
    create_reservation,
    delete_reservation,
    find_conflicting,
    get_by_id,
    list_by_range,
    list_by_user,
    update_reservation,
)
from app.repositories.rooms import get_room_by_id
from app.repositories.users import User
from app.schemas.reservation import ReservationCreateRequest, ReservationUpdateRequest
from app.validation.reservation import is_capacity_ok, is_time_range_valid

ReservationPayload = ReservationCreateRequest | ReservationUpdateRequest


def _validate_common(conn: sqlite3.Connection, payload: ReservationPayload) -> None:
    """docs/P003-backend-spec.md §5.9のバリデーション順序②〜④。①(必須・形式)はPydanticが担う。"""
    if not is_time_range_valid(payload.start_time, payload.end_time):
        raise ApiError(400, "INVALID_TIME_RANGE", "終了時刻は開始時刻より後の時刻を指定してください")

    room = get_room_by_id(conn, payload.room_id)
    if room is None:
        raise ApiError(404, "NOT_FOUND", "指定した会議室が見つかりません")
    if not room.is_active:
        raise ApiError(400, "ROOM_INACTIVE", "指定した会議室は現在利用できません")

    if not is_capacity_ok(payload.expected_attendees, room.capacity):
        raise ApiError(400, "CAPACITY_EXCEEDED", "参加予定人数が会議室の収容人数を超えています")


def _check_conflict(
    conn: sqlite3.Connection,
    payload: ReservationPayload,
    exclude_id: int | None,
) -> None:
    conflicts = find_conflicting(
        conn, payload.room_id, payload.date, payload.start_time, payload.end_time, exclude_id=exclude_id
    )
    if conflicts:
        raise ApiError(409, "RESERVATION_CONFLICT", "選択した会議室・時間帯は既に予約されています")


def create_reservation_flow(
    conn: sqlite3.Connection,
    payload: ReservationCreateRequest,
    current_user: User,
    now: datetime,
) -> Reservation:
    _validate_common(conn, payload)
    _check_conflict(conn, payload, exclude_id=None)

    reservation_id = create_reservation(
        conn,
        room_id=payload.room_id,
        user_id=current_user.id,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        title=payload.title,
        expected_attendees=payload.expected_attendees,
        notes=payload.notes,
        participant_ids=payload.participant_ids,
        created_at=now.isoformat(),
        internal_memo=payload.internal_memo,  # ※CR-001により追加
    )
    return get_by_id(conn, reservation_id)


def list_reservations_flow(
    conn: sqlite3.Connection,
    date_from: str,
    date_to: str,
    room_id: int | None,
) -> list[Reservation]:
    return list_by_range(conn, date_from, date_to, room_id)


def list_my_reservations_flow(
    conn: sqlite3.Connection,
    current_user: User,
    now: datetime,
    period: Literal["upcoming", "past"],
) -> list[Reservation]:
    return list_by_user(conn, current_user.id, now=now, period=period)


def get_reservation_flow(conn: sqlite3.Connection, reservation_id: int) -> Reservation:
    reservation = get_by_id(conn, reservation_id)
    if reservation is None:
        raise ApiError(404, "NOT_FOUND", "予約が見つかりません")
    return reservation


def _require_owner_or_admin(reservation: Reservation, current_user: User, message: str) -> None:
    if reservation.user_id != current_user.id and not current_user.is_admin:
        raise ApiError(403, "FORBIDDEN", message)


def update_reservation_flow(
    conn: sqlite3.Connection,
    reservation_id: int,
    payload: ReservationUpdateRequest,
    current_user: User,
    now: datetime,
) -> Reservation:
    existing = get_by_id(conn, reservation_id)
    if existing is None:
        raise ApiError(404, "NOT_FOUND", "予約が見つかりません")
    _require_owner_or_admin(existing, current_user, "この予約を編集する権限がありません")

    _validate_common(conn, payload)
    _check_conflict(conn, payload, exclude_id=reservation_id)

    update_reservation(
        conn,
        reservation_id,
        room_id=payload.room_id,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        title=payload.title,
        expected_attendees=payload.expected_attendees,
        notes=payload.notes,
        participant_ids=payload.participant_ids,
        updated_at=now.isoformat(),
        internal_memo=payload.internal_memo,  # ※CR-001により追加
    )
    return get_by_id(conn, reservation_id)


def delete_reservation_flow(
    conn: sqlite3.Connection,
    reservation_id: int,
    current_user: User,
) -> None:
    existing = get_by_id(conn, reservation_id)
    if existing is None:
        raise ApiError(404, "NOT_FOUND", "予約が見つかりません")
    _require_owner_or_admin(existing, current_user, "この予約を取り消す権限がありません")

    delete_reservation(conn, reservation_id)
