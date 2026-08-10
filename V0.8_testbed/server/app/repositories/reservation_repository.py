"""Reservation repository (U003-T1, docs/P007-impl-direction/U003-reservation-core-and-calendar.md).

Implements the exclusive-control mechanism from docs/P003-backend-spec.md
4.6〜4.9.2節: reservation create/update callers are expected to run inside
begin_immediate_transaction() (BEGIN IMMEDIATE acquires SQLite's write lock
up front), then call find_overlapping() before create()/update(), so two
concurrent callers cannot both pass the overlap check for the same
room/time-range and double-book it - the second caller's BEGIN IMMEDIATE
blocks until the first commits or rolls back, and by the time it proceeds,
find_overlapping() will see the first caller's now-committed row.

Deciding what to do when find_overlapping() returns matches (raise a
conflict error, abort) is the Service layer's job (U003-T2/U004-T1), not
this layer's - this task's own 実装してはいけないこと says Repository層は受け
取った値をそのまま保存するだけでよい.

U004-T1 adds find_by_id/update/delete/find_by_organizer_or_participant/
replace_participants, following the same "no self-commit, caller wraps in
begin_immediate_transaction()" convention as create() (U003-T1) - these
functions issue plain execute() calls with no `with conn:`/commit of their
own.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import TypedDict


class ReservationListItem(TypedDict):
    reservation_id: int
    room_id: int
    room_name: str
    organizer_user_id: str
    organizer_name: str
    title: str
    start_datetime: str
    end_datetime: str


@contextmanager
def begin_immediate_transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """Acquire SQLite's write lock up front (BEGIN IMMEDIATE), then commit on
    success or roll back on any exception raised inside the `with` block.

    Must wrap the overlap-check SELECT (find_overlapping) *and* the
    following INSERT/UPDATE together - acquiring the lock only around the
    write, after the check, would reopen the race window this exists to
    close.
    """
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()


def find_overlapping(
    conn: sqlite3.Connection,
    room_id: int,
    start_datetime: str,
    end_datetime: str,
    exclude_reservation_id: int | None = None,
) -> list[int]:
    """docs/P003-backend-spec.md 4.6〜4.9.2節 の重複判定クエリ。端点が接するだけ
    (existing.end == new.start など)は重複としない(狭義の不等号を使う)。"""
    query = (
        "SELECT reservation_id FROM reservations "
        "WHERE room_id = ? AND start_datetime < ? AND end_datetime > ?"
    )
    params: list = [room_id, end_datetime, start_datetime]
    if exclude_reservation_id is not None:
        query += " AND reservation_id != ?"
        params.append(exclude_reservation_id)
    rows = conn.execute(query, params).fetchall()
    return [row["reservation_id"] for row in rows]


def create(
    conn: sqlite3.Connection,
    room_id: int,
    organizer_user_id: str,
    title: str,
    start_datetime: str,
    end_datetime: str,
    attendee_count: int | None,
    notes: str | None,
    participant_user_ids: list[str],
    meeting_url: str | None = None,
) -> int:
    """Insert the reservation and its participants in one call. Intended to
    run inside begin_immediate_transaction()'s `with` block (does not itself
    commit/rollback).

    meeting_url: CR-001 (docs/P901-cr-direction/CR-001.md, U003-T7). Optional
    keyword with a default so this stays call-compatible with any pre-CR-001
    callers; normalization (empty string -> None) and format/length
    validation are the Service layer's job (app/services/reservation_service.py),
    same division of responsibility as the other fields here."""
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO reservations (room_id, organizer_user_id, title, start_datetime, "
        "end_datetime, attendee_count, notes, meeting_url, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            room_id,
            organizer_user_id,
            title,
            start_datetime,
            end_datetime,
            attendee_count,
            notes,
            meeting_url,
            now,
            now,
        ),
    )
    reservation_id = cursor.lastrowid
    assert reservation_id is not None
    add_participants(conn, reservation_id, participant_user_ids)
    return reservation_id


def add_participants(conn: sqlite3.Connection, reservation_id: int, user_ids: list[str]) -> None:
    if not user_ids:
        return
    conn.executemany(
        "INSERT INTO reservation_participants (reservation_id, user_id) VALUES (?, ?)",
        [(reservation_id, user_id) for user_id in user_ids],
    )


def find_by_range(
    conn: sqlite3.Connection,
    date_from: str,
    date_to: str,
    room_ids: list[int] | None = None,
) -> list[ReservationListItem]:
    """docs/P002-frontend-spec.md 4.6節: room_name/organizer_name をJOINして
    返す(会議室が無効化されていても既存予約の会議室名は表示する。3.6節参照 - この
    クエリはrooms.is_activeでフィルタしない)。"""
    query = (
        "SELECT r.reservation_id, r.room_id, rm.name AS room_name, "
        "r.organizer_user_id, u.name AS organizer_name, r.title, "
        "r.start_datetime, r.end_datetime "
        "FROM reservations r "
        "JOIN rooms rm ON rm.room_id = r.room_id "
        "JOIN users u ON u.user_id = r.organizer_user_id "
        "WHERE r.start_datetime < ? AND r.end_datetime > ?"
    )
    params: list = [f"{date_to}T23:59:59.999999", f"{date_from}T00:00:00"]
    if room_ids:
        placeholders = ",".join("?" for _ in room_ids)
        query += f" AND r.room_id IN ({placeholders})"
        params.extend(room_ids)
    query += " ORDER BY r.start_datetime"
    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]  # type: ignore[misc]


def find_participants(conn: sqlite3.Connection, reservation_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT u.user_id AS employee_id, u.name FROM reservation_participants rp "
        "JOIN users u ON u.user_id = rp.user_id WHERE rp.reservation_id = ? "
        "ORDER BY u.user_id",
        (reservation_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def find_by_id(conn: sqlite3.Connection, reservation_id: int) -> dict | None:
    """docs/P002-frontend-spec.md 4.9節の詳細取得。room_name/organizer_name を
    JOINし、participants も併せて返す(editable の算出はService層の役割)。"""
    row = conn.execute(
        "SELECT r.reservation_id, r.room_id, rm.name AS room_name, "
        "r.organizer_user_id, u.name AS organizer_name, r.title, "
        "r.start_datetime, r.end_datetime, r.attendee_count, r.notes, r.meeting_url "
        "FROM reservations r "
        "JOIN rooms rm ON rm.room_id = r.room_id "
        "JOIN users u ON u.user_id = r.organizer_user_id "
        "WHERE r.reservation_id = ?",
        (reservation_id,),
    ).fetchone()
    if row is None:
        return None
    detail = dict(row)
    detail["participants"] = find_participants(conn, reservation_id)
    return detail


def update(
    conn: sqlite3.Connection,
    reservation_id: int,
    room_id: int,
    title: str,
    start_datetime: str,
    end_datetime: str,
    attendee_count: int | None,
    notes: str | None,
    meeting_url: str | None = None,
) -> bool:
    """Updates the reservation row only - participants are handled
    separately by replace_participants (docs/P003-backend-spec.md 4.6〜4.9.2節:
    "参加者は既存を全削除してから再INSERTする").

    meeting_url: CR-001 (U004-T6). Passing None clears a previously-set
    value (docs/P002-frontend-spec.md 3.4節: "空欄に戻すことも可能")."""
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "UPDATE reservations SET room_id = ?, title = ?, start_datetime = ?, "
        "end_datetime = ?, attendee_count = ?, notes = ?, meeting_url = ?, updated_at = ? "
        "WHERE reservation_id = ?",
        (
            room_id,
            title,
            start_datetime,
            end_datetime,
            attendee_count,
            notes,
            meeting_url,
            now,
            reservation_id,
        ),
    )
    return cursor.rowcount > 0


def replace_participants(conn: sqlite3.Connection, reservation_id: int, user_ids: list[str]) -> None:
    conn.execute(
        "DELETE FROM reservation_participants WHERE reservation_id = ?", (reservation_id,)
    )
    add_participants(conn, reservation_id, user_ids)


def delete(conn: sqlite3.Connection, reservation_id: int) -> bool:
    """Physical delete (docs/P002-frontend-spec.md 4.9.2節). Participant rows
    reference reservations.reservation_id with no ON DELETE CASCADE (2.2節
    DDL), so they must be deleted first or PRAGMA foreign_keys=ON rejects
    the parent delete."""
    conn.execute("DELETE FROM reservation_participants WHERE reservation_id = ?", (reservation_id,))
    cursor = conn.execute("DELETE FROM reservations WHERE reservation_id = ?", (reservation_id,))
    return cursor.rowcount > 0


def find_by_organizer_or_participant(
    conn: sqlite3.Connection, user_id: str, period: str = "upcoming"
) -> list[dict]:
    """docs/P002-frontend-spec.md 3.5節/4.8節のマイ予約一覧。

    ★実施メモ: このタスク自身の【実装内容】本文は「WHERE organizer_user_id = ?」
    としか書いていないが、メソッド名(find_by_organizer_or_participant)は
    参加者としての予約も含むことを示している。「マイ予約」という機能の性質上、
    自分が参加者になっている予約が一覧から漏れるのは利用者にとって不自然であり、
    メソッド名の方がこの節の意図をより正確に表していると判断し、OR条件で実装した。
    """
    query = (
        "SELECT r.reservation_id, r.room_id, rm.name AS room_name, "
        "r.start_datetime, r.end_datetime, r.title "
        "FROM reservations r "
        "JOIN rooms rm ON rm.room_id = r.room_id "
        "WHERE (r.organizer_user_id = ? OR r.reservation_id IN "
        "(SELECT reservation_id FROM reservation_participants WHERE user_id = ?))"
    )
    params: list = [user_id, user_id]

    if period in ("upcoming", "past"):
        now = datetime.now(timezone.utc).isoformat()
        query += " AND r.end_datetime >= ?" if period == "upcoming" else " AND r.end_datetime < ?"
        params.append(now)
    # period == "all": 追加条件なし。

    query += " ORDER BY r.start_datetime"
    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]
