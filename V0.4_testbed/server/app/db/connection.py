"""SQLite接続・マイグレーション実行ヘルパー (docs/P007-impl-direction/U001-foundation-auth.md U001-1)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _default_db_path() -> str:
    return os.environ.get("DATABASE_PATH", "server/data/app.db")


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with foreign keys enabled and Row factory set."""
    path = db_path or _default_db_path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None)  # autocommit; BEGIN IMMEDIATE controls txns explicitly (ADR-006)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | None = None) -> None:
    """未適用のマイグレーションを適用する。既に適用済みでも冪等に成功する。"""
    conn = get_connection(db_path)
    try:
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for migration_file in migration_files:
            sql = migration_file.read_text(encoding="utf-8")
            conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()
