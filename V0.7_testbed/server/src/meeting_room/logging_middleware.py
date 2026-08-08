"""アクセスログ・エラーログの出力とエラー変換(P003 4.4 / ADR-010)。

1リクエスト1行のJSONを標準出力に出す。
`sid`・パスワード・セッションIDは**絶対に出力しない**。
"""

from __future__ import annotations

import json
import logging
import sys
import time
import traceback

from starlette.middleware.base import BaseHTTPMiddleware

from .errors import ApiError, internal_error_response, to_response
from .security import now_utc

LOGGER_NAME = "meeting_room.access"

_logger = logging.getLogger(LOGGER_NAME)


def configure_logging() -> None:
    """標準出力に1行1レコードで出力するハンドラを1つだけ設定する。"""
    if getattr(_logger, "_meeting_room_configured", False):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False
    _logger._meeting_room_configured = True  # type: ignore[attr-defined]


def build_log_record(
    method: str,
    path: str,
    status: int,
    duration_ms: float,
    user_id: str | None = None,
    error_code: str | None = None,
    message: str = "",
    stack: str | None = None,
) -> dict:
    """ログ1行分のレコードを組み立てる(P003 4.4 の項目)。"""
    level = "ERROR" if status >= 500 else ("WARN" if status >= 400 else "INFO")
    record = {
        "ts": now_utc(),
        "level": level,
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": round(duration_ms, 3),
        "user_id": user_id or "-",
        "error_code": error_code or "-",
        "message": message,
    }
    if status >= 500 and stack:
        record["stack"] = stack
    return record


def format_log_line(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False)


def _user_id_of(request) -> str | None:
    """`request.state.user`(`repositories` が返す dict)から `user_id` を取り出す。"""
    user = getattr(request.state, "user", None)
    if isinstance(user, dict):
        return user.get("user_id")
    if user is not None:
        return getattr(user, "user_id", None)
    return None


class LoggingMiddleware(BaseHTTPMiddleware):
    """全リクエスト横断のログ出力と、例外のAPIエラー応答への変換。"""

    async def dispatch(self, request, call_next):
        started = time.perf_counter()
        error_code: str | None = None
        message = ""
        stack: str | None = None
        try:
            response = await call_next(request)
            if response.status_code >= 400:
                error_code = getattr(request.state, "error_code", None)
        except ApiError as exc:
            response = to_response(exc)
            error_code = exc.code
            message = exc.message
        except Exception as exc:  # noqa: BLE001 — 未捕捉例外は 500 に変換する
            response = internal_error_response()
            error_code = getattr(exc, "log_error_code", "INTERNAL_ERROR")
            message = "unhandled exception"
            stack = traceback.format_exc()

        duration_ms = (time.perf_counter() - started) * 1000
        record = build_log_record(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
            user_id=_user_id_of(request),
            error_code=error_code,
            message=message,
            stack=stack,
        )
        _logger.info(format_log_line(record))
        return response
