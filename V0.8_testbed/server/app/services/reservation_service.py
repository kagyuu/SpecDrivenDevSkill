"""Reservation Service layer.

U003-T2: create_reservation/list_reservations/list_participant_candidates,
validation per docs/P002-frontend-spec.md 3.3節/4.7節. Uses
app/repositories/reservation_repository.py's begin_immediate_transaction +
find_overlapping (U003-T1) to detect conflicts under concurrent requests -
see that module's own docstring for the locking design.

U004-T1 adds get_reservation/update_reservation/cancel_reservation/
list_my_reservations, per docs/P002-frontend-spec.md 3.4〜3.5節/4.8〜4.9.2節.
"""

from __future__ import annotations

import sqlite3

from app.exceptions import (
    ForbiddenError,
    NotFoundError,
    ReservationConflictError,
    ValidationError,
)
from app.repositories import reservation_repository, room_repository, user_repository
from app.repositories.reservation_repository import ReservationListItem
from app.repositories.user_repository import DirectoryEntry

_TITLE_MAX_LENGTH = 100
_NOTES_MAX_LENGTH = 500
_MEETING_URL_MAX_LENGTH = 500  # CR-001 (docs/P901-cr-direction/CR-001.md)


def _combine(date: str, time: str) -> str:
    return f"{date}T{time}:00"


def _split_datetime(start_datetime: str, end_datetime: str) -> tuple[str, str, str]:
    return start_datetime[:10], start_datetime[11:16], end_datetime[11:16]


def _is_admin(conn: sqlite3.Connection, user_id: str) -> bool:
    user = user_repository.find_by_id(conn, user_id)
    return user is not None and user["role"] == "admin"


def _normalize_meeting_url(meeting_url: str | None) -> str | None:
    """CR-001 (docs/P903-cr-records/CR-001.md「対処内容」節): 未指定・空文字列・
    null はすべて「値なし」として None に統一する(DBにはNULLを保存し、空文字列
    をそのまま保存しない)。"""
    if meeting_url is None or meeting_url == "":
        return None
    return meeting_url


def _validate(
    title: str,
    notes: str | None,
    start_time: str,
    end_time: str,
    attendee_count: int | None,
    capacity: int,
    meeting_url: str | None = None,
) -> None:
    fields: dict[str, str] = {}

    if not title or not title.strip():
        fields["title"] = "件名を入力してください"
    elif len(title) > _TITLE_MAX_LENGTH:
        fields["title"] = "件名は100文字以内で入力してください"

    if notes is not None and len(notes) > _NOTES_MAX_LENGTH:
        fields["notes"] = "備考は500文字以内で入力してください"

    if end_time <= start_time:
        fields["end_time"] = "終了時刻は開始時刻より後にしてください"

    if attendee_count is not None:
        if attendee_count < 1:
            fields["attendee_count"] = "参加予定人数は1以上の整数で入力してください"
        elif attendee_count > capacity:
            fields["attendee_count"] = f"選択した会議室の収容人数({capacity}名)を超えています"

    # CR-001 (docs/P002-frontend-spec.md 3.3節, docs/P003-backend-spec.md
    # 4.6〜4.9.2節): 値が指定されている場合のみ検証する。
    if meeting_url:
        if not (meeting_url.startswith("http://") or meeting_url.startswith("https://")):
            fields["meeting_url"] = "オンライン会議URLは http:// または https:// で始めてください"
        elif len(meeting_url) > _MEETING_URL_MAX_LENGTH:
            fields["meeting_url"] = "オンライン会議URLは500文字以内で入力してください"

    if fields:
        raise ValidationError(fields=fields)


def create_reservation(
    conn: sqlite3.Connection,
    room_id: int,
    date: str,
    start_time: str,
    end_time: str,
    title: str,
    participant_user_ids: list[str],
    attendee_count: int | None,
    notes: str | None,
    organizer_user_id: str,
    meeting_url: str | None = None,
) -> dict:
    """Returns the created reservation in the docs/P002-frontend-spec.md 4.9節
    detail shape (4.7節: "レスポンス201: 作成された予約の詳細(4.9節と同形式)").
    U004-T1 has not added reservation_repository.find_by_id yet, so this
    builds the response from data already at hand rather than re-querying -
    at creation time the requester is always the organizer, so `editable`
    is trivially True.

    meeting_url: CR-001 (docs/P901-cr-direction/CR-001.md, U003-T7).
    """
    room = room_repository.find_by_id(conn, room_id)
    if room is None or not room["is_active"]:
        raise NotFoundError("指定した会議室が見つかりません")

    meeting_url = _normalize_meeting_url(meeting_url)
    _validate(title, notes, start_time, end_time, attendee_count, room["capacity"], meeting_url)

    start_datetime = _combine(date, start_time)
    end_datetime = _combine(date, end_time)

    with reservation_repository.begin_immediate_transaction(conn):
        if reservation_repository.find_overlapping(conn, room_id, start_datetime, end_datetime):
            raise ReservationConflictError()
        reservation_id = reservation_repository.create(
            conn,
            room_id,
            organizer_user_id,
            title,
            start_datetime,
            end_datetime,
            attendee_count,
            notes,
            participant_user_ids,
            meeting_url,
        )

    organizer = user_repository.find_by_id(conn, organizer_user_id)
    participants = []
    for user_id in participant_user_ids:
        participant = user_repository.find_by_id(conn, user_id)
        if participant is not None:
            participants.append({"employee_id": participant["user_id"], "name": participant["name"]})

    return {
        "reservation_id": reservation_id,
        "room_id": room["room_id"],
        "room_name": room["name"],
        "organizer_user_id": organizer_user_id,
        "organizer_name": organizer["name"] if organizer else organizer_user_id,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "title": title,
        "participants": participants,
        "attendee_count": attendee_count,
        "notes": notes,
        "meeting_url": meeting_url,
        "editable": True,
    }


def list_reservations(
    conn: sqlite3.Connection,
    date_from: str,
    date_to: str,
    room_ids: list[int] | None = None,
) -> list[ReservationListItem]:
    """Thin wrapper (this task's own 実装内容): find_by_range's shape already
    matches docs/P002-frontend-spec.md 4.6節's response exactly."""
    return reservation_repository.find_by_range(conn, date_from, date_to, room_ids)


def list_participant_candidates(conn: sqlite3.Connection) -> list[DirectoryEntry]:
    """docs/P002-frontend-spec.md 4.10.1節: 有効なユーザーの employee_id・name の
    み。内部実現(認可・Repository層)は docs/P003-backend-spec.md 4.10節参照。"""
    return user_repository.find_active_for_directory(conn)


def get_reservation(conn: sqlite3.Connection, reservation_id: int, requesting_user_id: str) -> dict:
    """docs/P002-frontend-spec.md 4.9節: editable は予約者本人または管理者かどうか
    から算出する。"""
    reservation = reservation_repository.find_by_id(conn, reservation_id)
    if reservation is None:
        raise NotFoundError("予約が見つかりません")

    editable = _is_admin(conn, requesting_user_id) or (
        reservation["organizer_user_id"] == requesting_user_id
    )
    date, start_time, end_time = _split_datetime(
        reservation["start_datetime"], reservation["end_datetime"]
    )
    return {
        "reservation_id": reservation["reservation_id"],
        "room_id": reservation["room_id"],
        "room_name": reservation["room_name"],
        "organizer_user_id": reservation["organizer_user_id"],
        "organizer_name": reservation["organizer_name"],
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "title": reservation["title"],
        "participants": reservation["participants"],
        "attendee_count": reservation["attendee_count"],
        "notes": reservation["notes"],
        "meeting_url": reservation["meeting_url"],  # CR-001 (U003-T7)
        "editable": editable,
    }


def _require_editable(conn: sqlite3.Connection, reservation: dict, requesting_user_id: str) -> None:
    if reservation["organizer_user_id"] != requesting_user_id and not _is_admin(conn, requesting_user_id):
        raise ForbiddenError()


def update_reservation(
    conn: sqlite3.Connection,
    reservation_id: int,
    room_id: int,
    date: str,
    start_time: str,
    end_time: str,
    title: str,
    participant_user_ids: list[str],
    attendee_count: int | None,
    notes: str | None,
    requesting_user_id: str,
    meeting_url: str | None = None,
) -> dict:
    """docs/P003-backend-spec.md 4.9.1節: 自分自身(reservation_id)を除外して
    重複チェックする。権限チェック(予約者本人または管理者)はService層で行う
    (このタスクの実装内容のとおり)。

    meeting_url: CR-001 (docs/P901-cr-direction/CR-001.md, U004-T6). Passing
    "" or None clears a previously-set value (docs/P002-frontend-spec.md
    3.4節: "空欄に戻すことも可能")."""
    existing = reservation_repository.find_by_id(conn, reservation_id)
    if existing is None:
        raise NotFoundError("予約が見つかりません")

    _require_editable(conn, existing, requesting_user_id)

    room = room_repository.find_by_id(conn, room_id)
    if room is None or not room["is_active"]:
        raise NotFoundError("指定した会議室が見つかりません")

    meeting_url = _normalize_meeting_url(meeting_url)
    _validate(title, notes, start_time, end_time, attendee_count, room["capacity"], meeting_url)

    start_datetime = _combine(date, start_time)
    end_datetime = _combine(date, end_time)

    with reservation_repository.begin_immediate_transaction(conn):
        overlapping = reservation_repository.find_overlapping(
            conn, room_id, start_datetime, end_datetime, exclude_reservation_id=reservation_id
        )
        if overlapping:
            raise ReservationConflictError()
        reservation_repository.update(
            conn,
            reservation_id,
            room_id,
            title,
            start_datetime,
            end_datetime,
            attendee_count,
            notes,
            meeting_url,
        )
        reservation_repository.replace_participants(conn, reservation_id, participant_user_ids)

    return get_reservation(conn, reservation_id, requesting_user_id)


def cancel_reservation(conn: sqlite3.Connection, reservation_id: int, requesting_user_id: str) -> None:
    """docs/P002-frontend-spec.md 4.9.2節: 物理削除。権限チェックは更新と同様。"""
    existing = reservation_repository.find_by_id(conn, reservation_id)
    if existing is None:
        raise NotFoundError("予約が見つかりません")

    _require_editable(conn, existing, requesting_user_id)

    with reservation_repository.begin_immediate_transaction(conn):
        reservation_repository.delete(conn, reservation_id)


def list_my_reservations(
    conn: sqlite3.Connection, user_id: str, period: str = "upcoming"
) -> list[dict]:
    """docs/P002-frontend-spec.md 3.5節/4.8節。"""
    rows = reservation_repository.find_by_organizer_or_participant(conn, user_id, period)
    return [
        {
            "reservation_id": row["reservation_id"],
            "room_id": row["room_id"],
            "room_name": row["room_name"],
            "date": row["start_datetime"][:10],
            "start_time": row["start_datetime"][11:16],
            "end_time": row["end_datetime"][11:16],
            "title": row["title"],
        }
        for row in rows
    ]
