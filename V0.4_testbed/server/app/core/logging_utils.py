"""構造化ログ(JSON Lines)ユーティリティ (docs/P003-backend-spec.md §8).

★F002修正★ アプリケーションは標準出力に構造化ログ(JSON Lines、1行1JSON)を出力する。
アクセスログ(リクエストごと)とエラーログ(`AppError`発生時)の両方をこのモジュール経由で出力する。
標準出力からのログ収集基盤への転送はデプロイ環境側の責務(`docs/P003-backend-spec.md` §8)であり、
本モジュールは標準出力に書き出すところまでを担う。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


def log_event(level: str, event: str, **fields) -> None:
    """1行1JSON形式で標準出力にログを出力する。"""
    record = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": level,
        "event": event,
    }
    record.update(fields)
    print(json.dumps(record, ensure_ascii=False), file=sys.stdout, flush=True)
