"""Auth Service layer (U001-T3, docs/P007-impl-direction/U001-foundation-and-auth.md).

Implements docs/P003-backend-spec.md 4.1〜4.3節 login/logout/get_current_user
business logic, on top of app/repositories/user_repository.py and
app/repositories/session_repository.py (both already implemented) and
app/security/password.py (hash/verify, already implemented).

Per this task's own 実装してはいけないこと, this layer never raises
fastapi.HTTPException directly - it raises the module-level exception
classes below, and the Router/Handler layer (U001-T4) is responsible for
mapping them to HTTP status codes.
"""

from __future__ import annotations

import secrets
import sqlite3

from app.logging_utils import log_event
from app.repositories import session_repository, user_repository
from app.repositories.session_repository import SessionRow
from app.repositories.user_repository import UserRow
from app.security.password import verify_password

_SESSION_ID_BYTES = 32  # docs/P003-backend-spec.md 1.2節: 32バイトのURL-safe乱数


class InvalidCredentialsError(Exception):
    """Employee ID does not exist (or is inactive), or the password is wrong.

    Deliberately raised for both cases (unknown user vs. wrong password) so
    the API response cannot be used to enumerate valid employee IDs.
    """


class UnauthorizedError(Exception):
    """No session_id, or session_id does not map to a valid, unexpired
    session, or the session's user has since been deactivated."""


def login(conn: sqlite3.Connection, employee_id: str, password: str) -> SessionRow:
    """Authenticate and create a new session.

    docs/P003-backend-spec.md 4.1節 steps 1-3 (Set-Cookie response building,
    step 4, is the Router layer's job - U001-T4).
    """
    # P202 F004 (docs/P202-fix-plan/F004-login-failed-logging.md):
    # docs/P003-backend-spec.md 6章 requires a WARNING-level "login_failed"
    # event. user_id is included only "取得できる場合" (when obtainable) -
    # for an unknown employee_id there is no real user to attribute the
    # attempt to, so it is omitted rather than logging the (possibly
    # fabricated) attempted employee_id as if it were a real user_id.
    user: UserRow | None = user_repository.find_active_by_id(conn, employee_id)
    if user is None:
        log_event("WARNING", "login_failed")
        raise InvalidCredentialsError()
    if not verify_password(password, user["password_hash"]):
        log_event("WARNING", "login_failed", user_id=user["user_id"])
        raise InvalidCredentialsError()

    session_id = secrets.token_urlsafe(_SESSION_ID_BYTES)
    return session_repository.create(conn, session_id, user["user_id"])


def get_current_user(conn: sqlite3.Connection, session_id: str | None) -> UserRow:
    """Resolve the current user from a session_id (docs/P003-backend-spec.md 4.3節).

    A session whose user has been deactivated after the session was created
    is treated the same as an invalid session (401), not as "user data
    changed" - docs/P003-backend-spec.md 1.2節's "無効化時に全セッション削除"
    means this path should be unreachable in practice, but this check is
    kept as defense in depth in case a session outlives its user for any
    other reason.
    """
    if not session_id:
        raise UnauthorizedError()

    session = session_repository.find_valid(conn, session_id)
    if session is None:
        raise UnauthorizedError()

    user = user_repository.find_active_by_id(conn, session["user_id"])
    if user is None:
        raise UnauthorizedError()

    return user


def logout(conn: sqlite3.Connection, session_id: str | None) -> None:
    """Delete a session. Idempotent: no error for a missing/None session_id
    (docs/P003-backend-spec.md 4.2節)."""
    if session_id:
        session_repository.delete(conn, session_id)
