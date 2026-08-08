"""U003-T4 単体テスト — 予約の更新系API(API-15・API-16・API-17。P002 5.7 / 5.2)。"""

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


class ReservationWriteApiTestBase(unittest.TestCase):
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
            for user_id, name, role in [
                ("user001", "山田 太郎", "general"),
                ("user002", "鈴木 花子", "general"),
                ("adminx001", "管理 太郎", "admin"),
            ]:
                users_repo.insert(
                    self.conn, user_id, name, security.hash_password("Passw0rd!23"),
                    role, True, NOW,
                )
        self.client = TestClient(self.app, base_url="https://testserver")
        self.addCleanup(self.client.close)

    def login(self, user_id="user001"):
        self.client.cookies.clear()
        res = self.client.post(
            "/api/auth/login", json={"user_id": user_id, "password": "Passw0rd!23"}
        )
        self.assertEqual(res.status_code, 200)

    def body(self, **overrides):
        payload = {
            "room_id": self.room_a,
            "reserved_date": _date(1),
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例会議",
            "attendee_user_ids": [],
            "attendee_count": None,
            "note": "",
        }
        payload.update(overrides)
        return payload

    def create(self, **overrides):
        return self.client.post("/api/reservations", json=self.body(**overrides))


class CreateApiTest(ReservationWriteApiTestBase):
    # 正常系: 201 + { "reservation": ... }
    def test_create_returns_201(self):
        self.login()
        res = self.create(attendee_user_ids=["user002"], attendee_count=8, note="資料は事前配布")
        self.assertEqual(res.status_code, 201)
        reservation = res.json()["reservation"]
        self.assertIsInstance(reservation["reservation_id"], int)
        self.assertEqual(reservation["user_id"], "user001")
        self.assertEqual(reservation["attendees"], [{"user_id": "user002", "name": "鈴木 花子"}])
        self.assertEqual(reservation["attendee_count"], 8)

    # 異常系: ボディの user_id は無視される
    def test_body_user_id_is_ignored(self):
        self.login("user002")
        res = self.create(user_id="user001")
        self.assertEqual(res.json()["reservation"]["user_id"], "user002")

    # 異常系: 重複登録は 409 + error.conflicts
    def test_conflict_returns_409_with_conflicts(self):
        self.login()
        first = self.create().json()["reservation"]
        res = self.create(start_time="10:30", end_time="11:30")
        self.assertEqual(res.status_code, 409)
        error = res.json()["error"]
        self.assertEqual(error["code"], "RESERVATION_CONFLICT")
        self.assertEqual(error["message"], "選択した時間帯はすでに予約されています。")
        self.assertEqual(len(error["conflicts"]), 1)
        conflict = error["conflicts"][0]
        self.assertEqual(set(conflict), {"reservation_id", "start_time", "end_time"})
        self.assertEqual(conflict["reservation_id"], first["reservation_id"])

    def test_boundary_touch_succeeds(self):
        self.login()
        self.create()
        self.assertEqual(self.create(start_time="11:00", end_time="12:00").status_code, 201)

    # 異常系: 収容人数超過は 400 CAPACITY_EXCEEDED
    def test_capacity_exceeded(self):
        self.login()
        res = self.create(room_id=self.room_b, attendee_count=5)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], "CAPACITY_EXCEEDED")
        self.assertIn("4", res.json()["error"]["message"])

    def test_validation_error_shape(self):
        self.login()
        res = self.create(title="")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(res.json()["error"]["details"][0]["field"], "title")

    def test_requires_login(self):
        self.assertEqual(self.create().status_code, 401)


class UpdateDeleteApiTest(ReservationWriteApiTestBase):
    def setUp(self):
        super().setUp()
        self.login()
        self.reservation_id = self.create(
            attendee_user_ids=["user002"]
        ).json()["reservation"]["reservation_id"]

    # 正常系: 更新は 200
    def test_update_returns_200(self):
        res = self.client.put(
            f"/api/reservations/{self.reservation_id}", json=self.body(title="臨時会議")
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["reservation"]["title"], "臨時会議")
        self.assertEqual(res.json()["reservation"]["attendees"], [])

    # 正常系: 取消は 204 で本文が空、その後 API-14 が 404
    def test_delete_returns_204_and_then_404(self):
        res = self.client.delete(f"/api/reservations/{self.reservation_id}")
        self.assertEqual(res.status_code, 204)
        self.assertEqual(res.content, b"")
        self.assertEqual(
            self.client.get(f"/api/reservations/{self.reservation_id}").status_code, 404
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT COUNT(*) AS c FROM reservation_attendees"
            ).fetchone()["c"],
            0,
        )

    # 正常系: 管理者は他人の予約を更新・取消できる
    def test_admin_can_update_and_delete(self):
        self.login("adminx001")
        self.assertEqual(
            self.client.put(
                f"/api/reservations/{self.reservation_id}", json=self.body(title="管理者更新")
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.delete(f"/api/reservations/{self.reservation_id}").status_code, 204
        )

    # 異常系: 第三者は 403
    def test_third_party_forbidden(self):
        self.login("user002")
        put = self.client.put(
            f"/api/reservations/{self.reservation_id}", json=self.body(title="乗っ取り")
        )
        self.assertEqual(put.status_code, 403)
        self.assertEqual(put.json()["error"]["code"], "FORBIDDEN")
        delete = self.client.delete(f"/api/reservations/{self.reservation_id}")
        self.assertEqual(delete.status_code, 403)
        # DBの予約は変化していない
        row = reservations_repo.find_by_id(self.conn, self.reservation_id)
        self.assertEqual(row["title"], "定例会議")

    def test_update_conflict_returns_409(self):
        self.create(start_time="13:00", end_time="14:00")
        res = self.client.put(
            f"/api/reservations/{self.reservation_id}",
            json=self.body(start_time="13:00", end_time="14:00"),
        )
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "RESERVATION_CONFLICT")

    def test_update_same_slot_excludes_self(self):
        res = self.client.put(
            f"/api/reservations/{self.reservation_id}", json=self.body(title="件名だけ変更")
        )
        self.assertEqual(res.status_code, 200)

    def test_unknown_id(self):
        self.assertEqual(
            self.client.put("/api/reservations/9999", json=self.body()).status_code, 404
        )
        self.assertEqual(self.client.delete("/api/reservations/9999").status_code, 404)

    def test_requires_login(self):
        self.client.cookies.clear()
        self.assertEqual(
            self.client.put(
                f"/api/reservations/{self.reservation_id}", json=self.body()
            ).status_code,
            401,
        )
        self.assertEqual(
            self.client.delete(f"/api/reservations/{self.reservation_id}").status_code, 401
        )


class MeetingUrlApiTest(ReservationWriteApiTestBase):
    """※CR-001 オンライン会議URLの検証と往復(P002 3.3 / 5.3 / 5.7、ADR-011)。"""

    URL = "https://example.com/meet/abc"
    LENGTH_MESSAGE = "オンライン会議URLは500文字以内で入力してください。"
    SCHEME_MESSAGE = "オンライン会議URLは http:// または https:// で始まるURLを入力してください。"

    def setUp(self):
        super().setUp()
        self.login("user001")

    def _detail_of(self, res):
        return res.json()["reservation"]

    def _field_errors(self, res):
        return [
            d["message"]
            for d in res.json()["error"].get("details", [])
            if d["field"] == "meeting_url"
        ]

    # 正常系: キーを送らない場合は空文字で登録される
    def test_absent_key_is_empty_string(self):
        payload = self.body()
        payload.pop("meeting_url", None)
        res = self.client.post("/api/reservations", json=payload)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(self._detail_of(res)["meeting_url"], "")

    # 正常系: null・空文字も空文字として扱う
    def test_null_and_empty_are_empty_string(self):
        res = self.create(meeting_url=None, start_time="11:00", end_time="12:00")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(self._detail_of(res)["meeting_url"], "")
        res = self.create(meeting_url="", start_time="12:00", end_time="13:00")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(self._detail_of(res)["meeting_url"], "")

    # 正常系: https:// / http:// が登録でき、API-14 でも返る
    def test_https_and_http_are_accepted(self):
        res = self.create(meeting_url=self.URL)
        self.assertEqual(res.status_code, 201)
        rid = self._detail_of(res)["reservation_id"]
        self.assertEqual(self._detail_of(res)["meeting_url"], self.URL)
        got = self.client.get(f"/api/reservations/{rid}")
        self.assertEqual(got.json()["reservation"]["meeting_url"], self.URL)

        res = self.create(
            meeting_url="http://example.com/x", start_time="14:00", end_time="15:00"
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(self._detail_of(res)["meeting_url"], "http://example.com/x")

    # 正常系: 500文字ちょうどは通る(境界値)
    def test_500_chars_is_accepted(self):
        url = "https://" + ("a" * 492)
        self.assertEqual(len(url), 500)
        res = self.create(meeting_url=url)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(len(self._detail_of(res)["meeting_url"]), 500)

    # 異常系: 501文字は 400(境界値)
    def test_501_chars_is_rejected(self):
        url = "https://" + ("a" * 493)
        self.assertEqual(len(url), 501)
        res = self.create(meeting_url=url)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn(self.LENGTH_MESSAGE, self._field_errors(res))

    # 異常系: スキームが無い / http(s) 以外は 400
    def test_invalid_scheme_is_rejected(self):
        for value in ("example.com/meet", "ftp://example.com/meet", "//example.com", "HTTP://example.com"):
            with self.subTest(value=value):
                res = self.create(meeting_url=value)
                self.assertEqual(res.status_code, 400)
                self.assertIn(self.SCHEME_MESSAGE, self._field_errors(res))

    # 異常系: 文字数超過とスキーム違反の両方に違反する場合は文字数のメッセージ(P002 3.3 の判定順序)
    def test_length_is_checked_before_scheme(self):
        res = self.create(meeting_url="ftp://" + ("a" * 495))
        self.assertEqual(res.status_code, 400)
        self.assertIn(self.LENGTH_MESSAGE, self._field_errors(res))
        self.assertNotIn(self.SCHEME_MESSAGE, self._field_errors(res))

    # 異常系: 検証エラーのとき予約は作られない
    def test_rejected_request_does_not_create_reservation(self):
        before = self.client.get(
            f"/api/reservations?date_from={_date(1)}&date_to={_date(1)}"
        ).json()["reservations"]
        self.create(meeting_url="ftp://example.com")
        after = self.client.get(
            f"/api/reservations?date_from={_date(1)}&date_to={_date(1)}"
        ).json()["reservations"]
        self.assertEqual(len(before), len(after))

    # 正常系: API-16 は全置換更新であり、空文字を送るとURLが消える
    def test_update_replaces_and_clears_meeting_url(self):
        rid = self._detail_of(self.create(meeting_url=self.URL))["reservation_id"]
        res = self.client.put(
            f"/api/reservations/{rid}", json=self.body(meeting_url="https://example.com/new")
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self._detail_of(res)["meeting_url"], "https://example.com/new")
        res = self.client.put(f"/api/reservations/{rid}", json=self.body(meeting_url=""))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self._detail_of(res)["meeting_url"], "")

    # 異常系: API-16 でも同じ検証が働く
    def test_update_validates_meeting_url(self):
        rid = self._detail_of(self.create(meeting_url=self.URL))["reservation_id"]
        res = self.client.put(
            f"/api/reservations/{rid}", json=self.body(meeting_url="example.com")
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn(self.SCHEME_MESSAGE, self._field_errors(res))
        got = self.client.get(f"/api/reservations/{rid}")
        self.assertEqual(got.json()["reservation"]["meeting_url"], self.URL)  # 変更されていない


if __name__ == "__main__":
    unittest.main()
