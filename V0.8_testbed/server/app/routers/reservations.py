"""Reservation API router.

U003-T3: docs/P002-frontend-spec.md 4.6〜4.7節 (GET/POST list+create).
U004-T2 adds GET/PUT/DELETE /api/reservations/{id} and GET
/api/reservations/mine (4.8〜4.9.2節) to this same file, per that task's own
作成・編集対象ファイル.

Route ordering note: "/api/reservations/mine" is registered before
"/api/reservations/{reservation_id}" - FastAPI matches routes in
registration order, and a literal path segment must be tried before a
path-parameter segment can accidentally swallow it (i.e. "mine" would
otherwise fail int(reservation_id) conversion instead of ever reaching the
/mine handler).
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_current_user, get_db
from app.exceptions import ValidationError
from app.repositories.user_repository import UserRow
from app.schemas.reservation import (
    MyReservationListItemResponse,
    ReservationCreateRequest,
    ReservationDetailResponse,
    ReservationListItemResponse,
    ReservationUpdateRequest,
)
from app.services import reservation_service

router = APIRouter(tags=["reservations"])


@router.get("/api/reservations", response_model=list[ReservationListItemResponse])
def list_reservations(
    date_from: str,
    date_to: str,
    room_id: list[int] | None = Query(default=None),
    _: UserRow = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[ReservationListItemResponse]:
    if date_from > date_to:
        raise ValidationError(message="date_fromはdate_to以前を指定してください")
    results = reservation_service.list_reservations(conn, date_from, date_to, room_id)
    return [ReservationListItemResponse(**item) for item in results]


@router.post("/api/reservations", response_model=ReservationDetailResponse, status_code=201)
def create_reservation(
    body: ReservationCreateRequest,
    user: UserRow = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> ReservationDetailResponse:
    result = reservation_service.create_reservation(
        conn,
        body.room_id,
        body.date,
        body.start_time,
        body.end_time,
        body.title,
        body.participant_user_ids,
        body.attendee_count,
        body.notes,
        user["user_id"],
        body.meeting_url,  # CR-001 (U003-T7)
    )
    return ReservationDetailResponse(**result)


@router.get("/api/reservations/mine", response_model=list[MyReservationListItemResponse])
def list_my_reservations(
    period: str = "upcoming",
    user: UserRow = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[MyReservationListItemResponse]:
    results = reservation_service.list_my_reservations(conn, user["user_id"], period)
    return [MyReservationListItemResponse(**item) for item in results]


@router.get("/api/reservations/{reservation_id}", response_model=ReservationDetailResponse)
def get_reservation(
    reservation_id: int,
    user: UserRow = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> ReservationDetailResponse:
    result = reservation_service.get_reservation(conn, reservation_id, user["user_id"])
    return ReservationDetailResponse(**result)


@router.put("/api/reservations/{reservation_id}", response_model=ReservationDetailResponse)
def update_reservation(
    reservation_id: int,
    body: ReservationUpdateRequest,
    user: UserRow = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> ReservationDetailResponse:
    result = reservation_service.update_reservation(
        conn,
        reservation_id,
        body.room_id,
        body.date,
        body.start_time,
        body.end_time,
        body.title,
        body.participant_user_ids,
        body.attendee_count,
        body.notes,
        user["user_id"],
        body.meeting_url,  # CR-001 (U004-T6)
    )
    return ReservationDetailResponse(**result)


@router.delete("/api/reservations/{reservation_id}", status_code=204)
def cancel_reservation(
    reservation_id: int,
    user: UserRow = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> Response:
    reservation_service.cancel_reservation(conn, reservation_id, user["user_id"])
    return Response(status_code=204)
