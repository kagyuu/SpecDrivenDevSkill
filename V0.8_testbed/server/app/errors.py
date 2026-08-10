"""Common error response formatting.

U001-T4 registered handlers for the auth-specific exceptions (which predate
app/exceptions.py and keep their own `InvalidCredentialsError`/
`UnauthorizedError`, plus `RequestValidationError`). U002 onward adds a
generic mechanism for app/exceptions.py's domain exceptions (ValidationError,
NotFoundError, ForbiddenError, ReservationConflictError,
SelfDeactivationForbiddenError, LastAdminProtectedError) - each of those
classes carries `code`/`message`(/`fields`) as instance attributes, so one
handler factory covers all of them instead of one bespoke handler per class.
U005-T5 adds a catch-all handler for any other (truly unexpected) exception,
logging a structured "unhandled_exception" event per
docs/P003-backend-spec.md 6章 before returning 500.

All handlers converge on the common error envelope from
docs/P002-frontend-spec.md 4章冒頭:

    {"error": {"code": "...", "message": "...", "fields": {...}}}

("fields" only for 400/VALIDATION_ERROR). Registered once, in app/main.py,
so every router (auth/rooms/reservations/users) shares these handlers
instead of each reimplementing error formatting.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import (
    ForbiddenError,
    LastAdminProtectedError,
    NotFoundError,
    ReservationConflictError,
    SelfDeactivationForbiddenError,
    ValidationError,
)
from app.logging_utils import log_event
from app.services.auth_service import InvalidCredentialsError, UnauthorizedError

# app/exceptions.py classes -> HTTP status code. Each class's own .code/
# .message/.fields attributes supply the response body (see
# _domain_error_handler below).
_DOMAIN_ERROR_STATUS: dict[type[Exception], int] = {
    ValidationError: 400,
    SelfDeactivationForbiddenError: 400,
    LastAdminProtectedError: 400,
    ForbiddenError: 403,
    NotFoundError: 404,
    ReservationConflictError: 409,
}


def _error_body(
    code: str, message: str, fields: dict[str, str] | None = None
) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if fields is not None:
        body["error"]["fields"] = fields
    return body


def _field_error_message(error: dict) -> str:
    # Our own field_validator ValueError messages (app/schemas/auth.py) are
    # already the exact user-facing text from docs/P002-frontend-spec.md
    # 3.1節; pydantic v2 wraps them as "Value error, <message>".
    if error.get("type") == "value_error":
        msg = str(error.get("msg", ""))
        prefix = "Value error, "
        return msg[len(prefix) :] if msg.startswith(prefix) else msg
    return str(error.get("msg", "入力値が不正です"))


def _make_domain_error_handler(status_code: int):
    async def handler(_: Request, exc: Exception) -> JSONResponse:
        code = getattr(exc, "code", exc.__class__.__name__)
        message = getattr(exc, "message", str(exc))
        fields = getattr(exc, "fields", None) or None
        return JSONResponse(
            status_code=status_code, content=_error_body(code, message, fields)
        )

    return handler


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidCredentialsError)
    async def _invalid_credentials_handler(
        _: Request, __: InvalidCredentialsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=_error_body(
                "INVALID_CREDENTIALS", "社員IDまたはパスワードが正しくありません"
            ),
        )

    @app.exception_handler(UnauthorizedError)
    async def _unauthorized_handler(
        _: Request, __: UnauthorizedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=_error_body("UNAUTHORIZED", "ログインが必要です"),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields: dict[str, str] = {}
        for error in exc.errors():
            loc = error.get("loc", ())
            field_name = str(loc[-1]) if loc else "_"
            fields[field_name] = _field_error_message(error)
        return JSONResponse(
            status_code=400,
            content=_error_body(
                "VALIDATION_ERROR", "入力内容を確認してください", fields
            ),
        )

    for exc_class, status_code in _DOMAIN_ERROR_STATUS.items():
        app.exception_handler(exc_class)(_make_domain_error_handler(status_code))

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # docs/P003-backend-spec.md 6章: 未処理例外(500応答)はERRORレベルで
        # event="unhandled_exception" のJSON Linesを標準出力に出力する。
        log_event(
            "ERROR",
            "unhandled_exception",
            request_id=request.headers.get("x-request-id"),
            path=request.url.path,
            error_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content=_error_body(
                "INTERNAL_SERVER_ERROR", "サーバー内部でエラーが発生しました"
            ),
        )
