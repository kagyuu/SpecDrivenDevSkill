"""共通APIエラー。docs/P002-frontend-spec.md §2(共通エラーレスポンス形式)。"""

from __future__ import annotations


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: list[dict] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details

    def to_body(self) -> dict:
        body: dict = {"error_code": self.error_code, "message": self.message}
        if self.details:
            body["details"] = self.details
        return body
