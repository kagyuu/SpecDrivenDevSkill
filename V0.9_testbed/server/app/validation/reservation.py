"""予約バリデーション純粋関数。docs/P003-backend-spec.md §5.9(重複判定ロジック含む)。

DBアクセスは行わない(既存予約との突き合わせはRepository層の find_conflicting が担う)。
"""

from __future__ import annotations


def is_time_range_valid(start: str, end: str) -> bool:
    # "HH:MM" は辞書順比較が時刻順と一致するため文字列比較でよい。
    return end > start


def overlaps(new_start: str, new_end: str, existing_start: str, existing_end: str) -> bool:
    # docs/P003-backend-spec.md §5.9: 半開区間 [start, end) 同士の重なり判定。
    # 背中合わせ(new_start == existing_end または new_end == existing_start)は重複としない。
    return not (new_end <= existing_start or new_start >= existing_end)


def is_capacity_ok(expected_attendees: int | None, room_capacity: int) -> bool:
    if expected_attendees is None:
        return True
    return expected_attendees <= room_capacity
