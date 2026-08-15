"""GET/POST/PUT/DELETE /api/users(全操作、管理者専用)。

docs/P002-frontend-spec.md §3 S07。docs/P003-backend-spec.md §5.11。
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.api.deps import get_db, require_admin
from app.repositories.users import User
from app.schemas.user import UserCreateRequest, UserResponse, UserUpdateRequest
from app.services.users import create_user_flow, deactivate_user_flow, list_users_flow, update_user_flow

router = APIRouter(tags=["users"])


def _to_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, employee_id=user.employee_id, name=user.name, role=user.role, is_active=user.is_active)


@router.get("/api/users", response_model=list[UserResponse])
def get_users(
    conn: sqlite3.Connection = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> list[UserResponse]:
    users = list_users_flow(conn)
    return [_to_response(u) for u in users]


@router.post("/api/users", response_model=UserResponse, status_code=201)
def post_user(
    payload: UserCreateRequest,
    conn: sqlite3.Connection = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserResponse:
    now = datetime.now(timezone.utc)
    user = create_user_flow(conn, payload, now=now)
    return _to_response(user)


@router.put("/api/users/{user_id}", response_model=UserResponse)
def put_user(
    user_id: int,
    payload: UserUpdateRequest,
    conn: sqlite3.Connection = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserResponse:
    now = datetime.now(timezone.utc)
    user = update_user_flow(conn, user_id, payload, now=now)
    return _to_response(user)


@router.delete("/api/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    now = datetime.now(timezone.utc)
    deactivate_user_flow(conn, user_id, current_user=admin, now=now)
    return None
