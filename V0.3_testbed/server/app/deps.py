"""共通の認証・認可依存関数とエラーレスポンスヘルパー。"""
from starlette.responses import JSONResponse

from app.security import get_session_user


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status_code)


def require_login(request):
    conn = request.app.state.conn
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise ApiError(401, "UNAUTHORIZED", "ログインが必要です")
    user = get_session_user(conn, session_id)
    if user is None:
        raise ApiError(401, "UNAUTHORIZED", "セッションが無効です")
    return user


def require_admin(request):
    user = require_login(request)
    if user["role"] != "admin":
        raise ApiError(403, "FORBIDDEN", "管理者のみ実行できます")
    return user
