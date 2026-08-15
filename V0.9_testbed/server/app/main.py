"""FastAPIアプリのエントリポイント。起動時にマイグレーションを実行する(docs/P003-backend-spec.md §4)。"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.api.errors import ApiError
from app.api.routers import auth as auth_router
from app.api.routers import reservations as reservations_router
from app.api.routers import rooms as rooms_router
from app.api.routers import users as users_router
from app.db.connection import get_connection
from app.db.migrate import run_migrations

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("app")

MIGRATIONS_DIR = "migrations"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    conn = get_connection()
    try:
        applied = run_migrations(conn, MIGRATIONS_DIR, applied_at=datetime.now(timezone.utc).isoformat())
        logger.info('{"event": "migrations_applied", "versions": %s}', applied)
    finally:
        conn.close()
    yield


app = FastAPI(title="Meeting Room Reservation API", lifespan=lifespan)

app.include_router(auth_router.router)
app.include_router(rooms_router.router)
app.include_router(reservations_router.router)
app.include_router(users_router.router)


@app.exception_handler(ApiError)
async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.to_body())


async def _extract_error_code(response: Response) -> tuple[Response, str | None]:
    """エラーレスポンス(status_code >= 400)のボディから error_code を取り出す。

    ※P202 F005にもとづき追加。docs/P009-acceptance-direction/A009-structured-logging.md の
    「失敗時はerror_codeに相当するフィールドをログに含める」という期待に応えるための追加。
    レスポンスボディはストリーミング(body_iterator)であり一度しか読めないため、読み取った
    バイト列から新しいイテレータを作り直してクライアントへの送信に影響しないようにする。
    """
    if response.status_code < 400 or not hasattr(response, "body_iterator"):
        return response, None

    body_bytes = b"".join([section async for section in response.body_iterator])

    async def _replay():
        yield body_bytes

    response.body_iterator = _replay()

    try:
        error_code = json.loads(body_bytes.decode("utf-8")).get("error_code")
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
        error_code = None
    return response, error_code


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    response = await call_next(request)
    response, error_code = await _extract_error_code(response)

    log_entry = {
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if error_code:
        log_entry["error_code"] = error_code

    logger.info(json.dumps(log_entry, ensure_ascii=False))
    return response
