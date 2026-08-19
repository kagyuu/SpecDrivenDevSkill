"""マイグレーションランナー。

docs/P003-backend-spec.md §4 の方式に対応する:
- schema_migrations テーブルで適用済みバージョンを記録する差分適用方式。
- 未適用のマイグレーションファイルのみを実行するため、同じマイグレーションが
  2回以上実行されることはない(冪等)。
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

_FILENAME_RE = re.compile(r"^(\d+)_.*\.sql$")


def _ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def _applied_versions(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def _discover_migrations(migrations_dir: str | Path) -> list[tuple[int, Path]]:
    directory = Path(migrations_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"migrations directory not found: {migrations_dir}")

    found: list[tuple[int, Path]] = []
    for path in directory.iterdir():
        match = _FILENAME_RE.match(path.name)
        if not match:
            continue
        found.append((int(match.group(1)), path))
    found.sort(key=lambda item: item[0])
    return found


def run_migrations(
    conn: sqlite3.Connection,
    migrations_dir: str | Path,
    applied_at: str,
) -> list[int]:
    """未適用のマイグレーションを順に適用し、適用したバージョン番号のリストを返す。

    ``applied_at`` は呼び出し元が計算した現在時刻の文字列を渡す(Repository層/
    ユーティリティ層は内部でシステム時計を呼び出さない、docs/P003-backend-spec.md
    §6 の方針をこのモジュールにも適用する)。
    """
    _ensure_schema_migrations_table(conn)
    already_applied = _applied_versions(conn)

    newly_applied: list[int] = []
    for version, path in _discover_migrations(migrations_dir):
        if version in already_applied:
            continue
        sql = path.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (version, applied_at),
        )
        conn.commit()
        newly_applied.append(version)

    return newly_applied
