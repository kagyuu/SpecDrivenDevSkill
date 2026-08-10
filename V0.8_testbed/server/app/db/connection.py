"""SQLite connection helpers (U001-T2, docs/P007-impl-direction/U001-foundation-and-auth.md).

DATABASE_PATH (docs/P003-backend-spec.md 4.1節) controls where the SQLite
file lives. Defaults to server/data/app.db (relative to the current working
directory) when unset.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def get_database_path() -> Path:
    raw = os.environ.get("DATABASE_PATH", "data/app.db")
    return Path(raw)


def get_connection(database_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys enabled.

    Creates the parent directory of the database file if it does not exist
    yet (skipped for the special ":memory:" path used by tests).
    """
    path = Path(database_path) if database_path is not None else get_database_path()
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False (P202 F001, docs/P202-fix-plan/F001-sqlite-thread-safety.md):
    # FastAPI dispatches this function's caller (app/dependencies.py's get_db,
    # a sync generator dependency) via AnyIO's threadpool. Within a single
    # request, sqlite3's default check_same_thread=True does not guarantee
    # that the connection is opened and later used from the same OS thread -
    # under concurrent requests this intermittently raised
    # "SQLite objects created in a thread can only be used in that same
    # thread" (sqlite3.ProgrammingError), surfacing as 500s
    # (docs/test-records/20260809-1500-test-record.md T009 and
    # docs/test-records/20260809-1900-test-record.md A001/A003/A004/A006/A010).
    # This is safe here because each connection is created fresh per request
    # (get_db()) and never shared across concurrent requests - only ever used
    # sequentially within one request's lifecycle, possibly by different
    # threads at different points. Cross-request write safety is unrelated
    # and already handled at the SQLite file-lock level (BEGIN IMMEDIATE,
    # docs/ADR.md ADR-004), not by check_same_thread.
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn
