"""パスワードハッシュ (ADR-004: bcrypt採用)。docs/P003-backend-spec.md §2.2。"""

from __future__ import annotations

import bcrypt


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
