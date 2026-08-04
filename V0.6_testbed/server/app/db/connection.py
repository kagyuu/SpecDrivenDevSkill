"""SQLite接続・マイグレーション実行ヘルパー (docs/P007-impl-direction/U001-foundation-auth.md U001-1).

マイグレーションの適用方式は `docs/P003-backend-spec.md` §6.4 に定義する
(`SCHEMA_MIGRATIONS` テーブルによる差分適用方式。CR-003で導入)。
"""
from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# 「そのDDLは既に適用済みである」ことを意味するSQLiteのエラーメッセージ。
# CR-003以前の方式(全件再実行)で構築済みのDBから差分適用方式へ移行する際にのみ発生しうる
# (docs/P003-backend-spec.md §6.4(3) のブートストラップ手順)。
_ALREADY_APPLIED_PATTERNS = (
    "duplicate column name",
    "already exists",
)


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


def _split_statements(sql: str) -> list[str]:
    """マイグレーションSQLを個々の文に分割する。

    ★FIXME★ 行コメント(`--`)を除去したうえで `;` で分割する単純な実装である。
    現状のマイグレーションにはトリガ(`BEGIN ... END` を含む複合文)が存在しないため
    問題ないが、将来トリガを定義する場合はこの分割処理の見直しが必要
    (docs/P003-backend-spec.md §6.4(3) の★FIXME★参照)。
    """
    without_comments = re.sub(r"--[^\n]*", "", sql)
    return [stmt.strip() for stmt in without_comments.split(";") if stmt.strip()]


def _is_already_applied_error(exc: sqlite3.OperationalError) -> bool:
    message = str(exc).lower()
    return any(pattern in message for pattern in _ALREADY_APPLIED_PATTERNS)


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS SCHEMA_MIGRATIONS ("
        "filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )


def applied_migrations(conn: sqlite3.Connection) -> set[str]:
    """適用済みマイグレーションのファイル名集合を返す(運用時の確認用)。"""
    _ensure_migrations_table(conn)
    return {row["filename"] for row in conn.execute("SELECT filename FROM SCHEMA_MIGRATIONS")}


def init_db(db_path: str | None = None) -> None:
    """未適用のマイグレーションのみを適用する(差分適用方式、docs/P003-backend-spec.md §6.4)。

    * 適用済みのファイル名は `SCHEMA_MIGRATIONS` に記録する。2回目以降の起動では
      1文も実行されないため、`ALTER TABLE ... ADD COLUMN` のような非冪等なDDLを
      含んでいても再起動で失敗しない。
    * CR-003以前の方式(毎回全件を `executescript` で再実行する)で構築済みのDBは
      `SCHEMA_MIGRATIONS` を持たないため、初回の移行時に限り 0001・0002 が
      「未適用」と判定されて再実行される。この場合に発生する「既に適用済み」を
      意味するエラーだけを読み飛ばし、**同一ファイル内の後続の文の実行は継続する**
      (CR-002の場当たり対処は `continue` でファイルの残りを読み飛ばしていた。
      その問題点は docs/P003-backend-spec.md §6.4(3) を参照)。
    """
    conn = get_connection(db_path)
    try:
        _ensure_migrations_table(conn)
        already = applied_migrations(conn)
        for migration_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if migration_file.name in already:
                continue
            sql = migration_file.read_text(encoding="utf-8")
            for statement in _split_statements(sql):
                try:
                    conn.execute(statement)
                except sqlite3.OperationalError as exc:
                    if _is_already_applied_error(exc):
                        continue  # この文だけを読み飛ばし、後続の文は実行する
                    raise
            conn.execute(
                "INSERT OR REPLACE INTO SCHEMA_MIGRATIONS (filename, applied_at) VALUES (?, ?)",
                (migration_file.name,
                 datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
            )
        conn.commit()
    finally:
        conn.close()
