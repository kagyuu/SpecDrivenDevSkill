"""予約Repository。docs/03-backend-spec.md 4章「予約系」対応。

注記: 参加者ID実在チェック(find_missing_participant_ids)は、docs/03-backend-spec.md 4章に
既に明記されている仕様どおり、最初から実装する(V0.2で見つかったF001バグの再現はしない)。
"""
import sqlite3

from app.validation import time_ranges_overlap


def _row_to_summary_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "room_id": row["room_id"],
        "room_name": row["room_name"],
        "date": row["date"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "subject": row["subject"],
        "created_by": row["created_by"],
        "created_by_name": row["created_by_name"],
    }


_SUMMARY_SELECT = """
SELECT r.*, rm.name AS room_name, u.name AS created_by_name
FROM reservations r
JOIN rooms rm ON rm.id = r.room_id
JOIN users u ON u.id = r.created_by
"""


def list_reservations(conn: sqlite3.Connection, date_from: str, date_to: str, room_id: int | None) -> list[dict]:
    query = _SUMMARY_SELECT + " WHERE r.date BETWEEN ? AND ?"
    params: list = [date_from, date_to]
    if room_id is not None:
        query += " AND r.room_id = ?"
        params.append(room_id)
    query += " ORDER BY r.date, r.start_time"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_summary_dict(r) for r in rows]


def list_mine(conn: sqlite3.Connection, user_id: int, period: str, today: str) -> list[dict]:
    if period == "past":
        query = _SUMMARY_SELECT + " WHERE r.created_by = ? AND r.date < ? ORDER BY r.date DESC, r.start_time"
    else:
        query = _SUMMARY_SELECT + " WHERE r.created_by = ? AND r.date >= ? ORDER BY r.date, r.start_time"
    rows = conn.execute(query, (user_id, today)).fetchall()
    return [_row_to_summary_dict(r) for r in rows]


def get_reservation(conn: sqlite3.Connection, reservation_id: int) -> dict | None:
    row = conn.execute(_SUMMARY_SELECT + " WHERE r.id = ?", (reservation_id,)).fetchone()
    if row is None:
        return None
    participant_rows = conn.execute(
        "SELECT user_id FROM reservation_participants WHERE reservation_id = ? ORDER BY user_id",
        (reservation_id,),
    ).fetchall()
    result = _row_to_summary_dict(row)
    result["notes"] = row["notes"]
    result["participant_ids"] = [p["user_id"] for p in participant_rows]
    return result


def find_missing_participant_ids(conn: sqlite3.Connection, participant_ids: list[int]) -> list[int]:
    """participant_ids のうち、有効な(is_active=1)usersに実在しないIDの一覧を返す。

    docs/03-backend-spec.md 4章「予約系」: 「participant_ids に指定された各IDは、有効な
    (is_active=1) users に実在することを事前に検証し、1件でも存在しない場合は
    400 VALIDATION_ERROR を返す」に対応。
    """
    if not participant_ids:
        return []
    placeholders = ",".join("?" for _ in participant_ids)
    rows = conn.execute(
        f"SELECT id FROM users WHERE id IN ({placeholders}) AND is_active = 1",
        participant_ids,
    ).fetchall()
    found = {r["id"] for r in rows}
    return [pid for pid in participant_ids if pid not in found]


def has_overlap(
    conn: sqlite3.Connection,
    room_id: int,
    date: str,
    start_time: str,
    end_time: str,
    exclude_id: int | None = None,
) -> bool:
    if exclude_id is None:
        rows = conn.execute(
            "SELECT start_time, end_time FROM reservations WHERE room_id = ? AND date = ?",
            (room_id, date),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT start_time, end_time FROM reservations WHERE room_id = ? AND date = ? AND id != ?",
            (room_id, date, exclude_id),
        ).fetchall()
    return any(time_ranges_overlap(start_time, end_time, r["start_time"], r["end_time"]) for r in rows)


def create_reservation(
    conn: sqlite3.Connection,
    room_id: int,
    date: str,
    start_time: str,
    end_time: str,
    subject: str,
    notes: str | None,
    created_by: int,
    participant_ids: list[int],
) -> dict:
    conn.execute("BEGIN IMMEDIATE")
    try:
        if has_overlap(conn, room_id, date, start_time, end_time):
            conn.rollback()
            raise ConflictError("指定の時間帯は既に予約されています")
        cur = conn.execute(
            """INSERT INTO reservations (room_id, date, start_time, end_time, subject, notes, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (room_id, date, start_time, end_time, subject, notes, created_by),
        )
        reservation_id = cur.lastrowid
        all_participants = set(participant_ids) | {created_by}
        for uid in all_participants:
            conn.execute(
                "INSERT INTO reservation_participants (reservation_id, user_id) VALUES (?, ?)",
                (reservation_id, uid),
            )
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    return get_reservation(conn, reservation_id)


def update_reservation(
    conn: sqlite3.Connection,
    reservation_id: int,
    room_id: int,
    date: str,
    start_time: str,
    end_time: str,
    subject: str,
    notes: str | None,
    created_by: int,
    participant_ids: list[int],
) -> dict:
    conn.execute("BEGIN IMMEDIATE")
    try:
        if has_overlap(conn, room_id, date, start_time, end_time, exclude_id=reservation_id):
            conn.rollback()
            raise ConflictError("指定の時間帯は既に予約されています")
        conn.execute(
            """UPDATE reservations SET room_id=?, date=?, start_time=?, end_time=?, subject=?, notes=?
               WHERE id=?""",
            (room_id, date, start_time, end_time, subject, notes, reservation_id),
        )
        conn.execute("DELETE FROM reservation_participants WHERE reservation_id = ?", (reservation_id,))
        all_participants = set(participant_ids) | {created_by}
        for uid in all_participants:
            conn.execute(
                "INSERT INTO reservation_participants (reservation_id, user_id) VALUES (?, ?)",
                (reservation_id, uid),
            )
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    return get_reservation(conn, reservation_id)


def delete_reservation(conn: sqlite3.Connection, reservation_id: int) -> None:
    conn.execute("DELETE FROM reservation_participants WHERE reservation_id = ?", (reservation_id,))
    conn.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    conn.commit()


class ConflictError(Exception):
    pass
