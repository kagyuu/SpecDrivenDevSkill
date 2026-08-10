"""Room API router (U002-T2, docs/P007-impl-direction/U002-room-management.md).

Implements docs/P002-frontend-spec.md 4.4〜4.5.2節 on top of
app/services/room_service.py (U002-T1). Authorization: GET requires login
only; POST/PUT/DELETE require admin (Depends(require_admin)).
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_db, require_admin
from app.repositories.room_repository import RoomRow
from app.repositories.user_repository import UserRow
from app.schemas.room import RoomCreateRequest, RoomResponse, RoomUpdateRequest
from app.services import room_service

router = APIRouter(tags=["rooms"])


def _to_response(room: RoomRow) -> RoomResponse:
    return RoomResponse(**room)


@router.get("/api/rooms", response_model=list[RoomResponse])
def list_rooms(
    include_inactive: bool = False,
    user: UserRow = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[RoomResponse]:
    # docs/P002-frontend-spec.md 4.4節: include_inactive=true is admin-only;
    # a non-admin's true is silently ignored (not an error).
    effective_include_inactive = include_inactive and user["role"] == "admin"
    rooms = room_service.list_rooms(conn, include_inactive=effective_include_inactive)
    return [_to_response(room) for room in rooms]


@router.post("/api/rooms", response_model=RoomResponse, status_code=201)
def create_room(
    body: RoomCreateRequest,
    _: UserRow = Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> RoomResponse:
    room = room_service.create(conn, body.name, body.capacity, body.equipment, body.description)
    return _to_response(room)


@router.put("/api/rooms/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: int,
    body: RoomUpdateRequest,
    _: UserRow = Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> RoomResponse:
    room = room_service.update(
        conn, room_id, body.name, body.capacity, body.equipment, body.description, body.is_active
    )
    return _to_response(room)


@router.delete("/api/rooms/{room_id}")
def delete_room(
    room_id: int,
    _: UserRow = Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    room = room_service.deactivate(conn, room_id)
    return {"room_id": room["room_id"], "is_active": bool(room["is_active"])}
