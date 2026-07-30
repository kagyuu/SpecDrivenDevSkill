"""重複判定・予約入力バリデーションの純粋関数。docs/03-backend-spec.md 4章「予約系」対応。"""
import re
from datetime import datetime

TIME_RE = re.compile(r"^\d{2}:\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def time_ranges_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    """docs/03-backend-spec.md: NOT (end_time <= 対象.start_time OR start_time >= 対象.end_time) を満たせば重複。"""
    return not (end1 <= start2 or start1 >= end2)


def validate_reservation_input(payload: dict) -> list[str]:
    errors: list[str] = []

    date = payload.get("date")
    start_time = payload.get("start_time")
    end_time = payload.get("end_time")
    subject = payload.get("subject")
    notes = payload.get("notes") or ""

    if not date or not isinstance(date, str) or not DATE_RE.match(date):
        errors.append("date は YYYY-MM-DD 形式で必須です")
    if not start_time or not isinstance(start_time, str) or not TIME_RE.match(start_time):
        errors.append("start_time は HH:MM 形式で必須です")
    if not end_time or not isinstance(end_time, str) or not TIME_RE.match(end_time):
        errors.append("end_time は HH:MM 形式で必須です")
    if (
        start_time
        and end_time
        and TIME_RE.match(start_time or "")
        and TIME_RE.match(end_time or "")
        and end_time <= start_time
    ):
        errors.append("end_time は start_time より後である必要があります")

    if not subject or not isinstance(subject, str) or len(subject) < 1:
        errors.append("subject は必須です")
    elif len(subject) > 100:
        errors.append("subject は100文字以内である必要があります")

    if notes and len(notes) > 500:
        errors.append("notes は500文字以内である必要があります")

    return errors
