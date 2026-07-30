"""ユーザーAPI。docs/02-frontend-spec.md 2章「users」、docs/03-backend-spec.md 4章「ユーザー系」対応。"""
from starlette.responses import JSONResponse

from app.deps import ApiError, error_response, require_admin
from app.repositories import users as users_repo
from app.schemas import UserCreateRequest, UserUpdateRequest


async def list_users_handler(request):
    try:
        require_admin(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    return JSONResponse(users_repo.list_users(conn))


async def create_user_handler(request):
    try:
        require_admin(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    try:
        body = await request.json()
        payload = UserCreateRequest(**body)
    except Exception:
        return error_response(400, "VALIDATION_ERROR", "リクエストボディが不正です")
    if payload.role not in ("general", "admin"):
        return error_response(400, "VALIDATION_ERROR", "role は general か admin である必要があります")
    if users_repo.employee_id_exists(conn, payload.employee_id):
        return error_response(400, "VALIDATION_ERROR", "同じ社員IDのユーザーが既に存在します")
    user = users_repo.create_user(conn, payload.employee_id, payload.name, payload.role, payload.password)
    return JSONResponse(user, status_code=201)


async def update_user_handler(request):
    try:
        require_admin(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    user_id = int(request.path_params["user_id"])
    if users_repo.get_user(conn, user_id) is None:
        return error_response(404, "NOT_FOUND", "ユーザーが存在しません")
    try:
        body = await request.json()
        payload = UserUpdateRequest(**body)
    except Exception:
        return error_response(400, "VALIDATION_ERROR", "リクエストボディが不正です")
    if payload.role not in ("general", "admin"):
        return error_response(400, "VALIDATION_ERROR", "role は general か admin である必要があります")
    user = users_repo.update_user(conn, user_id, payload.name, payload.role, payload.is_active, payload.password)
    return JSONResponse(user)


async def delete_user_handler(request):
    try:
        require_admin(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    conn = request.app.state.conn
    user_id = int(request.path_params["user_id"])
    if users_repo.get_user(conn, user_id) is None:
        return error_response(404, "NOT_FOUND", "ユーザーが存在しません")
    users_repo.deactivate_user(conn, user_id)
    return JSONResponse(None, status_code=204)
