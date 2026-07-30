"""予約API。docs/02-frontend-spec.md 2章「reservations」、docs/03-backend-spec.md 4章「予約系」対応。"""
from datetime import date as date_cls

from starlette.responses import JSONResponse

from app.deps import ApiError, error_response, require_login
from app.repositories import reservations as res_repo
from app.repositories import rooms as rooms_repo
from app.schemas import ReservationWriteRequest
from app.validation import validate_reservation_input


async def list_reservations_handler(request):
    try:
        require_login(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    room_id_raw = request.query_params.get("room_id")
    if not date_from or not date_to:
        return error_response(400, "VALIDATION_ERROR", "date_from, date_to は必須です")
    if date_from > date_to:
        return error_response(400, "VALIDATION_ERROR", "date_from は date_to 以前である必要があります")
    room_id = int(room_id_raw) if room_id_raw else None
    return JSONResponse(res_repo.list_reservations(conn, date_from, date_to, room_id))


async def list_mine_handler(request):
    try:
        user = require_login(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    period = request.query_params.get("period", "future")
    today = date_cls.today().isoformat()
    return JSONResponse(res_repo.list_mine(conn, user["id"], period, today))


async def get_reservation_handler(request):
    try:
        require_login(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    reservation_id = int(request.path_params["reservation_id"])
    reservation = res_repo.get_reservation(conn, reservation_id)
    if reservation is None:
        return error_response(404, "NOT_FOUND", "予約が存在しません")
    return JSONResponse(reservation)


async def _validate_and_extract(request, conn):
    """POST/PUTで共通のバリデーション。参加者ID実在チェックを最初から含む(V0.2 F001対応)。"""
    body = await request.json()
    payload = ReservationWriteRequest(**body)

    field_errors = validate_reservation_input(body)
    if field_errors:
        return None, error_response(400, "VALIDATION_ERROR", "; ".join(field_errors))

    room = rooms_repo.get_room(conn, payload.room_id)
    if room is None or not room["is_active"]:
        return None, error_response(404, "NOT_FOUND", "指定した会議室が存在しないか無効です")

    missing = res_repo.find_missing_participant_ids(conn, payload.participant_ids)
    if missing:
        return None, error_response(
            400, "VALIDATION_ERROR", f"存在しない、または無効な参加者IDが指定されています: {missing}"
        )

    return payload, None


async def create_reservation_handler(request):
    try:
        user = require_login(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    try:
        payload, err = await _validate_and_extract(request, conn)
    except Exception:
        return error_response(400, "VALIDATION_ERROR", "リクエストボディが不正です")
    if err:
        return err
    try:
        reservation = res_repo.create_reservation(
            conn,
            payload.room_id,
            payload.date,
            payload.start_time,
            payload.end_time,
            payload.subject,
            payload.notes,
            user["id"],
            payload.participant_ids,
        )
    except res_repo.ConflictError as e:
        return error_response(409, "CONFLICT", str(e))
    return JSONResponse(reservation, status_code=201)


async def update_reservation_handler(request):
    try:
        user = require_login(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    reservation_id = int(request.path_params["reservation_id"])
    existing = res_repo.get_reservation(conn, reservation_id)
    if existing is None:
        return error_response(404, "NOT_FOUND", "予約が存在しません")
    if existing["created_by"] != user["id"] and user["role"] != "admin":
        return error_response(403, "FORBIDDEN", "本人または管理者のみ編集できます")
    try:
        payload, err = await _validate_and_extract(request, conn)
    except Exception:
        return error_response(400, "VALIDATION_ERROR", "リクエストボディが不正です")
    if err:
        return err
    try:
        reservation = res_repo.update_reservation(
            conn,
            reservation_id,
            payload.room_id,
            payload.date,
            payload.start_time,
            payload.end_time,
            payload.subject,
            payload.notes,
            existing["created_by"],
            payload.participant_ids,
        )
    except res_repo.ConflictError as e:
        return error_response(409, "CONFLICT", str(e))
    return JSONResponse(reservation)


async def delete_reservation_handler(request):
    try:
        user = require_login(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    reservation_id = int(request.path_params["reservation_id"])
    existing = res_repo.get_reservation(conn, reservation_id)
    if existing is None:
        return error_response(404, "NOT_FOUND", "予約が存在しません")
    if existing["created_by"] != user["id"] and user["role"] != "admin":
        return error_response(403, "FORBIDDEN", "本人または管理者のみ取消できます")
    res_repo.delete_reservation(conn, reservation_id)
    return JSONResponse(None, status_code=204)
