"""U003-T2 単体テスト — `ReservationRequest` と `reservation_service`。

参照: docs/P002-frontend-spec.md 3.3 / 3.4 / 5.2 / 5.7、docs/P003-backend-spec.md 5 / 6.4 / 4.5
同時実行(2スレッドから同一枠へ `create`)で必ず一方だけが成功することを確認する。
"""

import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from meeting_room import db, security
from meeting_room.errors import ApiError
from meeting_room.repositories import reservations_repo, rooms_repo, users_repo
from meeting_room.schemas import ReservationRequest, validate
from meeting_room.services import reservation_service, room_service

NOW = "2026-08-05T00:00:00Z"


def _date(offset_days: int) -> str:
    return (datetime.now() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _body(**overrides) -> dict:
    body = {
        "room_id": 1,
        "reserved_date": _date(1),
        "start_time": "10:00",
        "end_time": "11:00",
        "title": "定例会議",
        "attendee_user_ids": [],
        "attendee_count": None,
        "note": "",
    }
    body.update(overrides)
    return body


class ReservationServiceTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        db.apply_migrations(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)
        with db.transaction(self.conn):
            self.room_a = rooms_repo.insert(self.conn, "会議室A", 10, "", "", True, NOW)
            self.room_b = rooms_repo.insert(self.conn, "会議室B", 4, "", "", True, NOW)
            self.room_c = rooms_repo.insert(self.conn, "会議室C", 20, "", "", False, NOW)
            for user_id, name, role, active in [
                ("admin001", "管理 太郎", "admin", True),
                ("user001", "山田 太郎", "general", True),
                ("user002", "鈴木 花子", "general", True),
                ("user003", "退職 次郎", "general", False),
            ]:
                users_repo.insert(
                    self.conn, user_id, name, security.hash_password("Passw0rd!23"),
                    role, active, NOW,
                )
        self.actor = users_repo.find_by_id(self.conn, "user001")
        self.other = users_repo.find_by_id(self.conn, "user002")
        self.admin = users_repo.find_by_id(self.conn, "admin001")

    def req(self, **overrides):
        overrides.setdefault("room_id", self.room_a)
        return validate(ReservationRequest, _body(**overrides))

    def create(self, actor=None, **overrides):
        return reservation_service.create(self.conn, actor or self.actor, self.req(**overrides))

    def assertApiError(self, status, code, callable_, *args, **kwargs):
        with self.assertRaises(ApiError) as ctx:
            callable_(*args, **kwargs)
        self.assertEqual((ctx.exception.status, ctx.exception.code), (status, code))
        return ctx.exception


class RequestSchemaTest(ReservationServiceTestBase):
    def test_valid_body(self):
        req = self.req()
        self.assertEqual(req.attendee_user_ids, [])
        self.assertIsNone(req.attendee_count)

    def test_title_required(self):
        error = self.assertApiError(400, "VALIDATION_ERROR", self.req, title="")
        self.assertEqual(error.details[0]["field"], "title")
        self.assertEqual(error.details[0]["message"], "件名を入力してください。")

    def test_title_too_long(self):
        error = self.assertApiError(400, "VALIDATION_ERROR", self.req, title="あ" * 101)
        self.assertEqual(error.details[0]["message"], "件名は100文字以内で入力してください。")

    def test_note_too_long(self):
        error = self.assertApiError(400, "VALIDATION_ERROR", self.req, note="あ" * 501)
        self.assertEqual(error.details[0]["field"], "note")

    def test_too_many_attendees(self):
        error = self.assertApiError(
            400, "VALIDATION_ERROR", self.req,
            attendee_user_ids=[f"user{i:04d}" for i in range(51)],
        )
        self.assertEqual(error.details[0]["message"], "参加者は50名以内で選択してください。")

    def test_duplicate_attendees(self):
        error = self.assertApiError(
            400, "VALIDATION_ERROR", self.req, attendee_user_ids=["user002", "user002"]
        )
        self.assertEqual(error.details[0]["field"], "attendee_user_ids")

    def test_attendee_count_zero(self):
        error = self.assertApiError(400, "VALIDATION_ERROR", self.req, attendee_count=0)
        self.assertEqual(error.details[0]["field"], "attendee_count")

    def test_invalid_time_format(self):
        self.assertApiError(400, "VALIDATION_ERROR", self.req, start_time="9:00")

    def test_invalid_date_format(self):
        self.assertApiError(400, "VALIDATION_ERROR", self.req, reserved_date="2026/08/10")


class CreateTest(ReservationServiceTestBase):
    # 正常系: 予約が作られ、user_id はセッションのユーザーになる
    def test_create_uses_session_user(self):
        created = self.create(attendee_user_ids=["user002"], attendee_count=8)
        self.assertEqual(created["user_id"], "user001")
        self.assertEqual(created["user_name"], "山田 太郎")
        self.assertEqual(created["room_name"], "会議室A")
        self.assertEqual(created["attendees"], [{"user_id": "user002", "name": "鈴木 花子"}])

    def test_create_ignores_user_id_in_body(self):
        body = _body(room_id=self.room_a, user_id="admin001")
        created = reservation_service.create(
            self.conn, self.actor, validate(ReservationRequest, body)
        )
        self.assertEqual(created["user_id"], "user001")

    # 異常系: 30分刻み違反・業務時間外・終了 <= 開始
    def test_time_step_violation(self):
        error = self.assertApiError(400, "VALIDATION_ERROR", self.create, start_time="09:15")
        self.assertEqual(error.details[0]["field"], "start_time")

    def test_before_business_hours(self):
        error = self.assertApiError(400, "VALIDATION_ERROR", self.create, start_time="07:30")
        self.assertEqual(error.details[0]["field"], "start_time")

    def test_after_business_hours(self):
        error = self.assertApiError(
            400, "VALIDATION_ERROR", self.create, start_time="19:30", end_time="20:30"
        )
        self.assertEqual(error.details[0]["field"], "end_time")

    def test_end_not_after_start(self):
        error = self.assertApiError(
            400, "VALIDATION_ERROR", self.create, start_time="11:00", end_time="10:00"
        )
        self.assertEqual(error.details[0]["message"], "終了時刻は開始時刻より後にしてください。")

    # 異常系: 過去日
    def test_past_date(self):
        error = self.assertApiError(400, "VALIDATION_ERROR", self.create, reserved_date=_date(-1))
        self.assertEqual(error.details[0]["field"], "reserved_date")
        self.assertEqual(error.details[0]["message"], "過去の日付には予約できません。")

    # 異常系: 存在しない/無効な会議室
    def test_unknown_room(self):
        error = self.assertApiError(400, "VALIDATION_ERROR", self.create, room_id=9999)
        self.assertEqual(error.details[0]["field"], "room_id")

    def test_inactive_room(self):
        error = self.assertApiError(400, "VALIDATION_ERROR", self.create, room_id=self.room_c)
        self.assertEqual(error.details[0]["field"], "room_id")

    # 異常系/境界値: 収容人数
    def test_capacity_exceeded(self):
        error = self.assertApiError(
            400, "CAPACITY_EXCEEDED", self.create, room_id=self.room_b, attendee_count=5
        )
        self.assertIn("4", error.message)

    def test_capacity_exact(self):
        created = self.create(room_id=self.room_b, attendee_count=4)
        self.assertEqual(created["attendee_count"], 4)

    # 異常系: 無効なユーザーを参加者に指定
    def test_inactive_attendee(self):
        error = self.assertApiError(
            400, "VALIDATION_ERROR", self.create, attendee_user_ids=["user003"]
        )
        self.assertEqual(error.details[0]["field"], "attendee_user_ids")

    def test_unknown_attendee(self):
        self.assertApiError(
            400, "VALIDATION_ERROR", self.create, attendee_user_ids=["nosuchuser"]
        )


class ConflictTest(ReservationServiceTestBase):
    def setUp(self):
        super().setUp()
        self.existing = self.create(start_time="10:00", end_time="11:00")

    def test_conflict_returns_409_with_conflicts(self):
        error = self.assertApiError(
            409, "RESERVATION_CONFLICT", self.create, start_time="10:30", end_time="11:30"
        )
        self.assertEqual(error.message, "選択した時間帯はすでに予約されています。")
        self.assertEqual(
            error.extra["conflicts"],
            [{
                "reservation_id": self.existing["reservation_id"],
                "start_time": "10:00",
                "end_time": "11:00",
            }],
        )

    def test_touching_boundary_after_succeeds(self):
        created = self.create(start_time="11:00", end_time="12:00")
        self.assertEqual(created["start_time"], "11:00")

    def test_touching_boundary_before_succeeds(self):
        created = self.create(start_time="09:00", end_time="10:00")
        self.assertEqual(created["end_time"], "10:00")

    def test_other_room_succeeds(self):
        created = self.create(room_id=self.room_b, start_time="10:00", end_time="11:00")
        self.assertEqual(created["room_id"], self.room_b)

    def test_conflicts_limited_to_five(self):
        # 08:00-08:30 〜 09:30-10:00 の4件を追加し、既存の10:00-11:00と合わせて6件と重なる枠を作る
        for start, end in [
            ("08:00", "08:30"), ("08:30", "09:00"), ("09:00", "09:30"), ("09:30", "10:00"),
        ]:
            self.create(start_time=start, end_time=end)
        self.create(start_time="11:00", end_time="11:30")
        error = self.assertApiError(
            409, "RESERVATION_CONFLICT", self.create, start_time="08:00", end_time="12:00"
        )
        self.assertEqual(len(error.extra["conflicts"]), 5)


class UpdateDeleteTest(ReservationServiceTestBase):
    def setUp(self):
        super().setUp()
        self.reservation = self.create(attendee_user_ids=["user002"])
        self.reservation_id = self.reservation["reservation_id"]

    # 正常系: 同じ時間帯のまま件名だけ変更できる(自己除外)
    def test_update_same_slot_different_title(self):
        updated = reservation_service.update(
            self.conn, self.actor, self.reservation_id,
            self.req(title="臨時会議", attendee_user_ids=[]),
        )
        self.assertEqual(updated["title"], "臨時会議")
        self.assertEqual(updated["attendees"], [])

    def test_update_by_admin(self):
        updated = reservation_service.update(
            self.conn, self.admin, self.reservation_id, self.req(title="管理者更新")
        )
        self.assertEqual(updated["title"], "管理者更新")
        self.assertEqual(updated["user_id"], "user001")  # 予約者は変わらない

    def test_update_by_third_party_forbidden(self):
        self.assertApiError(
            403, "FORBIDDEN", reservation_service.update,
            self.conn, self.other, self.reservation_id, self.req(title="乗っ取り"),
        )

    def test_update_missing(self):
        self.assertApiError(
            404, "NOT_FOUND", reservation_service.update,
            self.conn, self.actor, 9999, self.req(),
        )

    def test_update_conflicts_with_other_reservation(self):
        self.create(start_time="13:00", end_time="14:00")
        self.assertApiError(
            409, "RESERVATION_CONFLICT", reservation_service.update,
            self.conn, self.actor, self.reservation_id,
            self.req(start_time="13:00", end_time="14:00"),
        )

    # 正常系: 取消で行と参加者行が消える
    def test_delete_removes_rows(self):
        reservation_service.delete(self.conn, self.actor, self.reservation_id)
        self.assertIsNone(reservations_repo.find_by_id(self.conn, self.reservation_id))
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) AS c FROM reservation_attendees").fetchone()["c"],
            0,
        )

    def test_delete_by_admin(self):
        reservation_service.delete(self.conn, self.admin, self.reservation_id)
        self.assertIsNone(reservations_repo.find_by_id(self.conn, self.reservation_id))

    def test_delete_by_third_party_forbidden(self):
        self.assertApiError(
            403, "FORBIDDEN", reservation_service.delete,
            self.conn, self.other, self.reservation_id,
        )

    def test_delete_missing(self):
        self.assertApiError(
            404, "NOT_FOUND", reservation_service.delete, self.conn, self.actor, 9999
        )

    # 異常系: 過去日の予約の更新・取消は 409 CONSTRAINT_VIOLATION
    def _insert_past(self):
        with db.transaction(self.conn):
            return reservations_repo.insert(
                self.conn, self.room_a, "user001", _date(-2), "10:00", "11:00",
                "過去の会議", None, "", NOW,
            )

    def test_update_past_reservation(self):
        past_id = self._insert_past()
        error = self.assertApiError(
            409, "CONSTRAINT_VIOLATION", reservation_service.update,
            self.conn, self.actor, past_id, self.req(),
        )
        self.assertEqual(error.message, "過去の予約は編集できません。")

    def test_delete_past_reservation(self):
        past_id = self._insert_past()
        self.assertApiError(
            409, "CONSTRAINT_VIOLATION", reservation_service.delete,
            self.conn, self.actor, past_id,
        )


class CountFutureReservationsTest(ReservationServiceTestBase):
    """U003-T2 完了条件: `room_service.count_future_reservations` の本実装(TODO解消)。"""

    def test_counts_only_future(self):
        self.create(reserved_date=_date(1))
        with db.transaction(self.conn):
            reservations_repo.insert(
                self.conn, self.room_a, "user001", _date(-3), "10:00", "11:00",
                "過去の会議", None, "", NOW,
            )
        self.assertEqual(room_service.count_future_reservations(self.conn, self.room_a), 1)
        self.assertEqual(room_service.count_future_reservations(self.conn, self.room_b), 0)

    def test_deactivate_room_blocked_by_future_reservation(self):
        self.create(reserved_date=_date(1))
        error = self.assertApiError(
            409, "CONSTRAINT_VIOLATION", room_service.deactivate_room, self.conn, self.room_a
        )
        self.assertIn("1", error.message)


class ConcurrentCreateTest(ReservationServiceTestBase):
    """P003 5.3。同一枠への同時 `create` は必ず一方だけが成功する。

    片方が 500 `INTERNAL_ERROR`(ロックタイムアウト)になった場合もFAILとする(U003-T2)。
    """

    def _worker(self, results, index):
        conn = db.connect(self.db_path)
        try:
            body = _body(
                room_id=self.room_a, start_time="15:00", end_time="16:00",
                title=f"同時実行{index}",
            )
            reservation_service.create(conn, self.actor, validate(ReservationRequest, body))
            results[index] = ("OK", None)
        except ApiError as exc:
            results[index] = ("ERROR", (exc.status, exc.code))
        except sqlite3.Error as exc:  # 素のsqlite3例外が漏れた場合も記録する
            results[index] = ("SQLITE", str(exc))
        finally:
            conn.close()

    def test_only_one_succeeds(self):
        barrier = threading.Barrier(2)
        results = {}

        def run(index):
            barrier.wait()
            self._worker(results, index)

        threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        outcomes = [results[i] for i in range(2)]
        successes = [o for o in outcomes if o[0] == "OK"]
        failures = [o for o in outcomes if o[0] != "OK"]
        self.assertEqual(len(successes), 1, f"成功が1件でない: {outcomes}")
        self.assertEqual(len(failures), 1, f"失敗が1件でない: {outcomes}")
        self.assertEqual(failures[0], ("ERROR", (409, "RESERVATION_CONFLICT")), outcomes)
        rows = self.conn.execute(
            "SELECT COUNT(*) AS c FROM reservations WHERE start_time = '15:00'"
        ).fetchone()
        self.assertEqual(rows["c"], 1)

    def test_repeated_concurrency_is_stable(self):
        # 同時実行を5回繰り返しても、常に1件だけがDBに残る(時間帯を変えて繰り返す)
        for hour in range(9, 14):
            barrier = threading.Barrier(2)
            results = {}
            start, end = f"{hour:02d}:00", f"{hour:02d}:30"

            def run(index, start=start, end=end):
                barrier.wait()
                conn = db.connect(self.db_path)
                try:
                    body = _body(
                        room_id=self.room_a, start_time=start, end_time=end, title="繰り返し"
                    )
                    reservation_service.create(
                        conn, self.actor, validate(ReservationRequest, body)
                    )
                    results[index] = ("OK", None)
                except ApiError as exc:
                    results[index] = ("ERROR", (exc.status, exc.code))
                finally:
                    conn.close()

            threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)
            outcomes = [results[i] for i in range(2)]
            self.assertEqual(
                len([o for o in outcomes if o[0] == "OK"]), 1, f"{start}: {outcomes}"
            )
            self.assertEqual(
                self.conn.execute(
                    "SELECT COUNT(*) AS c FROM reservations WHERE start_time = ?", (start,)
                ).fetchone()["c"],
                1,
            )


if __name__ == "__main__":
    unittest.main()
