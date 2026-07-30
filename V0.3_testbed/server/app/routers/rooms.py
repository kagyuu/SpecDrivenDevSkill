"""会議室API。docs/02-frontend-spec.md 2章「rooms」、docs/03-backend-spec.md 4章「会議室系」対応。"""
from starlette.responses import JSONResponse

from app.deps import ApiError, error_response, require_admin, require_login
from app.repositories import rooms as rooms_repo
from app.schemas import RoomCreateRequest, RoomUpdateRequest


async def list_rooms_handler(request):
    try:
        user = require_login(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    include_inactive_raw = request.query_params.get("include_inactive", "false")
    include_inactive = include_inactive_raw.lower() == "true" and user["role"] == "admin"
    return JSONResponse(rooms_repo.list_rooms(conn, include_inactive))


async def create_room_handler(request):
    try:
        require_admin(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    try:
        body = await request.json()
        payload = RoomCreateRequest(**body)
    except Exception:
        return error_response(400, "VALIDATION_ERROR", "リクエストボディが不正です")
    if payload.capacity < 1:
        return error_response(400, "VALIDATION_ERROR", "capacity は1以上である必要があります")
    if rooms_repo.name_exists(conn, payload.name):
        return error_response(400, "VALIDATION_ERROR", "同名の会議室が既に存在します")
    room = rooms_repo.create_room(conn, payload.name, payload.capacity, payload.equipment)
    return JSONResponse(room, status_code=201)


async def update_room_handler(request):
    try:
        require_admin(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    room_id = int(request.path_params["room_id"])
    if rooms_repo.get_room(conn, room_id) is None:
        return error_response(404, "NOT_FOUND", "会議室が存在しません")
    try:
        body = await request.json()
        payload = RoomUpdateRequest(**body)
    except Exception:
        return error_response(400, "VALIDATION_ERROR", "リクエストボディが不正です")
    if payload.capacity < 1:
        return error_response(400, "VALIDATION_ERROR", "capacity は1以上である必要があります")
    if rooms_repo.name_exists(conn, payload.name, exclude_id=room_id):
        return error_response(400, "VALIDATION_ERROR", "同名の会議室が既に存在します")
    room = rooms_repo.update_room(conn, room_id, payload.name, payload.capacity, payload.equipment, payload.is_active)
    return JSONResponse(room)


async def delete_room_handler(request):
    try:
        require_admin(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    room_id = int(request.path_params["room_id"])
    if rooms_repo.get_room(conn, room_id) is None:
        return error_response(404, "NOT_FOUND", "会議室が存在しません")
    rooms_repo.deactivate_room(conn, room_id)
    return JSONResponse(None, status_code=204)
