"""API-08〜API-11(ユーザー)のHTTP入出力(P002 5.6 / P003 6.3)。"""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import Response

from .. import auth, schemas
from ..errors import ApiError, json_response
from ..schemas import UserCreateRequest, UserUpdateRequest
from ..services import user_service
from .auth_handlers import _json_body

VALID_SCOPES = (user_service.SCOPE_MANAGEMENT, user_service.SCOPE_ATTENDEE_CANDIDATES)


def _scope(request: Request) -> str:
    scope = request.query_params.get("scope") or user_service.SCOPE_MANAGEMENT
    if scope not in VALID_SCOPES:
        # ★FIXME★ 未知の `scope` の扱いはP002 5.6に記載がないため 400 と解釈した
        raise ApiError(
            400,
            "VALIDATION_ERROR",
            "入力内容に誤りがあります。",
            details=[{"field": "scope", "message": "scope の指定が正しくありません。"}],
        )
    return scope


async def list_users(request: Request) -> Response:
    """API-08 `GET /api/users`。`scope=attendee_candidates` のみ要ログイン、他は管理者。"""
    scope = _scope(request)
    if scope == user_service.SCOPE_ATTENDEE_CANDIDATES:
        user = auth.require_login(request)
        include_inactive = False
    else:
        user = auth.require_admin(request)
        raw = request.query_params.get("include_inactive")
        include_inactive = True if raw is None else raw.lower() == "true"
    with auth.open_conn(request) as conn:
        users = user_service.list_users(conn, user, scope, include_inactive)
    return json_response({"users": users}, status_code=200)


async def create_user(request: Request) -> Response:
    """API-09 `POST /api/users`(管理者)。"""
    auth.require_admin(request)
    payload = schemas.validate(UserCreateRequest, await _json_body(request))
    with auth.open_conn(request) as conn:
        user = user_service.create_user(conn, payload)
    return json_response({"user": user}, status_code=201)


async def update_user(request: Request) -> Response:
    """API-10 `PUT /api/users/{user_id}`(管理者)。"""
    auth.require_admin(request)
    user_id = request.path_params["user_id"]
    payload = schemas.validate(UserUpdateRequest, await _json_body(request))
    with auth.open_conn(request) as conn:
        user = user_service.update_user(conn, user_id, payload)
    return json_response({"user": user}, status_code=200)


async def deactivate_user(request: Request) -> Response:
    """API-11 `DELETE /api/users/{user_id}`(管理者)。論理削除。"""
    actor = auth.require_admin(request)
    user_id = request.path_params["user_id"]
    with auth.open_conn(request) as conn:
        user_service.deactivate_user(conn, actor, user_id)
    return Response(status_code=204)
