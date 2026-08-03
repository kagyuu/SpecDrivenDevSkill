"""Service層が送出する共通例外。HTTPステータスへの変換はAPI Handler層(app/api/errors.py)の責務。

docs/P002-frontend-spec.md §2 の共通エラーコード一覧に対応する。
"""
from __future__ import annotations


class AppError(Exception):
    code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(self, message: str, details: list[dict] | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationError(AppError):
    code = "VALIDATION_ERROR"
    status_code = 400


class InvalidCredentialsError(AppError):
    code = "AUTH_INVALID_CREDENTIALS"
    status_code = 401


class AuthRequiredError(AppError):
    code = "AUTH_REQUIRED"
    status_code = 401


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status_code = 403


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class OverlapError(AppError):
    code = "RESERVATION_CONFLICT"
    status_code = 409
