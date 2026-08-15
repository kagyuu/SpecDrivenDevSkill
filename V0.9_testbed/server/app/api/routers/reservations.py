"""GET /api/reservations, GET /api/reservations/mine, GET /api/reservations/{id}, POST /api/reservations。

docs/P002-frontend-spec.md §3 S02/S03/S05, §7.2。docs/P003-backend-spec.md §5.6〜§5.9。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_db
from app.repositories.reservations import Reservation
from app.repositories.users import User
from app.schemas.reservation import ReservationCreateRequest, ReservationResponse, ReservationUpdateRequest
from app.services.reservations import (
    create_reservation_flow,
    delete_reservation_flow,
    get_reservation_flow,
    list_my_reservations_flow,
    list_reservations_flow,
    update_reservation_flow,
)

router = APIRouter(tags=["reservations"])


def _to_response(reservation: Reservation, viewer: User) -> ReservationResponse:
    """docs/P003-backend-spec.md 「internal_memo のマスキング(※CR-001により追加)」参照。

    Repository層は常に実値を返す。閲覧者が所有者・管理者でない場合、Router層で
    internal_memoをnullに置き換える(予約自体は誰でも閲覧可能なため403にはしない)。
    """
    can_view_memo = viewer.id == reservation.user_id or viewer.is_admin
    return ReservationResponse(
        id=reservation.id,
        room_id=reservation.room_id,
        room_name=reservation.room_name,
        user_id=reservation.user_id,
        user_name=reservation.user_name,
        date=reservation.date,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        title=reservation.title,
        participant_ids=reservation.participant_ids,
        expected_attendees=reservation.expected_attendees,
        notes=reservation.notes,
        internal_memo=reservation.internal_memo if can_view_memo else None,  # ※CR-001により追加
    )


@router.get("/api/reservations", response_model=list[ReservationResponse])
def get_reservations(
    date_from: str = Query(...),
    date_to: str = Query(...),
    room_id: int | None = Query(default=None),
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReservationResponse]:
    reservations = list_reservations_flow(conn, date_from, date_to, room_id)
    return [_to_response(r, user) for r in reservations]


@router.get("/api/reservations/mine", response_model=list[ReservationResponse])
def get_my_reservations(
    period: Literal["upcoming", "past"] = Query(default="upcoming"),
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReservationResponse]:
    now = datetime.now(timezone.utc)
    reservations = list_my_reservations_flow(conn, user, now=now, period=period)
    return [_to_response(r, user) for r in reservations]


@router.get("/api/reservations/{reservation_id}", response_model=ReservationResponse)
def get_reservation(
    reservation_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReservationResponse:
    reservation = get_reservation_flow(conn, reservation_id)
    return _to_response(reservation, user)


@router.post("/api/reservations", response_model=ReservationResponse, status_code=201)
def post_reservation(
    payload: ReservationCreateRequest,
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReservationResponse:
    now = datetime.now(timezone.utc)
    reservation = create_reservation_flow(conn, payload, current_user=user, now=now)
    return _to_response(reservation, user)


@router.put("/api/reservations/{reservation_id}", response_model=ReservationResponse)
def put_reservation(
    reservation_id: int,
    payload: ReservationUpdateRequest,
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReservationResponse:
    now = datetime.now(timezone.utc)
    reservation = update_reservation_flow(conn, reservation_id, payload, current_user=user, now=now)
    return _to_response(reservation, user)


@router.delete("/api/reservations/{reservation_id}", status_code=204)
def delete_reservation_endpoint(
    reservation_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    delete_reservation_flow(conn, reservation_id, current_user=user)
    return None
