"""共通エラーレスポンス形式の例外ハンドラ (docs/P002-frontend-spec.md §2)."""
from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.exceptions import AppError
from app.core.logging_utils import log_event


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    body = {"error": {"code": exc.code, "message": exc.message}}
    if exc.details:
        body["error"]["details"] = exc.details
    # ★F002修正★ エラー発生時に構造化ログ(JSON Lines)を標準出力に出す (docs/P003-backend-spec.md §8)。
    log_event(
        "error", "app_error",
        method=request.method, path=request.url.path,
        status_code=exc.status_code, code=exc.code, message=exc.message,
    )
    return JSONResponse(body, status_code=exc.status_code)


EXCEPTION_HANDLERS = {
    AppError: app_error_handler,
}
