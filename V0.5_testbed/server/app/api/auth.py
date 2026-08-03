"""認証API (docs/P002-frontend-spec.md §4.1〜§4.3)."""
from __future__ import annotations

import os

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.api.deps import SESSION_COOKIE_NAME, get_conn, require_auth
from app.core.exceptions import ValidationError
from app.services import auth_service

COOKIE_MAX_AGE = 28800  # 8時間


def _cookie_secure() -> bool:
    """セッションCookieの `Secure` 属性を決定する。

    ★F001修正★ ADR-004はCookieを `HttpOnly / Secure / SameSite=Lax` とすることを決定しており、
    既定値は `secure=True`(ADR-004どおり)を維持する。ただし本アプリの配布物には現状TLS終端
    コンポーネント(リバースプロキシ等)が含まれておらず、`server/INDEX.md` の実行方法どおり
    プレーンHTTPで起動すると、Secure属性のためログイン直後から一切Cookieが送信されず
    実質的にログイン状態を維持できない(`docs/test-records/20260803-1900-test-record.md` 根本原因1)。
    TLSのないローカル動作確認・受け入れテスト時のみ、環境変数 `SESSION_COOKIE_SECURE=false` を
    明示的に指定することでSecure属性を無効化できるようにする(本番相当の既定動作は変えない)。
    """
    return os.environ.get("SESSION_COOKIE_SECURE", "true").strip().lower() != "false"


def _user_dict(user) -> dict:
    return {
        "id": user["id"],
        "employee_id": user["employee_id"],
        "name": user["name"],
        "role": user["role"],
    }


async def login(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}
    employee_id = body.get("employee_id")
    password = body.get("password")
    if not employee_id or not password:
        raise ValidationError(
            "employee_idとpasswordは必須です",
            details=[{"field": "employee_id", "reason": "required"}],
        )
    conn = get_conn(request)
    try:
        user, session_id = auth_service.login(conn, employee_id, password)
    finally:
        conn.close()
    resp = JSONResponse({"user": _user_dict(user)})
    resp.set_cookie(
        SESSION_COOKIE_NAME, session_id,
        max_age=COOKIE_MAX_AGE, httponly=True, secure=_cookie_secure(), samesite="lax",
    )
    return resp


async def logout(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        auth_service.logout(conn, session_id)
    finally:
        conn.close()
    resp = JSONResponse({"message": "logged out"})
    resp.delete_cookie(SESSION_COOKIE_NAME)
    return resp


async def me(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        user = require_auth(request, conn)
    finally:
        conn.close()
    return JSONResponse({"user": _user_dict(user)})


routes = [
    Route("/api/auth/login", login, methods=["POST"]),
    Route("/api/auth/logout", logout, methods=["POST"]),
    Route("/api/me", me, methods=["GET"]),
]
