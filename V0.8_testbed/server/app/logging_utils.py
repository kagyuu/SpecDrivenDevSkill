"""Structured JSON Lines logging (U005-T5, docs/P007-impl-direction/U005-user-management-and-hardening.md).

docs/P003-backend-spec.md 6章: standard output, one JSON object per line,
minimum fields timestamp/level/event/user_id(if available)/request_id.

This task's own 実装内容 requires this specifically for
event="unhandled_exception" on 500 responses (wired in app/errors.py); the
helper itself is written generically so future events (login_failed,
reservation_conflict, ...) mentioned in docs/P003-backend-spec.md 6章 can
reuse it. ★実施メモ: wiring those *other* event call sites (e.g. logging
login_failed inside app/services/auth_service.py) is not done in this task -
U005-T5's own 実装内容 only requires confirming the unhandled_exception/500
path, and its 実装してはいけないこと says "新しいAPIエンドポイント・画面の追加
は行わない"; adding logging calls throughout every existing service is a
larger change than this thin confirmation task's scope.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone


def log_event(
    level: str,
    event: str,
    *,
    request_id: str | None = None,
    user_id: str | None = None,
    **extra: object,
) -> None:
    record: dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": event,
    }
    if user_id is not None:
        record["user_id"] = user_id
    if request_id is not None:
        record["request_id"] = request_id
    record.update(extra)
    print(json.dumps(record, ensure_ascii=False), file=sys.stdout, flush=True)
