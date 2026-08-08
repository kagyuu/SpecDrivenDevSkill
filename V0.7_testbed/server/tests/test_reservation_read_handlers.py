"""U003-T3 単体テスト — 予約の参照系API(API-12・API-13・API-14。P002 5.7 / P003 6.4)。"""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from starlette.testclient import TestClient

from meeting_room import db, main, security
from meeting_room.repositories import reservations_repo, rooms_repo, users_repo

NOW = "2026-08-05T00:00:00Z"


def _date(offset_days: int) -> str:
    return (datetime.now() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


class ReservationReadApiTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        self.app = main.create_app(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)
        with db.transaction(self.conn):
            self.room_a = rooms_repo.insert(self.conn, "会議室A", 10, "", "", True, NOW)
            self.room_b = rooms_repo.insert(self.conn, "会議室B", 4, "", "", True, NOW)
            for user_id, name in [("user001", "山田 太郎"), ("user002", "鈴木 花子")]:
                users_repo.insert(
                    self.conn, user_id, name, security.hash_password("Passw0rd!23"),
                    "general", True, NOW,
                )
        self.client = TestClient(self.app, base_url="https://testserver")
        self.addCleanup(self.client.close)

    def login(self, user_id="user001"):
        self.client.cookies.clear()
        res = self.client.post(
            "/api/auth/login", json={"user_id": user_id, "password": "Passw0rd!23"}
        )
        self.assertEqual(res.status_code, 200)

    def _insert(
        self, room_id=None, user_id="user001", reserved_date=None,
        start_time="10:00", end_time="11:00", title="定例会議", attendees=(),
        meeting_url="",
    ):
        with db.transaction(self.conn):
            reservation_id = reservations_repo.insert(
                self.conn, self.room_a if room_id is None else room_id, user_id,
                reserved_date or _date(1), start_time, end_time, title, None, "", NOW,
                meeting_url=meeting_url,
            )
            reservations_repo.replace_attendees(self.conn, reservation_id, list(attendees))
        return reservation_id


class ListReservationsTest(ReservationReadApiTestBase):
    # 正常系: 期間内の予約のみが reserved_date, start_time, room_id 昇順で返る
    def test_list_period_and_order(self):
        self._insert(reserved_date=_date(2), start_time="09:00", end_time="10:00")
        self._insert(reserved_date=_date(1), start_time="11:00", end_time="12:00")
        self._insert(room_id=self.room_b, reserved_date=_date(1), start_time="09:00",
                     end_time="10:00")
        self._insert(reserved_date=_date(1), start_time="09:00", end_time="10:00")
        self._insert(reserved_date=_date(10))  # 範囲外
        self.login()
        res = self.client.get(
            f"/api/reservations?date_from={_date(0)}&date_to={_date(6)}"
        )
        self.assertEqual(res.status_code, 200)
        rows = res.json()["reservations"]
        self.assertEqual(
            [(r["reserved_date"], r["start_time"], r["room_id"]) for r in rows],
            [
                (_date(1), "09:00", self.room_a),
                (_date(1), "09:00", self.room_b),
                (_date(1), "11:00", self.room_a),
                (_date(2), "09:00", self.room_a),
            ],
        )
        # 一覧では attendees は空配列(P002 5.7 API-12)
        self.assertTrue(all(r["attendees"] == [] for r in rows))
        self.assertEqual(rows[0]["room_name"], "会議室A")
        self.assertEqual(rows[0]["user_name"], "山田 太郎")

    def test_list_attendees_is_empty_even_when_present(self):
        self._insert(attendees=["user002"])
        self.login()
        rows = self.client.get(
            f"/api/reservations?date_from={_date(0)}&date_to={_date(6)}"
        ).json()["reservations"]
        self.assertEqual(rows[0]["attendees"], [])

    def test_list_filters_by_room_id(self):
        self._insert()
        self._insert(room_id=self.room_b)
        self.login()
        rows = self.client.get(
            f"/api/reservations?date_from={_date(0)}&date_to={_date(6)}&room_id={self.room_b}"
        ).json()["reservations"]
        self.assertEqual([r["room_id"] for r in rows], [self.room_b])

    def test_list_accepts_repeated_room_id(self):
        self._insert()
        self._insert(room_id=self.room_b)
        self.login()
        rows = self.client.get(
            f"/api/reservations?date_from={_date(0)}&date_to={_date(6)}"
            f"&room_id={self.room_a}&room_id={self.room_b}"
        ).json()["reservations"]
        self.assertEqual(len(rows), 2)

    # 異常系
    def test_missing_date_from(self):
        self.login()
        res = self.client.get(f"/api/reservations?date_to={_date(6)}")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(res.json()["error"]["details"][0]["field"], "date_from")

    def test_date_to_before_date_from(self):
        self.login()
        res = self.client.get(
            f"/api/reservations?date_from={_date(6)}&date_to={_date(1)}"
        )
        self.assertEqual(res.status_code, 400)

    def test_period_31_days_ok(self):
        self.login()
        res = self.client.get(
            f"/api/reservations?date_from={_date(0)}&date_to={_date(30)}"
        )
        self.assertEqual(res.status_code, 200)

    def test_period_32_days_rejected(self):
        self.login()
        res = self.client.get(
            f"/api/reservations?date_from={_date(0)}&date_to={_date(31)}"
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")

    def test_requires_login(self):
        res = self.client.get(
            f"/api/reservations?date_from={_date(0)}&date_to={_date(6)}"
        )
        self.assertEqual(res.status_code, 401)


class MyReservationsTest(ReservationReadApiTestBase):
    # 正常系: /mine が予約IDとして解釈されない(ルーティング順序の確認)
    def test_mine_route_is_not_captured_as_id(self):
        self._insert()
        self.login()
        res = self.client.get("/api/reservations/mine")
        self.assertEqual(res.status_code, 200)
        self.assertIn("reservations", res.json())

    def test_upcoming_is_default_and_ascending(self):
        self._insert(reserved_date=_date(3))
        self._insert(reserved_date=_date(1))
        self._insert(reserved_date=_date(-2))
        self.login()
        rows = self.client.get("/api/reservations/mine").json()["reservations"]
        self.assertEqual([r["reserved_date"] for r in rows], [_date(1), _date(3)])

    def test_past_is_descending(self):
        self._insert(reserved_date=_date(-2))
        self._insert(reserved_date=_date(-5))
        self._insert(reserved_date=_date(1))
        self.login()
        rows = self.client.get("/api/reservations/mine?period=past").json()["reservations"]
        self.assertEqual([r["reserved_date"] for r in rows], [_date(-2), _date(-5)])

    def test_only_own_reservations(self):
        self._insert(user_id="user002")
        self._insert(user_id="user001")
        self.login("user001")
        rows = self.client.get("/api/reservations/mine").json()["reservations"]
        self.assertEqual([r["user_id"] for r in rows], ["user001"])

    def test_invalid_period(self):
        self.login()
        res = self.client.get("/api/reservations/mine?period=future")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["details"][0]["field"], "period")

    def test_requires_login(self):
        self.assertEqual(self.client.get("/api/reservations/mine").status_code, 401)


class ReservationDetailTest(ReservationReadApiTestBase):
    # 正常系: attendees と room_name / user_name を含む
    def test_detail_includes_attendees_and_names(self):
        reservation_id = self._insert(attendees=["user002"])
        self.login()
        res = self.client.get(f"/api/reservations/{reservation_id}")
        self.assertEqual(res.status_code, 200)
        reservation = res.json()["reservation"]
        self.assertEqual(reservation["room_name"], "会議室A")
        self.assertEqual(reservation["user_name"], "山田 太郎")
        self.assertEqual(reservation["attendees"], [{"user_id": "user002", "name": "鈴木 花子"}])

    # 正常系: 他人の予約も閲覧できる(権限制限をかけない)
    def test_other_users_reservation_is_readable(self):
        reservation_id = self._insert(user_id="user001")
        self.login("user002")
        self.assertEqual(
            self.client.get(f"/api/reservations/{reservation_id}").status_code, 200
        )

    def test_unknown_id_returns_404(self):
        self.login()
        res = self.client.get("/api/reservations/9999")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["error"]["code"], "NOT_FOUND")

    def test_non_numeric_id_returns_404(self):
        self.login()
        self.assertEqual(self.client.get("/api/reservations/abc").status_code, 404)

    def test_requires_login(self):
        reservation_id = self._insert()
        self.assertEqual(
            self.client.get(f"/api/reservations/{reservation_id}").status_code, 401
        )


class MeetingUrlInReadApisTest(ReservationReadApiTestBase):
    """※CR-001 参照系APIの `Reservation` 表現に `meeting_url` が含まれる(P002 5.3)。"""

    URL = "https://example.com/meet/read"

    def setUp(self):
        super().setUp()
        self.login("user001")

    # 正常系: API-12(一覧)の各要素に meeting_url がある(S02は表示しないが応答には含む)
    def test_list_includes_meeting_url(self):
        self._insert(meeting_url=self.URL)
        self._insert(start_time="13:00", end_time="14:00")  # 未登録の予約
        res = self.client.get(f"/api/reservations?date_from={_date(1)}&date_to={_date(1)}")
        self.assertEqual(res.status_code, 200)
        values = [r["meeting_url"] for r in res.json()["reservations"]]
        self.assertIn(self.URL, values)
        self.assertIn("", values)

    # 正常系: API-13(マイ予約)にも含まれる
    def test_mine_includes_meeting_url(self):
        self._insert(meeting_url=self.URL)
        res = self.client.get("/api/reservations/mine")
        self.assertEqual(res.json()["reservations"][0]["meeting_url"], self.URL)

    # 正常系: API-14(詳細)。未登録は空文字で、null ではない
    def test_detail_returns_empty_string_when_not_set(self):
        rid = self._insert()
        res = self.client.get(f"/api/reservations/{rid}")
        self.assertEqual(res.json()["reservation"]["meeting_url"], "")


if __name__ == "__main__":
    unittest.main()
