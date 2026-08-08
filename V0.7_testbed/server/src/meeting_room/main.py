"""ASGIアプリの生成・ルーティング・静的ファイル配信(P003 4.1 / 7、ADR-010)。"""

from __future__ import annotations

from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import FileResponse, Response
from starlette.routing import Route

from . import db
from .errors import ApiError, to_response
from .logging_middleware import LoggingMiddleware, configure_logging

#: フロントエンドの静的ファイル置き場(同一オリジン配信。ADR-010)
CLIENT_DIR: Path = Path(__file__).resolve().parents[3] / "client"

#: 明示するMIME型(ESモジュールは正しいMIME型でないとブラウザが読み込まない。P003 7章)
MIME_TYPES = {
    ".js": "text/javascript",
    ".css": "text/css",
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def _media_type(path: Path) -> str:
    return MIME_TYPES.get(path.suffix.lower(), "application/octet-stream")


def _safe_client_file(relative: str) -> Path | None:
    """`client/` の外に出るパスを拒否する(`..` を含むパスは 404)。"""
    if ".." in relative.split("/"):
        return None
    candidate = (CLIENT_DIR / relative).resolve()
    try:
        candidate.relative_to(CLIENT_DIR.resolve())
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def _index_response() -> Response:
    index = CLIENT_DIR / "index.html"
    if not index.is_file():
        raise ApiError(404, "NOT_FOUND", "対象のデータが見つかりません。削除された可能性があります。")
    return FileResponse(index, media_type=MIME_TYPES[".html"])


async def index_handler(request: Request) -> Response:
    return _index_response()


async def static_handler(request: Request) -> Response:
    relative = request.url.path.lstrip("/")
    target = _safe_client_file(relative)
    if target is None:
        raise ApiError(404, "NOT_FOUND", "対象のデータが見つかりません。削除された可能性があります。")
    return FileResponse(target, media_type=_media_type(target))


async def fallback_handler(request: Request) -> Response:
    """`/api/` 以外の未知パスは `index.html` を返す(ハッシュルーティングの保険。P003 7章)。"""
    path = request.url.path
    if path.startswith("/api/") or path == "/api":
        raise ApiError(404, "NOT_FOUND", "対象のデータが見つかりません。削除された可能性があります。")
    return _index_response()


def api_routes() -> list[Route]:
    """`/api/*` のルート定義。スプリントの進行に合わせてここに追加する。"""
    from .handlers import auth_handlers, reservation_handlers, room_handlers, user_handlers

    return [
        # --- 認証(API-01〜API-03。U001-T4) ---
        # `/api/auth/login` のみ認証不要。他は各ハンドラが `require_login` を通す(P003 4.3)
        Route("/api/auth/login", auth_handlers.login, methods=["POST"]),
        Route("/api/auth/logout", auth_handlers.logout, methods=["POST"]),
        Route("/api/me", auth_handlers.me, methods=["GET"]),
        # --- 会議室(API-04〜API-07。U002-T2) ---
        Route("/api/rooms", room_handlers.list_rooms, methods=["GET"]),
        Route("/api/rooms", room_handlers.create_room, methods=["POST"]),
        Route("/api/rooms/{room_id}", room_handlers.update_room, methods=["PUT"]),
        Route("/api/rooms/{room_id}", room_handlers.deactivate_room, methods=["DELETE"]),
        # --- ユーザー(API-08〜API-11。U002-T3) ---
        Route("/api/users", user_handlers.list_users, methods=["GET"]),
        Route("/api/users", user_handlers.create_user, methods=["POST"]),
        Route("/api/users/{user_id}", user_handlers.update_user, methods=["PUT"]),
        Route("/api/users/{user_id}", user_handlers.deactivate_user, methods=["DELETE"]),
        # --- 予約(API-12〜API-17。U003-T3 / U003-T4) ---
        Route("/api/reservations", reservation_handlers.list_reservations, methods=["GET"]),
        Route("/api/reservations", reservation_handlers.create_reservation, methods=["POST"]),
        # `/mine` は `/{reservation_id}` より**先に**登録する(P003 6.4。登録順に最初にマッチする)
        Route(
            "/api/reservations/mine",
            reservation_handlers.list_my_reservations,
            methods=["GET"],
        ),
        Route(
            "/api/reservations/{reservation_id}",
            reservation_handlers.get_reservation,
            methods=["GET"],
        ),
        Route(
            "/api/reservations/{reservation_id}",
            reservation_handlers.update_reservation,
            methods=["PUT"],
        ),
        Route(
            "/api/reservations/{reservation_id}",
            reservation_handlers.delete_reservation,
            methods=["DELETE"],
        ),
    ]


def build_routes() -> list[Route]:
    return [
        *api_routes(),
        Route("/", index_handler, methods=["GET"]),
        Route("/src/{path:path}", static_handler, methods=["GET"]),
        Route("/assets/{path:path}", static_handler, methods=["GET"]),
        Route("/{path:path}", fallback_handler, methods=["GET"]),
    ]


async def api_error_handler(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, ApiError)
    # アクセスログに `error_code` を残すためミドルウェアへ伝える(P003 4.4)
    request.state.error_code = exc.code
    return to_response(exc)


def create_app(db_path: str | None = None, run_migrations: bool = True) -> Starlette:
    """ASGIアプリを生成する。生成直後(リクエスト受付前)にマイグレーションを1回適用する。"""
    configure_logging()
    if run_migrations:
        db.init_wal(db_path)
        db.apply_migrations(db_path)
        db.seed_initial_admin(db_path)

    app = Starlette(
        routes=build_routes(),
        middleware=[Middleware(LoggingMiddleware)],
        exception_handlers={ApiError: api_error_handler},
    )
    app.state.db_path = db_path
    return app


def __getattr__(name: str):
    # `uvicorn meeting_room.main:app` のための遅延生成(import 時にDBを触らない)
    if name == "app":
        return create_app()
    raise AttributeError(name)
