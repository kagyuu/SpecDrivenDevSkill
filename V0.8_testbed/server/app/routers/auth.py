"""Auth API router (U001-T4, docs/P007-impl-direction/U001-foundation-and-auth.md).

Implements docs/P002-frontend-spec.md 4.1〜4.3節 (external contract) on top
of app/services/auth_service.py (U001-T3, Service layer). Exceptions raised
by the Service layer are deliberately not caught here - app/errors.py
registers app-wide exception handlers (wired in app/main.py) that map them
to the HTTP responses this contract requires. This mirrors this task's own
実装してはいけないこと in docs/P007-impl-direction/U001-foundation-and-auth.md:
routers/handlers do HTTP-shape work only, never business logic.

(This file previously held a placeholder stub created ahead of schedule
while U001-T3 was still in progress, a "先行実装の禁止" violation per
SKILL-P102-implement.md - see docs/P007-impl-direction/U001-foundation-and-auth.md
U001-T3 for how that was found and resolved. It has been fully replaced by
this task's real implementation.)
"""

from __future__ import annotations

import os
import sqlite3

from fastapi import APIRouter, Cookie, Depends, Response

from app.dependencies import get_current_user, get_db
from app.repositories.user_repository import UserRow
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse
from app.services import auth_service

router = APIRouter(tags=["auth"])

_SESSION_COOKIE_NAME = "session_id"
_SESSION_MAX_AGE_SECONDS = 8 * 60 * 60  # 8時間固定, docs/P002-frontend-spec.md 2章


def _cookie_secure() -> bool:
    # docs/P003-backend-spec.md 4.1節: 開発環境(HTTP)はCOOKIE_SECURE=falseで
    # Secure属性を外せるようにする。既定は本番相当のtrue。
    return os.environ.get("COOKIE_SECURE", "true").lower() != "false"


def _to_response_fields(user: UserRow) -> dict[str, str]:
    return {"employee_id": user["user_id"], "name": user["name"], "role": user["role"]}


@router.post("/api/auth/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
) -> LoginResponse:
    session = auth_service.login(conn, body.employee_id, body.password)
    user = auth_service.get_current_user(conn, session["session_id"])
    response.set_cookie(
        key=_SESSION_COOKIE_NAME,
        value=session["session_id"],
        max_age=_SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
    )
    return LoginResponse(**_to_response_fields(user))


@router.post("/api/auth/logout")
def logout(
    response: Response,
    session_id: str | None = Cookie(default=None),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    # No request body (docs/P002-frontend-spec.md 4.2節 "リクエストボディ: なし");
    # session_id comes from the Cookie. auth_service.logout() is idempotent,
    # so a missing/invalid session_id still returns 200 per that section.
    auth_service.logout(conn, session_id)
    response.delete_cookie(key=_SESSION_COOKIE_NAME)
    return {}


@router.get("/api/me", response_model=MeResponse)
def me(user: UserRow = Depends(get_current_user)) -> MeResponse:
    return MeResponse(**_to_response_fields(user))
