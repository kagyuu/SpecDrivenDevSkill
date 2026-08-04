"""予約API (docs/P002-frontend-spec.md §4.8〜§4.13).

U003-5: GET /api/reservations, POST /api/reservations
U004-4: GET /api/reservations/mine, GET/PUT/DELETE /api/reservations/{reservation_id}
"""
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.api.deps import get_conn, require_auth
from app.core.datetime_utils import parse_date
from app.core.exceptions import ValidationError
from app.services import reservation_service


def _list_item_dict(row) -> dict:
    return {
        "id": row["id"], "room_id": row["room_id"], "date": row["date"],
        "start_time": row["start_time"], "end_time": row["end_time"], "title": row["title"],
        "created_by": {"id": row["created_by_id"], "name": row["created_by_name"]},
    }


def _detail_dict(detail: dict) -> dict:
    return detail


async def list_reservations(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        require_auth(request, conn)
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if not date_from or not date_to:
            raise ValidationError("date_fromとdate_toは必須です",
                                   details=[{"field": "date_from", "reason": "required"}])
        try:
            parse_date(date_from)
            parse_date(date_to)
        except ValueError:
            raise ValidationError("date_from/date_toの形式が不正です",
                                   details=[{"field": "date_from", "reason": "invalid format"}])
        room_ids_param = request.query_params.get("room_ids")
        room_ids = [int(x) for x in room_ids_param.split(",")] if room_ids_param else None
        rows = reservation_service.list_for_calendar(conn, date_from, date_to, room_ids)
        return JSONResponse({"reservations": [_list_item_dict(r) for r in rows]})
    finally:
        conn.close()


async def create_reservation(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        user = require_auth(request, conn)
        body = await request.json()
        detail = reservation_service.create(conn, body, user)
        return JSONResponse(_detail_dict(detail), status_code=201)
    finally:
        conn.close()


async def list_mine(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        user = require_auth(request, conn)
        period = request.query_params.get("period", "upcoming")
        rows = reservation_service.list_mine(conn, user["id"], period)
        return JSONResponse({"reservations": [
            {
                "id": r["id"], "room_id": r["room_id"], "date": r["date"],
                "start_time": r["start_time"], "end_time": r["end_time"], "title": r["title"],
                # CR-003: マイ予約一覧には参加予定人数を含める(S02カレンダー用の
                # GET /api/reservations には含めない。docs/P002-frontend-spec.md §4.8/§4.9)
                "attendee_count": r["attendee_count"],
                "created_by": {"id": r["created_by"], "name": r["created_by_name"]},
            } for r in rows
        ]})
    finally:
        conn.close()


async def get_reservation(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        require_auth(request, conn)
        reservation_id = int(request.path_params["reservation_id"])
        detail = reservation_service.get_detail(conn, reservation_id)
        return JSONResponse(_detail_dict(detail))
    finally:
        conn.close()


async def update_reservation(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        user = require_auth(request, conn)
        reservation_id = int(request.path_params["reservation_id"])
        body = await request.json()
        detail = reservation_service.update(conn, reservation_id, body, user)
        return JSONResponse(_detail_dict(detail))
    finally:
        conn.close()


async def delete_reservation(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        user = require_auth(request, conn)
        reservation_id = int(request.path_params["reservation_id"])
        reservation_service.delete(conn, reservation_id, user)
        return JSONResponse({"id": reservation_id, "deleted": True})
    finally:
        conn.close()


routes = [
    # "mine" は固定パスとして {reservation_id} より先に定義する(docs/P007-impl-direction/U004-*.md)
    Route("/api/reservations/mine", list_mine, methods=["GET"]),
    Route("/api/reservations", list_reservations, methods=["GET"]),
    Route("/api/reservations", create_reservation, methods=["POST"]),
    Route("/api/reservations/{reservation_id}", get_reservation, methods=["GET"]),
    Route("/api/reservations/{reservation_id}", update_reservation, methods=["PUT"]),
    Route("/api/reservations/{reservation_id}", delete_reservation, methods=["DELETE"]),
]
