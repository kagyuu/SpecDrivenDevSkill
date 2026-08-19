"""reservations テーブルへのデータアクセス。docs/P003-backend-spec.md §3.2, §5.6〜§5.9, §6。

このモジュール内のいずれの関数も、現在時刻・現在日付をシステム時計から取得しない。
「今後/過去」判定などに必要な現在時刻は、呼び出し元(Service層)が計算して
明示的な引数(``now``)として渡す(docs/P003-backend-spec.md §6)。
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class Reservation:
    id: int
    room_id: int
    room_name: str
    user_id: int
    user_name: str
    date: str
    start_time: str
    end_time: str
    title: str
    expected_attendees: int | None
    notes: str | None
    internal_memo: str | None  # ※CR-001により追加。所有者・管理者のみ閲覧可(マスキングはRouter層で行う)
    participant_ids: list[int]
    created_at: str
    updated_at: str


_SELECT_BASE = """
    SELECT r.id, r.room_id, rm.name AS room_name, r.user_id, u.name AS user_name,
           r.date, r.start_time, r.end_time, r.title, r.expected_attendees, r.notes,
           r.internal_memo, r.created_at, r.updated_at
    FROM reservations r
    JOIN rooms rm ON rm.id = r.room_id
    JOIN users u ON u.id = r.user_id
"""


def _participant_ids(conn: sqlite3.Connection, reservation_id: int) -> list[int]:
    rows = conn.execute(
        "SELECT user_id FROM reservation_participants WHERE reservation_id = ? ORDER BY user_id",
        (reservation_id,),
    ).fetchall()
    return [row["user_id"] for row in rows]


def _row_to_reservation(conn: sqlite3.Connection, row: sqlite3.Row) -> Reservation:
    return Reservation(
        id=row["id"],
        room_id=row["room_id"],
        room_name=row["room_name"],
        user_id=row["user_id"],
        user_name=row["user_name"],
        date=row["date"],
        start_time=row["start_time"],
        end_time=row["end_time"],
        title=row["title"],
        expected_attendees=row["expected_attendees"],
        notes=row["notes"],
        internal_memo=row["internal_memo"],
        participant_ids=_participant_ids(conn, row["id"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_reservation(
    conn: sqlite3.Connection,
    room_id: int,
    user_id: int,
    date: str,
    start_time: str,
    end_time: str,
    title: str,
    expected_attendees: int | None,
    notes: str | None,
    participant_ids: list[int],
    created_at: str,
    internal_memo: str | None = None,  # ※CR-001により追加(既存呼び出しを壊さないようキーワード引数+デフォルト値)
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO reservations
            (room_id, user_id, date, start_time, end_time, title, expected_attendees, notes, internal_memo, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (room_id, user_id, date, start_time, end_time, title, expected_attendees, notes, internal_memo, created_at, created_at),
    )
    reservation_id = cursor.lastrowid
    for participant_id in participant_ids:
        conn.execute(
            "INSERT INTO reservation_participants (reservation_id, user_id) VALUES (?, ?)",
            (reservation_id, participant_id),
        )
    conn.commit()
    return reservation_id


def update_reservation(
    conn: sqlite3.Connection,
    reservation_id: int,
    room_id: int,
    date: str,
    start_time: str,
    end_time: str,
    title: str,
    expected_attendees: int | None,
    notes: str | None,
    participant_ids: list[int],
    updated_at: str,
    internal_memo: str | None = None,  # ※CR-001により追加
) -> None:
    conn.execute(
        """
        UPDATE reservations
        SET room_id = ?, date = ?, start_time = ?, end_time = ?, title = ?,
            expected_attendees = ?, notes = ?, internal_memo = ?, updated_at = ?
        WHERE id = ?
        """,
        (room_id, date, start_time, end_time, title, expected_attendees, notes, internal_memo, updated_at, reservation_id),
    )
    conn.execute("DELETE FROM reservation_participants WHERE reservation_id = ?", (reservation_id,))
    for participant_id in participant_ids:
        conn.execute(
            "INSERT INTO reservation_participants (reservation_id, user_id) VALUES (?, ?)",
            (reservation_id, participant_id),
        )
    conn.commit()


def delete_reservation(conn: sqlite3.Connection, reservation_id: int) -> None:
    conn.execute("DELETE FROM reservation_participants WHERE reservation_id = ?", (reservation_id,))
    conn.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    conn.commit()


def find_conflicting(
    conn: sqlite3.Connection,
    room_id: int,
    date: str,
    start_time: str,
    end_time: str,
    exclude_id: int | None,
) -> list[Reservation]:
    # docs/P003-backend-spec.md §5.9 のSQL実装例に対応する。
    rows = conn.execute(
        _SELECT_BASE
        + """
        WHERE r.room_id = ? AND r.date = ?
          AND r.id != ?
          AND NOT (? <= r.start_time OR ? >= r.end_time)
        """,
        (room_id, date, exclude_id if exclude_id is not None else -1, end_time, start_time),
    ).fetchall()
    return [_row_to_reservation(conn, row) for row in rows]


def list_by_range(
    conn: sqlite3.Connection,
    date_from: str,
    date_to: str,
    room_id: int | None,
) -> list[Reservation]:
    if room_id is not None:
        rows = conn.execute(
            _SELECT_BASE + " WHERE r.date BETWEEN ? AND ? AND r.room_id = ? ORDER BY r.date, r.start_time",
            (date_from, date_to, room_id),
        ).fetchall()
    else:
        rows = conn.execute(
            _SELECT_BASE + " WHERE r.date BETWEEN ? AND ? ORDER BY r.date, r.start_time",
            (date_from, date_to),
        ).fetchall()
    return [_row_to_reservation(conn, row) for row in rows]


def get_by_id(conn: sqlite3.Connection, reservation_id: int) -> Reservation | None:
    row = conn.execute(_SELECT_BASE + " WHERE r.id = ?", (reservation_id,)).fetchone()
    return _row_to_reservation(conn, row) if row else None


def list_by_user(
    conn: sqlite3.Connection,
    user_id: int,
    now: datetime,
    period: Literal["upcoming", "past"],
) -> list[Reservation]:
    today = now.date().isoformat()
    current_time = now.strftime("%H:%M")

    if period == "upcoming":
        rows = conn.execute(
            _SELECT_BASE
            + """
            WHERE r.user_id = ?
              AND (r.date > ? OR (r.date = ? AND r.end_time > ?))
            ORDER BY r.date, r.start_time
            """,
            (user_id, today, today, current_time),
        ).fetchall()
    else:
        rows = conn.execute(
            _SELECT_BASE
            + """
            WHERE r.user_id = ?
              AND NOT (r.date > ? OR (r.date = ? AND r.end_time > ?))
            ORDER BY r.date, r.start_time
            """,
            (user_id, today, today, current_time),
        ).fetchall()

    return [_row_to_reservation(conn, row) for row in rows]
