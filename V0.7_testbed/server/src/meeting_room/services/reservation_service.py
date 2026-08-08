"""予約の業務ルール(P002 3.3 / 3.4 / 5.7、P003 5 / 6.4)。

本モジュールが本システムの中核である。
* 重複判定は半開区間の交差(P003 5.1・5.2、ADR-007)。境界一致は重複としない。
* 「重複チェック → INSERT/UPDATE」は必ず**同一の `BEGIN IMMEDIATE` トランザクション**の中で行う
  (P003 5.3)。検査と更新を分けると TOCTOU になる。
* Pythonの `threading.Lock` による直列化は行わない(P003 5.3 が明確に否定している)。
"""

from __future__ import annotations

import json
import logging
import sqlite3

from .. import db, security
from ..errors import ApiError
from ..repositories import reservations_repo, rooms_repo, users_repo

#: 業務時間(P002 3.3。開始 08:00〜19:30 / 終了 08:30〜20:00)
BUSINESS_START = "08:00"
BUSINESS_END = "20:00"
#: 409 応答に含める競合予約の最大件数(P003 5.2)
MAX_CONFLICTS = 5

NOT_FOUND_MESSAGE = "対象のデータが見つかりません。削除された可能性があります。"
CONFLICT_MESSAGE = "選択した時間帯はすでに予約されています。"
PAST_DATE_MESSAGE = "過去の日付には予約できません。"
# P002 3.4 の文言。取消(API-17)にも同じ文言を使う
# ★FIXME★ 取消時の文言はP002 3.4に編集の文言しか無いため、同じ文言を流用した
PAST_RESERVATION_MESSAGE = "過去の予約は編集できません。"
ROOM_INVALID_MESSAGE = "会議室を選択してください。"
# ★FIXME★ 無効・存在しない参加者を指定したときの文言はP002 3.3に記載がないため補った
ATTENDEE_INVALID_MESSAGE = "選択できない参加者が含まれています。"

#: ロック競合(P003 5.3)を記録する専用ログ。アクセスログと同じ標準出力に1行1JSONで出す
_lock_logger = logging.getLogger("meeting_room.access")


def _validation_error(field: str, message: str) -> ApiError:
    return ApiError(
        400,
        "VALIDATION_ERROR",
        "入力内容に誤りがあります。",
        details=[{"field": field, "message": message}],
    )


def _is_half_hour(value: str) -> bool:
    return value.endswith(":00") or value.endswith(":30")


def _validate_business(conn: sqlite3.Connection, req, today: str) -> dict:
    """P003 6.4(API-15)の入力検証。戻り値は対象の会議室(収容人数の比較に使う)。

    U003-T2 に指定された順に検証する。
    """
    # 1. 30分刻み・業務時間内・開始 < 終了
    from ..schemas import BUSINESS_HOURS_MESSAGE, TIME_STEP_MESSAGE

    if not _is_half_hour(req.start_time):
        raise _validation_error("start_time", TIME_STEP_MESSAGE)
    if not _is_half_hour(req.end_time):
        raise _validation_error("end_time", TIME_STEP_MESSAGE)
    if req.start_time < BUSINESS_START or req.start_time >= BUSINESS_END:
        raise _validation_error("start_time", BUSINESS_HOURS_MESSAGE)
    if req.end_time <= BUSINESS_START or req.end_time > BUSINESS_END:
        raise _validation_error("end_time", BUSINESS_HOURS_MESSAGE)
    if req.end_time <= req.start_time:
        raise _validation_error("end_time", "終了時刻は開始時刻より後にしてください。")

    # 2. 過去日は登録できない
    if req.reserved_date < today:
        raise _validation_error("reserved_date", PAST_DATE_MESSAGE)

    # 3. 会議室が存在し有効であること
    room = rooms_repo.find_by_id(conn, req.room_id)
    if room is None or not room["is_active"]:
        raise _validation_error("room_id", ROOM_INVALID_MESSAGE)

    # 4. 参加予定人数が収容人数を超えていないこと(400 CAPACITY_EXCEEDED)
    if req.attendee_count is not None and req.attendee_count > room["capacity"]:
        raise ApiError(
            400,
            "CAPACITY_EXCEEDED",
            f"参加予定人数が会議室の収容人数({room['capacity']}名)を超えています。",
        )

    # 5. 参加者が全て存在し有効であること
    for user_id in req.attendee_user_ids:
        target = users_repo.find_by_id(conn, user_id)
        if target is None or not target["is_active"]:
            raise _validation_error("attendee_user_ids", ATTENDEE_INVALID_MESSAGE)

    return room


def _check_conflicts(
    conn: sqlite3.Connection, req, exclude_reservation_id: int | None = None
) -> None:
    """P003 5.2 の重複チェック。1件以上なら 409 `RESERVATION_CONFLICT`(最大5件を添える)。"""
    conflicts = reservations_repo.find_conflicts(
        conn,
        req.room_id,
        req.reserved_date,
        req.start_time,
        req.end_time,
        exclude_reservation_id=exclude_reservation_id,
    )
    if conflicts:
        raise ApiError(
            409,
            "RESERVATION_CONFLICT",
            CONFLICT_MESSAGE,
            extra={"conflicts": conflicts[:MAX_CONFLICTS]},
        )


def _detail(conn: sqlite3.Connection, reservation_id: int) -> dict:
    """`attendees` を含む予約詳細(P002 5.3)。"""
    reservation = reservations_repo.find_by_id(conn, reservation_id)
    if reservation is None:
        raise ApiError(404, "NOT_FOUND", NOT_FOUND_MESSAGE)
    reservation["attendees"] = reservations_repo.list_attendees(conn, reservation_id)
    return reservation


def _require_owner_or_admin(actor: dict, reservation: dict) -> None:
    """予約者本人または管理者(P002 5.7 API-16/17)。"""
    if actor["user_id"] != reservation["user_id"] and actor["role"] != "admin":
        raise ApiError(403, "FORBIDDEN", "この操作を行う権限がありません。")


def _lock_timeout_error(exc: sqlite3.OperationalError) -> ApiError:
    """`database is locked` を 500 `INTERNAL_ERROR` に変換する(P003 5.3)。

    P002 5.2 のエラーコード表に 503 が無いため契約を増やさず 500 とし、
    ログにだけ `error_code=DB_LOCK_TIMEOUT` を残す。
    """
    _lock_logger.error(
        json.dumps(
            {
                "ts": security.now_utc(),
                "level": "ERROR",
                "error_code": "DB_LOCK_TIMEOUT",
                "message": str(exc),
            },
            ensure_ascii=False,
        )
    )
    return ApiError(
        500, "INTERNAL_ERROR", "システムエラーが発生しました。時間をおいて再度お試しください。"
    )


def _is_lock_timeout(exc: sqlite3.OperationalError) -> bool:
    return "locked" in str(exc).lower() or "busy" in str(exc).lower()


# --- 参照系(API-12・API-13・API-14) -------------------------------------------------


def list_by_period(
    conn: sqlite3.Connection, date_from: str, date_to: str, room_ids: list[int] | None
) -> list[dict]:
    """API-12。`attendees` は空配列のまま返す(一覧の軽量化。P002 5.7)。"""
    return reservations_repo.list_by_period(conn, date_from, date_to, room_ids)


def list_mine(conn: sqlite3.Connection, actor: dict, period: str) -> list[dict]:
    """API-13。予約者が自分である予約のみ(P002 3.5)。"""
    return reservations_repo.list_by_user(
        conn, actor["user_id"], period, security.today_local()
    )


def get_detail(conn: sqlite3.Connection, reservation_id: int) -> dict:
    """API-14。閲覧は全ログインユーザーに許可する(権限制限をかけない。P002 5.7)。"""
    return _detail(conn, reservation_id)


# --- 更新系(API-15・API-16・API-17) -------------------------------------------------


def create(conn: sqlite3.Connection, actor: dict, req) -> dict:
    """API-15。検証・重複チェック・INSERT を単一の `BEGIN IMMEDIATE` の中で行う。"""
    now = security.now_utc()
    today = security.today_local()
    try:
        with db.transaction(conn):
            _validate_business(conn, req, today)
            _check_conflicts(conn, req)
            reservation_id = reservations_repo.insert(
                conn,
                req.room_id,
                actor["user_id"],  # 予約者は常にセッションのユーザー(リクエスト値を信用しない)
                req.reserved_date,
                req.start_time,
                req.end_time,
                req.title,
                req.attendee_count,
                req.note,
                now,
                meeting_url=req.meeting_url,  # ※CR-001
            )
            reservations_repo.replace_attendees(conn, reservation_id, req.attendee_user_ids)
    except sqlite3.OperationalError as exc:
        if _is_lock_timeout(exc):
            raise _lock_timeout_error(exc) from exc
        raise
    return _detail(conn, reservation_id)


def update(conn: sqlite3.Connection, actor: dict, reservation_id: int, req) -> dict:
    """API-16。重複チェックから自分自身を除外する(P002 5.7)。"""
    now = security.now_utc()
    today = security.today_local()
    try:
        with db.transaction(conn):
            target = reservations_repo.find_by_id(conn, reservation_id)
            if target is None:
                raise ApiError(404, "NOT_FOUND", NOT_FOUND_MESSAGE)
            _require_owner_or_admin(actor, target)
            if target["reserved_date"] < today:
                raise ApiError(409, "CONSTRAINT_VIOLATION", PAST_RESERVATION_MESSAGE)
            _validate_business(conn, req, today)
            _check_conflicts(conn, req, exclude_reservation_id=reservation_id)
            reservations_repo.update(
                conn,
                reservation_id,
                req.room_id,
                req.reserved_date,
                req.start_time,
                req.end_time,
                req.title,
                req.attendee_count,
                req.note,
                now,
                meeting_url=req.meeting_url,  # ※CR-001
            )
            reservations_repo.replace_attendees(conn, reservation_id, req.attendee_user_ids)
    except sqlite3.OperationalError as exc:
        if _is_lock_timeout(exc):
            raise _lock_timeout_error(exc) from exc
        raise
    return _detail(conn, reservation_id)


def delete(conn: sqlite3.Connection, actor: dict, reservation_id: int) -> None:
    """API-17。予約行と参加者行を物理削除する(P002 5.7)。"""
    today = security.today_local()
    try:
        with db.transaction(conn):
            target = reservations_repo.find_by_id(conn, reservation_id)
            if target is None:
                raise ApiError(404, "NOT_FOUND", NOT_FOUND_MESSAGE)
            _require_owner_or_admin(actor, target)
            if target["reserved_date"] < today:
                raise ApiError(409, "CONSTRAINT_VIOLATION", PAST_RESERVATION_MESSAGE)
            # ON DELETE CASCADE でも消えるが明示する(P003 6.4)
            reservations_repo.delete_attendees(conn, reservation_id)
            reservations_repo.delete(conn, reservation_id)
    except sqlite3.OperationalError as exc:
        if _is_lock_timeout(exc):
            raise _lock_timeout_error(exc) from exc
        raise
