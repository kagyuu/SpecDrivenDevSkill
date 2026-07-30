"""ASGIエントリポイント。docs/03-backend-spec.md 1章「全体アーキテクチャ」対応。

FastAPIはPyPI取得不可のため、内部基盤のStarlette+Pydanticを直接使用する
(docs/06-impl-direction.md 冒頭の逸脱記録を参照)。
"""
import os

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.staticfiles import StaticFiles

CLIENT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "client"))

from app import __version__
from app.db import get_connection
from app.deps import error_response
from app.routers import auth, rooms, users, reservations
from app.seed import seed


async def health(request):
    return JSONResponse({"status": "ok", "version": __version__})


async def not_found(request, exc):
    return error_response(404, "NOT_FOUND", "リソースが見つかりません")


async def server_error(request, exc):
    return error_response(500, "INTERNAL_ERROR", "予期しないエラーが発生しました")


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/api/auth/login", auth.login, methods=["POST"]),
    Route("/api/auth/logout", auth.logout, methods=["POST"]),
    Route("/api/me", auth.me, methods=["GET"]),
    Route("/api/rooms", rooms.list_rooms_handler, methods=["GET"]),
    Route("/api/rooms", rooms.create_room_handler, methods=["POST"]),
    Route("/api/rooms/{room_id}", rooms.update_room_handler, methods=["PUT"]),
    Route("/api/rooms/{room_id}", rooms.delete_room_handler, methods=["DELETE"]),
    Route("/api/reservations", reservations.list_reservations_handler, methods=["GET"]),
    Route("/api/reservations/mine", reservations.list_mine_handler, methods=["GET"]),
    Route("/api/reservations/{reservation_id}", reservations.get_reservation_handler, methods=["GET"]),
    Route("/api/reservations", reservations.create_reservation_handler, methods=["POST"]),
    Route("/api/reservations/{reservation_id}", reservations.update_reservation_handler, methods=["PUT"]),
    Route("/api/reservations/{reservation_id}", reservations.delete_reservation_handler, methods=["DELETE"]),
    Route("/api/users", users.list_users_handler, methods=["GET"]),
    Route("/api/users", users.create_user_handler, methods=["POST"]),
    Route("/api/users/{user_id}", users.update_user_handler, methods=["PUT"]),
    Route("/api/users/{user_id}", users.delete_user_handler, methods=["DELETE"]),
]

exception_handlers = {
    404: not_found,
    500: server_error,
}


def create_app(db_path: str = "data/app.db") -> Starlette:
    application = Starlette(debug=False, routes=list(routes), exception_handlers=dict(exception_handlers))
    conn = get_connection(db_path)
    seed(conn)
    application.state.conn = conn
    # 静的フロントエンド配信(client/)。本検証ではAPIサーバーが静的ファイルも兼ねる。
    if os.path.isdir(CLIENT_DIR):
        application.mount("/", StaticFiles(directory=CLIENT_DIR, html=True), name="client")
    return application


app = create_app(os.environ.get("APP_DB_PATH", "data/app.db"))
