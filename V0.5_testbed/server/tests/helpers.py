"""テスト共通ヘルパー: メモリDBの初期化とシードデータ投入。"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.password import hash_password

MIGRATIONS_DIR = Path(__file__).parent.parent / "app" / "db" / "migrations"


def make_test_conn() -> sqlite3.Connection:
    """メモリ上にマイグレーション適用済みのSQLite接続を作成する。"""
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        conn.executescript(migration_file.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def seed_user(conn: sqlite3.Connection, employee_id: str, password: str, name: str = "テストユーザー",
              role: str = "general", is_active: bool = True) -> int:
    from app.repositories import user_repository

    row = user_repository.insert(conn, employee_id, name, hash_password(password), role, is_active)
    return row["id"]


def seed_room(conn: sqlite3.Connection, name: str = "会議室A", capacity: int = 6,
              equipment: str = "", is_active: bool = True, description: str | None = None) -> int:
    from app.repositories import room_repository

    row = room_repository.insert(conn, name, capacity, equipment, is_active, description)
    return row["id"]
