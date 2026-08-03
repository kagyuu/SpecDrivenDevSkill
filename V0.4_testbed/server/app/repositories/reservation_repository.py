"""予約Repository層 (docs/P003-backend-spec.md §5, §7.8〜§7.13).

U003-3: list_by_range, has_overlap, insert_with_participants
U004-2: find_with_detail, list_by_creator, update_with_participants, delete
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app.core.datetime_utils import is_upcoming
from app.core.exceptions import OverlapError


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def has_overlap(conn: sqlite3.Connection, room_id: int, date: str, start_time: str, end_time: str,
                exclude_reservation_id: int | None = None) -> bool:
    """区間判定式: start_time < 既存.end_time AND end_time > 既存.start_time (docs/P003-backend-spec.md §5)。"""
    query = (
        "SELECT COUNT(*) AS cnt FROM RESERVATIONS "
        "WHERE room_id = ? AND date = ? AND start_time < ? AND end_time > ?"
    )
    params: list = [room_id, date, end_time, start_time]
    if exclude_reservation_id is not None:
        query += " AND id != ?"
        params.append(exclude_reservation_id)
    row = conn.execute(query, params).fetchone()
    return row["cnt"] > 0


def list_by_range(conn: sqlite3.Connection, date_from: str, date_to: str,
                   room_ids: list[int] | None = None) -> list[sqlite3.Row]:
    """参加者・備考をJOINしない軽量なSELECT (docs/P003-backend-spec.md §7.8)。"""
    query = (
        "SELECT r.id, r.room_id, r.date, r.start_time, r.end_time, r.title, "
        "u.id AS created_by_id, u.name AS created_by_name "
        "FROM RESERVATIONS r JOIN USERS u ON r.created_by = u.id "
        "WHERE r.date >= ? AND r.date <= ?"
    )
    params: list = [date_from, date_to]
    if room_ids:
        placeholders = ",".join("?" for _ in room_ids)
        query += f" AND r.room_id IN ({placeholders})"
        params.extend(room_ids)
    query += " ORDER BY r.date, r.start_time"
    return conn.execute(query, params).fetchall()


def insert_with_participants(conn: sqlite3.Connection, data: dict, current_user_id: int) -> int:
    """BEGIN IMMEDIATEで排他制御しつつ重複再チェック後INSERTする (docs/P003-backend-spec.md §5)。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        if has_overlap(conn, data["room_id"], data["date"], data["start_time"], data["end_time"]):
            conn.execute("ROLLBACK")
            raise OverlapError("選択した会議室・時間帯は既に予約されています")
        now = _now_iso()
        cur = conn.execute(
            "INSERT INTO RESERVATIONS (room_id, date, start_time, end_time, title, notes, created_by, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data["room_id"], data["date"], data["start_time"], data["end_time"], data["title"],
             data.get("notes"), current_user_id, now, now),
        )
        reservation_id = cur.lastrowid
        for participant_id in data.get("participant_ids", []):
            conn.execute(
                "INSERT INTO RESERVATION_PARTICIPANTS (reservation_id, user_id) VALUES (?, ?)",
                (reservation_id, participant_id),
            )
        conn.execute("COMMIT")
        return reservation_id
    except OverlapError:
        raise
    except Exception:
        conn.execute("ROLLBACK")
        raise


def find_with_detail(conn: sqlite3.Connection, reservation_id: int) -> dict | None:
    """参加者一覧・作成者名までJOINして返す。存在しなければNone。"""
    row = conn.execute(
        "SELECT r.*, u.name AS created_by_name FROM RESERVATIONS r "
        "JOIN USERS u ON r.created_by = u.id WHERE r.id = ?",
        (reservation_id,),
    ).fetchone()
    if row is None:
        return None
    participants = conn.execute(
        "SELECT u.id, u.name FROM RESERVATION_PARTICIPANTS rp "
        "JOIN USERS u ON rp.user_id = u.id WHERE rp.reservation_id = ?",
        (reservation_id,),
    ).fetchall()
    return {
        "id": row["id"],
        "room_id": row["room_id"],
        "date": row["date"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "title": row["title"],
        "notes": row["notes"],
        "created_by": {"id": row["created_by"], "name": row["created_by_name"]},
        "participants": [{"id": p["id"], "name": p["name"]} for p in participants],
    }


def list_by_creator(conn: sqlite3.Connection, user_id: int, period: str = "upcoming") -> list[sqlite3.Row]:
    """作成者別一覧。upcoming/pastでフィルタする (docs/P003-backend-spec.md §7.9)。"""
    rows = conn.execute(
        "SELECT r.*, u.name AS created_by_name FROM RESERVATIONS r "
        "JOIN USERS u ON r.created_by = u.id WHERE r.created_by = ? ORDER BY r.date, r.start_time",
        (user_id,),
    ).fetchall()
    if period == "past":
        return [row for row in rows if not is_upcoming(row["date"])]
    return [row for row in rows if is_upcoming(row["date"])]


def update_with_participants(conn: sqlite3.Connection, reservation_id: int, data: dict) -> None:
    """BEGIN IMMEDIATEで重複再チェック(自分自身除外)後UPDATE、参加者は全削除→再INSERT。"""
    conn.execute("BEGIN IMMEDIATE")
    try:
        if has_overlap(conn, data["room_id"], data["date"], data["start_time"], data["end_time"],
                        exclude_reservation_id=reservation_id):
            conn.execute("ROLLBACK")
            raise OverlapError("選択した会議室・時間帯は既に予約されています")
        now = _now_iso()
        conn.execute(
            "UPDATE RESERVATIONS SET room_id = ?, date = ?, start_time = ?, end_time = ?, title = ?, "
            "notes = ?, updated_at = ? WHERE id = ?",
            (data["room_id"], data["date"], data["start_time"], data["end_time"], data["title"],
             data.get("notes"), now, reservation_id),
        )
        conn.execute("DELETE FROM RESERVATION_PARTICIPANTS WHERE reservation_id = ?", (reservation_id,))
        for participant_id in data.get("participant_ids", []):
            conn.execute(
                "INSERT INTO RESERVATION_PARTICIPANTS (reservation_id, user_id) VALUES (?, ?)",
                (reservation_id, participant_id),
            )
        conn.execute("COMMIT")
    except OverlapError:
        raise
    except Exception:
        conn.execute("ROLLBACK")
        raise


def delete(conn: sqlite3.Connection, reservation_id: int) -> None:
    """物理DELETE。RESERVATION_PARTICIPANTSはON DELETE CASCADEで自動削除される。"""
    conn.execute("DELETE FROM RESERVATIONS WHERE id = ?", (reservation_id,))
    conn.commit()
