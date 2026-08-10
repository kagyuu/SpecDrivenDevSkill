"""Users API router.

U003-T3 adds GET /api/users/directory (docs/P002-frontend-spec.md 4.10.1節,
login-only, any role). U005-T2 adds the admin-only CRUD endpoints
(GET/POST/PUT/DELETE /api/users, 4.10/4.11節) to this same file, per that
task's own 作成・編集対象ファイル - deliberately NOT touching the directory
endpoint's authorization (Depends(get_current_user), not require_admin),
per U005-T2's own 実装してはいけないこと.

No dedicated response_model class for the directory endpoint: it returns
app.repositories.user_repository.DirectoryEntry dicts
({"employee_id", "name"}) as-is, which already matches
docs/P002-frontend-spec.md 4.10.1節's shape exactly.
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_db, require_admin
from app.repositories.user_repository import DirectoryEntry, UserRow
from app.schemas.user import UserCreateRequest, UserResponse, UserUpdateRequest
from app.services import reservation_service, user_service

router = APIRouter(tags=["users"])


def _to_response(user: UserRow) -> UserResponse:
    return UserResponse(
        employee_id=user["user_id"], name=user["name"], role=user["role"], is_active=bool(user["is_active"])
    )


@router.get("/api/users/directory", response_model=list[DirectoryEntry])
def get_directory(
    _: UserRow = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[DirectoryEntry]:
    # docs/P003-backend-spec.md 4.10節: ログイン済みであれば誰でも呼べる
    # (role不問) - 管理者専用のGET /api/usersとは異なる認可。
    return reservation_service.list_participant_candidates(conn)


@router.get("/api/users", response_model=list[UserResponse])
def list_users(
    include_inactive: bool = False,
    _: UserRow = Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> list[UserResponse]:
    users = user_service.list_users(conn, include_inactive=include_inactive)
    return [_to_response(user) for user in users]


@router.post("/api/users", response_model=UserResponse, status_code=201)
def create_user(
    body: UserCreateRequest,
    _: UserRow = Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> UserResponse:
    user = user_service.create(conn, body.employee_id, body.name, body.password, body.role)
    return _to_response(user)


@router.put("/api/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    body: UserUpdateRequest,
    requester: UserRow = Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> UserResponse:
    user = user_service.update(
        conn, user_id, body.name, body.password, body.role, body.is_active, requester["user_id"]
    )
    return _to_response(user)


@router.delete("/api/users/{user_id}")
def delete_user(
    user_id: str,
    requester: UserRow = Depends(require_admin),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    user = user_service.deactivate(conn, user_id, requester["user_id"])
    return {"employee_id": user["user_id"], "is_active": bool(user["is_active"])}
