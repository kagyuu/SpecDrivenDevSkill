"""API-01〜API-03(認証)のHTTP入出力(P002 5.4 / P003 6.1)。"""

from __future__ import annotations

import json

from starlette.requests import Request
from starlette.responses import Response

from .. import auth, db, schemas
from ..errors import ApiError, json_response
from ..schemas import LoginRequest, UserResponse
from ..services import auth_service

#: P002 5.4 が定めるCookie属性
COOKIE_ATTRS = "HttpOnly; SameSite=Lax; Secure; Path=/"


async def _json_body(request: Request) -> dict:
    raw = await request.body()
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ApiError(
            400,
            "VALIDATION_ERROR",
            "入力内容に誤りがあります。",
            details=[{"field": "body", "message": "リクエストの形式が正しくありません。"}],
        ) from exc


async def login(request: Request) -> Response:
    """API-01 `POST /api/auth/login`(認証不要)。"""
    payload = schemas.validate(LoginRequest, await _json_body(request))
    with auth.open_conn(request) as conn:
        with db.transaction(conn):
            session_id, user = auth_service.login(conn, payload.user_id, payload.password)
    response = json_response({"user": UserResponse.of(user)}, status_code=200)
    response.headers.append(
        "set-cookie", f"{auth.COOKIE_NAME}={session_id}; {COOKIE_ATTRS}"
    )
    return response


async def logout(request: Request) -> Response:
    """API-02 `POST /api/auth/logout`(要ログイン)。"""
    auth.require_login(request)
    with auth.open_conn(request) as conn:
        with db.transaction(conn):
            auth_service.logout(conn, auth.session_id_of(request))
    response = Response(status_code=204)
    response.headers.append(
        "set-cookie", f"{auth.COOKIE_NAME}=; Max-Age=0; {COOKIE_ATTRS}"
    )
    return response


async def me(request: Request) -> Response:
    """API-03 `GET /api/me`(要ログイン)。追加のDBアクセスをしない。"""
    user = auth.require_login(request)
    return json_response({"user": UserResponse.of(user)}, status_code=200)
