"""`reservations` / `reservation_attendees` のデータアクセス(P002 6.2 / 5.3、P003 5.2 / 6.4)。

重複判定SQL(`find_conflicts`)は P003 5.2 の記述をそのまま用いる。半開区間の交差判定であり、
境界一致(A: 09:00-10:00、B: 10:00-11:00)を重複としない(`<=` を使わない。ADR-007)。
"""

from __future__ import annotations

import sqlite3

#: `Reservation` 表現に必要な列。`rooms`・`users` と JOIN して `room_name`/`user_name` を得る
#: (P002 5.3。S02のセル表示・S05の一覧が追加のAPI呼び出しなしで描画できるようにするため)
_SELECT = """
SELECT r.reservation_id, r.room_id, m.name AS room_name,
       r.user_id, u.name AS user_name,
       r.reserved_date, r.start_time, r.end_time, r.title,
       r.attendee_count, r.meeting_url, r.note, r.created_at, r.updated_at
  FROM reservations r
  JOIN rooms m ON m.room_id = r.room_id
  JOIN users u ON u.user_id = r.user_id
"""


def to_reservation_dict(row: sqlite3.Row | None, attendees: list | None = None) -> dict | None:
    """`reservations` の行を P002 5.3 の `Reservation` 表現に変換する。

    `attendees` は呼び出し側が渡す(一覧APIでは空配列。P002 5.7 API-12)。
    """
    if row is None:
        return None
    return {
        "reservation_id": row["reservation_id"],
        "room_id": row["room_id"],
        "room_name": row["room_name"],
        "user_id": row["user_id"],
        "user_name": row["user_name"],
        "reserved_date": row["reserved_date"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "title": row["title"],
        "attendee_count": row["attendee_count"],
        # ※CR-001 未登録は空文字。null を返さない(P002 5.3、ADR-011)
        "meeting_url": row["meeting_url"],
        "note": row["note"],
        "attendees": [] if attendees is None else attendees,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def find_by_id(conn: sqlite3.Connection, reservation_id: int) -> dict | None:
    row = conn.execute(
        _SELECT + " WHERE r.reservation_id = ?", (reservation_id,)
    ).fetchone()
    return to_reservation_dict(row)


def list_by_period(
    conn: sqlite3.Connection,
    date_from: str,
    date_to: str,
    room_ids: list[int] | None = None,
) -> list[dict]:
    """API-12。並びは `reserved_date, start_time, room_id`(P002 5.7)。

    `room_ids` が指定された場合のみ `IN` で絞る。予約ごとの追加クエリは発行しない(N+1の禁止)。
    """
    sql = _SELECT + " WHERE r.reserved_date >= ? AND r.reserved_date <= ?"
    params: list = [date_from, date_to]
    if room_ids:
        placeholders = ",".join("?" for _ in room_ids)
        sql += f" AND r.room_id IN ({placeholders})"
        params.extend(room_ids)
    sql += " ORDER BY r.reserved_date, r.start_time, r.room_id"
    return [d for d in (to_reservation_dict(r) for r in conn.execute(sql, params)) if d]


def list_by_user(conn: sqlite3.Connection, user_id: str, period: str, today: str) -> list[dict]:
    """API-13。`upcoming` は `reserved_date >= today` 昇順、`past` は `< today` 降順(P002 5.7)。"""
    if period == "past":
        sql = _SELECT + (
            " WHERE r.user_id = ? AND r.reserved_date < ?"
            " ORDER BY r.reserved_date DESC, r.start_time DESC"
        )
    else:
        sql = _SELECT + (
            " WHERE r.user_id = ? AND r.reserved_date >= ?"
            " ORDER BY r.reserved_date, r.start_time"
        )
    return [
        d for d in (to_reservation_dict(r) for r in conn.execute(sql, (user_id, today))) if d
    ]


def find_conflicts(
    conn: sqlite3.Connection,
    room_id: int,
    reserved_date: str,
    start_time: str,
    end_time: str,
    exclude_reservation_id: int | None = None,
) -> list[dict]:
    """P003 5.2 の判定SQLをそのまま用いる(半開区間 `[start, end)` の交差)。

    時刻はゼロ埋め固定長の `HH:MM` であり、辞書順比較が時刻順比較と一致する(P003 5.1)。
    """
    rows = conn.execute(
        "SELECT reservation_id, start_time, end_time"
        "  FROM reservations"
        " WHERE room_id = :room_id"
        "   AND reserved_date = :reserved_date"
        "   AND start_time < :end_time"
        "   AND :start_time < end_time"
        "   AND (:exclude_reservation_id IS NULL"
        "        OR reservation_id <> :exclude_reservation_id)"
        " ORDER BY start_time",
        {
            "room_id": room_id,
            "reserved_date": reserved_date,
            "start_time": start_time,
            "end_time": end_time,
            "exclude_reservation_id": exclude_reservation_id,
        },
    ).fetchall()
    return [
        {
            "reservation_id": r["reservation_id"],
            "start_time": r["start_time"],
            "end_time": r["end_time"],
        }
        for r in rows
    ]


def count_future(conn: sqlite3.Connection, room_id: int, today: str) -> int:
    """`reserved_date >= today` の予約件数(P003 6.2 API-07)。"""
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM reservations WHERE room_id = ? AND reserved_date >= ?",
        (room_id, today),
    ).fetchone()
    return int(row["c"])


def insert(
    conn: sqlite3.Connection,
    room_id: int,
    user_id: str,
    reserved_date: str,
    start_time: str,
    end_time: str,
    title: str,
    attendee_count: int | None,
    note: str,
    now: str,
    meeting_url: str = "",
) -> int:
    cursor = conn.execute(
        "INSERT INTO reservations(room_id, user_id, reserved_date, start_time, end_time,"
        " title, attendee_count, meeting_url, note, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            room_id, user_id, reserved_date, start_time, end_time,
            title, attendee_count, meeting_url, note, now, now,
        ),
    )
    return int(cursor.lastrowid)


def update(
    conn: sqlite3.Connection,
    reservation_id: int,
    room_id: int,
    reserved_date: str,
    start_time: str,
    end_time: str,
    title: str,
    attendee_count: int | None,
    note: str,
    now: str,
    meeting_url: str = "",
) -> None:
    """全項目送信の全置換更新(P002 5.7 API-16)。予約者(`user_id`)は変更しない。

    ※CR-001: `meeting_url` も全置換の対象であり、空文字を渡すと登録済みURLが削除される。
    """
    conn.execute(
        "UPDATE reservations SET room_id = ?, reserved_date = ?, start_time = ?, end_time = ?,"
        " title = ?, attendee_count = ?, meeting_url = ?, note = ?, updated_at = ?"
        " WHERE reservation_id = ?",
        (
            room_id, reserved_date, start_time, end_time,
            title, attendee_count, meeting_url, note, now, reservation_id,
        ),
    )


def delete(conn: sqlite3.Connection, reservation_id: int) -> None:
    """物理削除(ADR-008・P002 5.7 API-17)。論理削除はしない。"""
    conn.execute("DELETE FROM reservations WHERE reservation_id = ?", (reservation_id,))


def delete_attendees(conn: sqlite3.Connection, reservation_id: int) -> None:
    """参加者行の明示削除(FKの ON DELETE CASCADE でも消えるが明示する。P003 6.4 API-17)。"""
    conn.execute(
        "DELETE FROM reservation_attendees WHERE reservation_id = ?", (reservation_id,)
    )


def replace_attendees(
    conn: sqlite3.Connection, reservation_id: int, user_ids: list[str]
) -> None:
    """参加者を全置換する(API-16は全削除して再INSERT。P003 6.4)。"""
    delete_attendees(conn, reservation_id)
    for user_id in user_ids or []:
        conn.execute(
            "INSERT INTO reservation_attendees(reservation_id, user_id) VALUES (?, ?)",
            (reservation_id, user_id),
        )


def list_attendees(conn: sqlite3.Connection, reservation_id: int) -> list[dict]:
    """`users` と JOIN して `user_id` と `name` を返す(P002 5.3 の `attendees`)。"""
    rows = conn.execute(
        "SELECT a.user_id, u.name FROM reservation_attendees a"
        "  JOIN users u ON u.user_id = a.user_id"
        " WHERE a.reservation_id = ? ORDER BY a.user_id",
        (reservation_id,),
    ).fetchall()
    return [{"user_id": r["user_id"], "name": r["name"]} for r in rows]
