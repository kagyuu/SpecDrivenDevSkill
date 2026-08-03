"""FastAPI(の代替であるStarlette)アプリケーションの起点。

★deviation★ ADR-002はFastAPIを指定しているが、本サンドボックスはpypi.orgに
アクセスできずfastapiをインストールできない(docs/P101-impl-context.md参照)。
FastAPIのベースであるStarlette + Pydanticで代替する。
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.api import auth as auth_api
from app.api import reservations as reservations_api
from app.api import rooms as rooms_api
from app.api import users as users_api
from app.api.errors import EXCEPTION_HANDLERS
from app.core.logging_utils import log_event
from app.db.connection import init_db


def _read_version() -> str:
    """★P302修正★ リポジトリルートの `VERSION` ファイルからバージョン文字列を読む
    (`docs/P302-deliver.md` §5、実行モジュールからバージョンを確認できるようにする対応)。"""
    version_file = Path(__file__).resolve().parents[2] / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


APP_VERSION = _read_version()


async def health(request):
    return JSONResponse({"status": "ok", "version": APP_VERSION})


class AccessLogMiddleware(BaseHTTPMiddleware):
    """★F002修正★ 全リクエストについて構造化アクセスログ(JSON Lines)を標準出力に出す
    (docs/P003-backend-spec.md §8、docs/P202-fix-plan/fixed/F002-structured-logging-missing.md)。"""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log_event(
            "info", "http_request",
            method=request.method, path=request.url.path,
            status_code=response.status_code, duration_ms=duration_ms,
        )
        return response


@asynccontextmanager
async def lifespan(app: Starlette):
    init_db(getattr(app.state, "db_path", None))
    log_event("info", "startup", version=APP_VERSION)
    yield


def create_app(db_path: str | None = None) -> Starlette:
    routes = [
        Route("/api/health", health, methods=["GET"]),
        *auth_api.routes,
        *rooms_api.routes,
        *users_api.routes,
        *reservations_api.routes,
    ]
    middleware = [Middleware(AccessLogMiddleware)]
    app = Starlette(
        routes=routes, lifespan=lifespan, exception_handlers=dict(EXCEPTION_HANDLERS),
        middleware=middleware,
    )
    app.state.db_path = db_path
    return app


app = create_app()
