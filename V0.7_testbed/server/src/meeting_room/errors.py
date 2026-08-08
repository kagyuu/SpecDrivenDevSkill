"""APIエラー例外とエラーレスポンス変換(P002 5.2 / P003 4.4)。"""

from __future__ import annotations

import json
import typing

from starlette.responses import Response

JSON_MEDIA_TYPE = "application/json; charset=utf-8"


class JsonResponse(Response):
    """日本語をエスケープせずに返すJSONレスポンス(`Content-Type` はP002 5.1のとおり)。"""

    media_type = JSON_MEDIA_TYPE

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(content, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def json_response(content: typing.Any, status_code: int = 200) -> JsonResponse:
    return JsonResponse(content, status_code=status_code)


class ApiError(Exception):
    """業務・入力エラーを表す例外。`services` / `handlers` はこれを送出する。"""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        details: list | None = None,
        extra: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details
        self.extra = extra

    def to_dict(self) -> dict:
        error: dict = {"code": self.code, "message": self.message}
        if self.code == "VALIDATION_ERROR" and self.details is not None:
            error["details"] = self.details
        if self.extra:
            error.update(self.extra)
        return {"error": error}


def to_response(err: ApiError) -> JsonResponse:
    """`ApiError` を P002 5.2 の共通形式のレスポンスに変換する。"""
    return json_response(err.to_dict(), status_code=err.status)


def internal_error_response() -> JsonResponse:
    """想定外の例外に対する 500 応答。内部情報(スタック・SQL・パス)は含めない。"""
    return to_response(
        ApiError(
            500,
            "INTERNAL_ERROR",
            "システムエラーが発生しました。時間をおいて再度お試しください。",
        )
    )


def validation_error(details: list[dict]) -> ApiError:
    return ApiError(400, "VALIDATION_ERROR", "入力内容に誤りがあります。", details=details)
