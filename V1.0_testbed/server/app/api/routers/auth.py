"""POST /api/auth/login, POST /api/auth/logout, GET /api/me。

docs/P002-frontend-spec.md §1, §2, §3 S01, §9。docs/P003-backend-spec.md §5.1〜§5.3。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response

from app.api.deps import SESSION_COOKIE_NAME, get_current_user, get_db
from app.repositories.sessions import delete_session
from app.repositories.users import User
from app.schemas.auth import LoginRequest, MeResponse
from app.services.auth import login as login_service

router = APIRouter(tags=["auth"])


@router.post("/api/auth/login")
def login(
    payload: LoginRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    now = datetime.now(timezone.utc)
    user, token, _expires_at = login_service(conn, payload.employee_id, payload.password, now=now)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=8 * 60 * 60,
    )
    return {
        "user": {
            "id": user.id,
            "employee_id": user.employee_id,
            "name": user.name,
            "role": user.role,
        }
    }


@router.post("/api/auth/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        delete_session(conn, token)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return None


@router.get("/api/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(id=user.id, employee_id=user.employee_id, name=user.name, role=user.role)
