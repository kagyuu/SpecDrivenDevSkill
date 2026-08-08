"""API-12〜API-17(予約)のHTTP入出力(P002 5.7 / P003 6.4)。

権限判定(予約者本人または管理者)は `reservation_service` 側で行う(U003-T4)。
"""

from __future__ import annotations

from datetime import date

from starlette.requests import Request
from starlette.responses import Response

from .. import auth, schemas
from ..errors import ApiError, json_response
from ..schemas import DATE_PATTERN, ReservationRequest
from ..services import reservation_service
from .auth_handlers import _json_body

#: API-12 の期間の上限(P002 5.7「範囲は最大31日」)
MAX_PERIOD_DAYS = 31
VALID_PERIODS = ("upcoming", "past")


def _validation_error(field: str, message: str) -> ApiError:
    return ApiError(
        400,
        "VALIDATION_ERROR",
        "入力内容に誤りがあります。",
        details=[{"field": field, "message": message}],
    )


def _required_date(request: Request, name: str) -> str:
    raw = request.query_params.get(name)
    if raw is None or raw == "" or not DATE_PATTERN.match(raw):
        raise _validation_error(name, "日付を入力してください。")
    try:
        date.fromisoformat(raw)  # 形式は合っていても実在しない日付(2026-02-30 など)を弾く
    except ValueError as exc:
        raise _validation_error(name, "日付を入力してください。") from exc
    return raw


def _reservation_id(request: Request) -> int:
    try:
        return int(request.path_params["reservation_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ApiError(404, "NOT_FOUND", reservation_service.NOT_FOUND_MESSAGE) from exc


def _room_ids(request: Request) -> list[int] | None:
    """`room_id` は繰り返し可。未指定なら全件(P002 5.7 API-12)。"""
    raw_values = request.query_params.getlist("room_id")
    if not raw_values:
        return None
    room_ids: list[int] = []
    for raw in raw_values:
        try:
            room_ids.append(int(raw))
        except (TypeError, ValueError) as exc:
            # ★FIXME★ `room_id` が整数でない場合の扱いはP002 5.7に記載がないため 400 と解釈した
            raise _validation_error("room_id", "会議室を選択してください。") from exc
    return room_ids


def _period_days(date_from: str, date_to: str) -> int:
    start = date.fromisoformat(date_from)
    end = date.fromisoformat(date_to)
    return (end - start).days + 1


async def list_reservations(request: Request) -> Response:
    """API-12 `GET /api/reservations`(要ログイン)。"""
    auth.require_login(request)
    date_from = _required_date(request, "date_from")
    date_to = _required_date(request, "date_to")
    if date_to < date_from:
        raise _validation_error("date_to", "終了日は開始日以降にしてください。")
    # ★FIXME★ 期間超過時の文言はP002 5.7に記載がないため、上限日数から補った
    if _period_days(date_from, date_to) > MAX_PERIOD_DAYS:
        raise _validation_error("date_to", f"期間は{MAX_PERIOD_DAYS}日以内で指定してください。")
    room_ids = _room_ids(request)
    with auth.open_conn(request) as conn:
        reservations = reservation_service.list_by_period(conn, date_from, date_to, room_ids)
    return json_response({"reservations": reservations}, status_code=200)


async def list_my_reservations(request: Request) -> Response:
    """API-13 `GET /api/reservations/mine`(要ログイン)。

    `/api/reservations/{reservation_id}` より**先に**ルート登録すること(P003 6.4)。
    """
    actor = auth.require_login(request)
    period = request.query_params.get("period") or "upcoming"
    if period not in VALID_PERIODS:
        # ★FIXME★ 不正な `period` の文言はP002 5.7に記載がないため補った
        raise _validation_error("period", "period の指定が正しくありません。")
    with auth.open_conn(request) as conn:
        reservations = reservation_service.list_mine(conn, actor, period)
    return json_response({"reservations": reservations}, status_code=200)


async def get_reservation(request: Request) -> Response:
    """API-14 `GET /api/reservations/{reservation_id}`(要ログイン。閲覧は全員可)。"""
    auth.require_login(request)
    reservation_id = _reservation_id(request)
    with auth.open_conn(request) as conn:
        reservation = reservation_service.get_detail(conn, reservation_id)
    return json_response({"reservation": reservation}, status_code=200)


async def create_reservation(request: Request) -> Response:
    """API-15 `POST /api/reservations`(要ログイン)。成功時 201。"""
    actor = auth.require_login(request)
    payload = schemas.validate(ReservationRequest, await _json_body(request))
    with auth.open_conn(request) as conn:
        reservation = reservation_service.create(conn, actor, payload)
    return json_response({"reservation": reservation}, status_code=201)


async def update_reservation(request: Request) -> Response:
    """API-16 `PUT /api/reservations/{reservation_id}`(要ログイン。全置換更新)。"""
    actor = auth.require_login(request)
    reservation_id = _reservation_id(request)
    payload = schemas.validate(ReservationRequest, await _json_body(request))
    with auth.open_conn(request) as conn:
        reservation = reservation_service.update(conn, actor, reservation_id, payload)
    return json_response({"reservation": reservation}, status_code=200)


async def delete_reservation(request: Request) -> Response:
    """API-17 `DELETE /api/reservations/{reservation_id}`(要ログイン)。成功時 204(本文なし)。"""
    actor = auth.require_login(request)
    reservation_id = _reservation_id(request)
    with auth.open_conn(request) as conn:
        reservation_service.delete(conn, actor, reservation_id)
    return Response(status_code=204)
