"""SQLite接続・トランザクション・差分適用マイグレーション(P003 3.5 / 4.5、ADR-004 / ADR-009)。"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from . import config

#: マイグレーションSQLの既定の配置先(`server/migrations/`)
MIGRATIONS_DIR: Path = Path(__file__).resolve().parents[2] / "migrations"


def _resolve_db_path(db_path: str | None) -> str:
    return db_path if db_path is not None else config.DB_PATH


def connect(db_path: str | None = None) -> sqlite3.Connection:
    """接続を1つ開く。ADR-004 の固定設定を必ず適用する。"""
    path = _resolve_db_path(db_path)
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path, timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_wal(db_path: str | None = None) -> None:
    """起動時に1回だけ WAL モードを設定する(P003 4.5)。"""
    conn = connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    finally:
        conn.close()


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """`BEGIN IMMEDIATE` で開始し、正常終了でCOMMIT、例外でROLLBACKする(P003 4.5 / 5.3)。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")


def split_sql_statements(script: str) -> list[str]:
    """`;` 区切りで文単位に分割する。空文は読み飛ばす(`executescript()` は使わない。ADR-009)。"""
    statements: list[str] = []
    for chunk in script.split(";"):
        # 行コメントだけの断片を除いて空かどうかを判定する
        meaningful = "\n".join(
            line for line in chunk.splitlines() if not line.strip().startswith("--")
        )
        if meaningful.strip():
            statements.append(chunk.strip())
    return statements


def _migration_files(migrations_dir: Path) -> list[Path]:
    if not migrations_dir.is_dir():
        return []
    return sorted(migrations_dir.glob("*.sql"), key=lambda p: p.name)


def apply_migrations(
    db_path: str | None = None, migrations_dir: str | Path | None = None
) -> list[str]:
    """未適用のマイグレーションだけを適用する(P003 3.5 の手順1〜4)。

    戻り値は本呼び出しで適用した version(ファイル名)のリスト。
    """
    directory = Path(migrations_dir) if migrations_dir is not None else MIGRATIONS_DIR
    conn = connect(db_path)
    applied_now: list[str] = []
    try:
        # 手順1: 記録テーブル(この1文のみ常に実行してよい)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        # 手順2: 適用済み集合
        applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations")}
        # 手順3: ファイル名昇順・未適用のみ
        for path in _migration_files(directory):
            version = path.name
            if version in applied:
                continue
            script = path.read_text(encoding="utf-8")
            # 手順4: 1ファイル = 1トランザクション。文単位で実行し、最後に記録をINSERTする
            with transaction(conn):
                for statement in split_sql_statements(script):
                    conn.execute(statement)
                conn.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (version, _now_utc()),
                )
            applied_now.append(version)
    finally:
        conn.close()
    return applied_now


def _now_utc() -> str:
    # security.now_utc() と同じ形式。循環インポートを避けるためここでは局所定義する。
    from .security import now_utc

    return now_utc()


def seed_initial_admin(db_path: str | None = None) -> bool:
    """有効な管理者が1人も存在しない場合にのみ初期管理者を1件INSERTする(P003 3.6。冪等)。

    戻り値: INSERTしたら True、何もしなければ False。
    """
    from .security import hash_password, now_utc

    conn = connect(db_path)
    try:
        with transaction(conn):
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM users WHERE role = 'admin' AND is_active = 1"
            ).fetchone()
            if row["c"] > 0:
                return False
            now = now_utc()
            conn.execute(
                "INSERT INTO users(user_id, name, password_hash, role, is_active,"
                " created_at, updated_at) VALUES (?, ?, ?, 'admin', 1, ?, ?)",
                (
                    config.INITIAL_ADMIN_ID,
                    "初期管理者",
                    hash_password(config.INITIAL_ADMIN_PASSWORD),
                    now,
                    now,
                ),
            )
            return True
    finally:
        conn.close()
