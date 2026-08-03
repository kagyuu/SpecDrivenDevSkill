"""日付・時刻のパース・比較を行う純粋関数。

U003-1: parse_date, parse_time, is_future_or_today
U004-1: is_upcoming
"""
from __future__ import annotations

from datetime import date, datetime


def parse_date(value: str) -> date:
    """`YYYY-MM-DD` 形式を検証しパースする。不正形式は ValueError。"""
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value: str) -> tuple[int, int]:
    """`HH:MM` 形式を検証しパースする。不正形式は ValueError。"""
    parsed = datetime.strptime(value, "%H:%M")
    return parsed.hour, parsed.minute


def is_future_or_today(value: str, today: str | None = None) -> bool:
    """本日以降かを判定する (docs/P002-frontend-spec.md §3 S03「過去日付不可」)。"""
    target = parse_date(value)
    base = parse_date(today) if today else date.today()
    return target >= base


def is_upcoming(value: str, today: str | None = None) -> bool:
    """`date >= today` ならTrue(当日を含む、時刻は考慮しない) (docs/P003-backend-spec.md §7.9)。"""
    return is_future_or_today(value, today)
