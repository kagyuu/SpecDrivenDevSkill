"""共通フィクスチャ: マイグレーション適用済みの一時DB接続。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db.migrate import run_migrations

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


@pytest.fixture
def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    run_migrations(conn, MIGRATIONS_DIR, applied_at="2026-08-11T00:00:00+00:00")
    yield conn
    conn.close()
