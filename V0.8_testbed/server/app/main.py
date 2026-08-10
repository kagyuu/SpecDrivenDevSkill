"""FastAPI application entry point.

U001-T1 (docs/P007-impl-direction/U001-foundation-and-auth.md) creates the
minimal application instance and a /health endpoint used to confirm the
project scaffolding works. U001-T2 adds the startup-time migration hook
(its own explicit completion condition: "uvicorn app.main:app 起動時に
マイグレーションが自動適用され、admin ユーザーが作成されることを手動確認する").
U001-T4 registers the auth router and the shared error-handling (this
task's own 実装内容: "ルーター登録"). U002-T2 adds the rooms router. U003-T3
adds the reservations and users routers (GET/POST /api/reservations and
GET /api/users/directory only - U004-T2/U005-T2 add more paths to the same
two router modules, not new modules).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from fastapi import FastAPI

from app.db.connection import get_connection
from app.db.migration import apply_pending_migrations
from app.errors import register_exception_handlers
from app.routers.auth import router as auth_router
from app.routers.reservations import router as reservations_router
from app.routers.rooms import router as rooms_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Apply any not-yet-applied migrations before serving requests.

    Uses the same DATABASE_PATH-driven connection real requests would use
    (app/db/connection.py, U001-T2), so this is not a test-only shortcut.
    """
    conn = get_connection()
    try:
        apply_pending_migrations(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="Meeting Room Reservation API", lifespan=lifespan)
register_exception_handlers(app)
app.include_router(auth_router)
app.include_router(rooms_router)
app.include_router(reservations_router)
app.include_router(users_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check used to confirm the server process started correctly."""
    return {"status": "ok"}


@app.get("/version")
def get_version() -> dict[str, str]:
    """Report the running server's version.

    P302 (docs/P302-deliver.md 5章) requires that a running module expose
    its version where feasible; this endpoint is the "GET /version" option
    the SKILL itself lists as an acceptable minor addition ("最終仕上げとして
    軽微な追加で済む場合は実装してよい") that does not change any existing
    endpoint's behavior. pyproject.toml's [project].version remains the
    single source of truth (server/pyproject.toml); this reads it back via
    importlib.metadata since the package is installed editable (`pip
    install -e .`, see server/README or docs/P302-deliver.md 7章). Falls
    back to a hardcoded copy only if the package metadata is unavailable
    (e.g. dependencies installed without `-e .`), so the endpoint never 500s
    just because of how the environment was set up.
    """
    try:
        current_version = _pkg_version("meeting-room-reservation-server")
    except PackageNotFoundError:
        current_version = "0.1.0"  # must match server/pyproject.toml [project].version
    return {"version": current_version}
