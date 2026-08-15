"""GET/POST/PUT/DELETE /api/rooms。

docs/P002-frontend-spec.md §3 S02/S03/S06。docs/P003-backend-spec.md §5.4, §5.5。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_db, require_admin
from app.repositories.rooms import Room
from app.repositories.users import User
from app.schemas.room import RoomCreateRequest, RoomResponse, RoomUpdateRequest
from app.services.rooms import create_room_flow, deactivate_room_flow, list_rooms_flow, update_room_flow

router = APIRouter(tags=["rooms"])


def _to_response(room: Room) -> RoomResponse:
    return RoomResponse(
        id=room.id,
        name=room.name,
        capacity=room.capacity,
        equipment=room.equipment,
        description=room.description,
        is_active=room.is_active,
    )


@router.get("/api/rooms", response_model=list[RoomResponse])
def get_rooms(
    include_inactive: bool = Query(default=False),
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[RoomResponse]:
    rooms = list_rooms_flow(conn, user, include_inactive=include_inactive)
    return [_to_response(r) for r in rooms]


@router.post("/api/rooms", response_model=RoomResponse, status_code=201)
def post_room(
    payload: RoomCreateRequest,
    conn: sqlite3.Connection = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RoomResponse:
    now = datetime.now(timezone.utc)
    room = create_room_flow(conn, payload, now=now)
    return _to_response(room)


@router.put("/api/rooms/{room_id}", response_model=RoomResponse)
def put_room(
    room_id: int,
    payload: RoomUpdateRequest,
    conn: sqlite3.Connection = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RoomResponse:
    now = datetime.now(timezone.utc)
    room = update_room_flow(conn, room_id, payload, now=now)
    return _to_response(room)


@router.delete("/api/rooms/{room_id}", status_code=204)
def delete_room(
    room_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> None:
    now = datetime.now(timezone.utc)
    deactivate_room_flow(conn, room_id, now=now)
    return None
