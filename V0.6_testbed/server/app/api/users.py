"""ユーザーAPI (docs/P002-frontend-spec.md §4.14〜§4.17)."""
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.api.deps import get_conn, require_admin
from app.repositories import user_repository
from app.services import user_service


def _user_dict(user) -> dict:
    return {
        "id": user["id"],
        "employee_id": user["employee_id"],
        "name": user["name"],
        "role": user["role"],
        "is_active": bool(user["is_active"]),
    }


async def list_users(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        require_admin(request, conn)
        include_inactive_param = request.query_params.get("include_inactive", "true")
        include_inactive = include_inactive_param.lower() != "false"
        users = user_repository.list(conn, include_inactive=include_inactive)
        return JSONResponse({"users": [_user_dict(u) for u in users]})
    finally:
        conn.close()


async def create_user(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        require_admin(request, conn)
        body = await request.json()
        user = user_service.create(conn, body)
        return JSONResponse(_user_dict(user), status_code=201)
    finally:
        conn.close()


async def update_user(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        require_admin(request, conn)
        user_id = int(request.path_params["user_id"])
        body = await request.json()
        user = user_service.update(conn, user_id, body)
        return JSONResponse(_user_dict(user))
    finally:
        conn.close()


async def delete_user(request: Request) -> JSONResponse:
    conn = get_conn(request)
    try:
        current_user = require_admin(request, conn)
        user_id = int(request.path_params["user_id"])
        user = user_service.deactivate(conn, user_id, current_user["id"])
        return JSONResponse({"id": user["id"], "is_active": bool(user["is_active"])})
    finally:
        conn.close()


routes = [
    Route("/api/users", list_users, methods=["GET"]),
    Route("/api/users", create_user, methods=["POST"]),
    Route("/api/users/{user_id}", update_user, methods=["PUT"]),
    Route("/api/users/{user_id}", delete_user, methods=["DELETE"]),
]
