"""API-04〜API-07(会議室)のHTTP入出力(P002 5.5 / P003 6.2)。"""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from .. import auth, schemas
from ..errors import ApiError, json_response
from ..schemas import RoomRequest
from ..services import room_service
from .auth_handlers import _json_body


def _query_flag(request: Request, name: str, default: bool = False) -> bool:
    raw = request.query_params.get(name)
    if raw is None:
        return default
    return raw.lower() == "true"


def _room_id(request: Request) -> int:
    try:
        return int(request.path_params["room_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiError(404, "NOT_FOUND", room_service.NOT_FOUND_MESSAGE) from exc


async def list_rooms(request: Request) -> Response:
    """API-04 `GET /api/rooms`(要ログイン)。"""
    user = auth.require_login(request)
    include_inactive = _query_flag(request, "include_inactive", default=False)
    with auth.open_conn(request) as conn:
        rooms = room_service.list_rooms(conn, user, include_inactive)
    return json_response({"rooms": rooms}, status_code=200)


async def create_room(request: Request) -> Response:
    """API-05 `POST /api/rooms`(管理者)。"""
    auth.require_admin(request)
    payload = schemas.validate(RoomRequest, await _json_body(request))
    with auth.open_conn(request) as conn:
        room = room_service.create_room(conn, payload)
    return json_response({"room": room}, status_code=201)


async def update_room(request: Request) -> Response:
    """API-06 `PUT /api/rooms/{room_id}`(管理者)。"""
    auth.require_admin(request)
    room_id = _room_id(request)
    payload = schemas.validate(RoomRequest, await _json_body(request))
    with auth.open_conn(request) as conn:
        room = room_service.update_room(conn, room_id, payload)
    return json_response({"room": room}, status_code=200)


async def deactivate_room(request: Request) -> Response:
    """API-07 `DELETE /api/rooms/{room_id}`(管理者)。論理削除。"""
    auth.require_admin(request)
    room_id = _room_id(request)
    with auth.open_conn(request) as conn:
        room_service.deactivate_room(conn, room_id)
    return Response(status_code=204)
