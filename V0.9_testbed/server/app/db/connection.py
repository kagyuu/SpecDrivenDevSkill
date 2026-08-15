"""SQLite接続の取得。DATABASE_PATH 環境変数からパスを決定する(docs/P003-backend-spec.md §0)。"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DATABASE_PATH = "./data/app.db"


def get_database_path() -> str:
    return os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH)


def get_connection(database_path: str | None = None) -> sqlite3.Connection:
    path = database_path or get_database_path()
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    # ※P202 F003にもとづき修正: FastAPI/Starletteは同期の依存関数・エンドポイントを
    # スレッドプール上で実行するが、1リクエスト内でも「接続の生成」「利用」「破棄」が
    # 必ずしも同一のワーカースレッドで行われる保証はない。sqlite3の既定(check_same_thread=True)
    # のままだと、生成時と異なるスレッドで接続を使った際に
    # `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that
    # same thread.` が発生する(docs/test-records/20260811-0500-test-record.md T006、
    # docs/P202-fix-plan/fixed/F003-sqlite-thread-safety.md 参照)。
    # 本アプリはリクエストごとに新しい接続を開いてリクエスト内で完結させる設計であり、
    # 1つの接続オブジェクトが複数スレッドから「同時に」使われることは無い(生成したスレッドと
    # 利用するスレッドが異なるだけ)。このためcheck_same_thread=Falseによる回避は安全と判断した。
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
