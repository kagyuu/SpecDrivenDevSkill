"""会議室API (docs/P002-frontend-spec.md §4.4〜§4.7)."""
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.api.deps import get_conn, require_admin, require_auth
from app.repositories import room_repository
from app.services import room_service


def _room_dict(room) -> dict:
    equipment = room["equipment"] or ""
    equipment_list = equipment.split(",") if equipment else []
    return {
        "id": room["id"],
        "name": room["name"],
        "capacity": room["capacity"],
        "equipment": equipment_list,
        "is_active": bool(room["is_active"]),
        "description": room["description"],  # CR-002で追加。任意項目のためNoneのこともある。
    }


async def list_rooms(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        user = require_auth(request, conn)
        include_inactive_param = request.query_params.get("include_inactive", "false")
        include_inactive = include_inactive_param.lower() == "true" and user["role"] == "admin"
        rooms = room_repository.list(conn, include_inactive=include_inactive)
        return JSONResponse({"rooms": [_room_dict(r) for r in rooms]})
    finally:
        conn.close()


async def create_room(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        require_admin(request, conn)
        body = await request.json()
        room = room_service.create(conn, body)
        return JSONResponse(_room_dict(room), status_code=201)
    finally:
        conn.close()


async def update_room(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        require_admin(request, conn)
        room_id = int(request.path_params["room_id"])
        body = await request.json()
        room = room_service.update(conn, room_id, body)
        return JSONResponse(_room_dict(room))
    finally:
        conn.close()


async def delete_room(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        require_admin(request, conn)
        room_id = int(request.path_params["room_id"])
        room = room_service.deactivate(conn, room_id)
        return JSONResponse({"id": room["id"], "is_active": bool(room["is_active"])})
    finally:
        conn.close()


routes = [
    Route("/api/rooms", list_rooms, methods=["GET"]),
    Route("/api/rooms", create_room, methods=["POST"]),
    Route("/api/rooms/{room_id}", update_room, methods=["PUT"]),
    Route("/api/rooms/{room_id}", delete_room, methods=["DELETE"]),
]
