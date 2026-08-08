"""設定の読み込み(P003 2.2 / U001-T1)。

環境変数の値はモジュール読み込み時に1回だけ解決する。
テストから差し替える場合は、モジュール属性を直接書き換える。
"""

from __future__ import annotations

import os


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


#: SQLite データベースファイルのパス(ADR-004)
DB_PATH: str = os.environ.get("DB_PATH") or "./data/app.db"

#: 無操作タイムアウト(秒)。既定8時間(ADR-005)
SESSION_IDLE_SECONDS: int = _int_env("SESSION_IDLE_SECONDS", 28800)

#: セッションの絶対有効期限(秒)。既定24時間(ADR-005)
SESSION_ABSOLUTE_SECONDS: int = _int_env("SESSION_ABSOLUTE_SECONDS", 86400)

#: 初期管理者(P003 3.6)
INITIAL_ADMIN_ID: str = os.environ.get("INITIAL_ADMIN_ID") or "admin001"
INITIAL_ADMIN_PASSWORD: str = os.environ.get("INITIAL_ADMIN_PASSWORD") or "Passw0rd!23"
