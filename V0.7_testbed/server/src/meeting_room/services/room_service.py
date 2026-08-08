"""会議室の業務ルール(P002 5.5 / P003 6.2)。トランザクション境界はこの層に置く。"""

from __future__ import annotations

import sqlite3

from .. import db, security
from ..errors import ApiError
from ..repositories import reservations_repo, rooms_repo

DUPLICATE_MESSAGE = "同じ名前の会議室がすでに登録されています。"
NOT_FOUND_MESSAGE = "対象のデータが見つかりません。削除された可能性があります。"


def count_future_reservations(conn: sqlite3.Connection, room_id: int) -> int:
    """本日以降(`reserved_date >= 本日`)の予約件数(P003 6.2 API-07)。

    Sprint 3(U003-T2)で暫定実装(常に0を返す)から本実装へ差し替えた。
    """
    return reservations_repo.count_future(conn, room_id, security.today_local())


def list_rooms(conn: sqlite3.Connection, user: dict, include_inactive: bool) -> list[dict]:
    """API-04。`include_inactive=true` は管理者のみ(P002 5.5)。"""
    if include_inactive and user["role"] != "admin":
        raise ApiError(403, "FORBIDDEN", "この操作を行う権限がありません。")
    return rooms_repo.list_rooms(conn, include_inactive=include_inactive)


def create_room(conn: sqlite3.Connection, payload) -> dict:
    """API-05。`BEGIN IMMEDIATE` → 同名の有効な会議室の確認 → INSERT。"""
    now = security.now_utc()
    with db.transaction(conn):
        if rooms_repo.find_active_by_name(conn, payload.name) is not None:
            raise ApiError(409, "DUPLICATE_KEY", DUPLICATE_MESSAGE)
        room_id = rooms_repo.insert(
            conn, payload.name, payload.capacity, payload.equipment, payload.description,
            payload.is_active, now,
        )
    return rooms_repo.find_by_id(conn, room_id)


def update_room(conn: sqlite3.Connection, room_id: int, payload) -> dict:
    """API-06。全項目送信の全置換更新。自分以外の同名有効行があれば 409。"""
    now = security.now_utc()
    with db.transaction(conn):
        if rooms_repo.find_by_id(conn, room_id) is None:
            raise ApiError(404, "NOT_FOUND", NOT_FOUND_MESSAGE)
        if rooms_repo.find_active_by_name(conn, payload.name, exclude_room_id=room_id) is not None:
            raise ApiError(409, "DUPLICATE_KEY", DUPLICATE_MESSAGE)
        rooms_repo.update(
            conn, room_id, payload.name, payload.capacity, payload.equipment,
            payload.description, payload.is_active, now,
        )
    return rooms_repo.find_by_id(conn, room_id)


def deactivate_room(conn: sqlite3.Connection, room_id: int) -> None:
    """API-07。今後の予約が残っている会議室は無効化できない(409)。既に無効なら何もしない。"""
    now = security.now_utc()
    with db.transaction(conn):
        room = rooms_repo.find_by_id(conn, room_id)
        if room is None:
            raise ApiError(404, "NOT_FOUND", NOT_FOUND_MESSAGE)
        if not room["is_active"]:
            return  # 冪等(P002 5.5 API-07)
        count = count_future_reservations(conn, room_id)
        if count > 0:
            raise ApiError(
                409,
                "CONSTRAINT_VIOLATION",
                f"この会議室には今後の予約が{count}件あります。先に予約を取り消してください。",
            )
        rooms_repo.set_active(conn, room_id, False, now)
