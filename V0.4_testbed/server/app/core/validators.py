"""入力バリデーション純粋関数。

U001-2: validate_employee_id, validate_password_policy
U002-1: validate_room_name, validate_capacity, validate_user_name, validate_role
U003-2: validate_time_range, validate_title, validate_notes
"""
from __future__ import annotations

import re

_EMPLOYEE_ID_RE = re.compile(r"^[A-Za-z0-9]{1,20}$")


def validate_employee_id(value: str) -> bool:
    """半角英数字1〜20文字 (docs/P002-frontend-spec.md §3 S01)."""
    if not isinstance(value, str):
        return False
    return bool(_EMPLOYEE_ID_RE.match(value))


def validate_password_policy(value: str) -> bool:
    """8文字以上、英字・数字をそれぞれ1文字以上含む (docs/P002-frontend-spec.md §3 S07)."""
    if not isinstance(value, str) or len(value) < 8:
        return False
    has_alpha = any(c.isalpha() for c in value)
    has_digit = any(c.isdigit() for c in value)
    return has_alpha and has_digit


# --- U002-1: 会議室・ユーザー入力項目 ---

def validate_room_name(value: str) -> bool:
    """1〜50文字 (docs/P002-frontend-spec.md §3 S06)."""
    return isinstance(value, str) and 1 <= len(value) <= 50


def validate_capacity(value) -> bool:
    """1以上の整数 (docs/P002-frontend-spec.md §3 S06)."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def validate_user_name(value: str) -> bool:
    """1〜50文字 (docs/P002-frontend-spec.md §3 S07)."""
    return isinstance(value, str) and 1 <= len(value) <= 50


def validate_role(value: str) -> bool:
    """general または admin (docs/P002-frontend-spec.md §3 S07)."""
    return value in ("general", "admin")


# --- U003-2: 予約作成のバリデーション ---

def validate_time_range(start: str, end: str) -> bool:
    """end > start であること (等しい・逆転はFalse) (docs/P002-frontend-spec.md §3 S03)."""
    return end > start


def validate_title(value: str) -> bool:
    """1〜100文字 (docs/P002-frontend-spec.md §3 S03)."""
    return isinstance(value, str) and 1 <= len(value) <= 100


def validate_notes(value) -> bool:
    """空またはNoneを許容、最大500文字 (docs/P002-frontend-spec.md §3 S03)."""
    if value is None:
        return True
    return isinstance(value, str) and len(value) <= 500
