"""認証系API。docs/02-frontend-spec.md 2章「POST /api/auth/login」等、docs/03-backend-spec.md 3章対応。"""
from starlette.responses import JSONResponse

from app.deps import ApiError, error_response, require_login
from app.repositories.users import get_user_by_employee_id, row_to_public_dict
from app.schemas import LoginRequest
from app.security import create_session, delete_session, verify_password


async def login(request):
    conn = request.app.state.conn
    try:
        body = await request.json()
        payload = LoginRequest(**body)
    except Exception:
        return error_response(400, "VALIDATION_ERROR", "リクエストボディが不正です")

    row = get_user_by_employee_id(conn, payload.employee_id)
    if row is None or not row["is_active"] or not verify_password(payload.password, row["password_hash"]):
        return error_response(401, "UNAUTHORIZED", "ユーザーIDまたはパスワードが違います")

    session_id = create_session(conn, row["id"])
    user_public = row_to_public_dict(row)
    response = JSONResponse({"user": user_public})
    response.set_cookie("session_id", session_id, httponly=True, samesite="lax")
    return response


async def logout(request):
    conn = request.app.state.conn
    try:
        user = require_login(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    delete_session(conn, request.cookies.get("session_id"))
    response = JSONResponse(None, status_code=204)
    response.delete_cookie("session_id")
    return response


async def me(request):
    try:
        user = require_login(request)
    except ApiError as e:
        return error_response(e.status_code, e.code, e.message)
    return JSONResponse(row_to_public_dict(user))
