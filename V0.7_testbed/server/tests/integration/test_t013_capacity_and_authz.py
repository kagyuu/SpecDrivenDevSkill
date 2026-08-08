"""T013 — 収容人数超過と予約の認可(docs/P008-test-direction/T013-capacity-and-authz.md)。

時間帯は T013 の【使用するテストデータ】(P011矛盾点#4にもとづく明記)に従う。
既存予約は「本日+1日」13:00-14:00、新規登録は 16:00-17:00。
"""

import unittest
from datetime import datetime, timedelta

from tests.integration.support import IntegrationTestCase


def _date(offset_days: int) -> str:
    return (datetime.now() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


class T013CapacityAndAuthzTest(IntegrationTestCase):
    seed_rooms = True

    def setUp(self):
        super().setUp()
        self.assertEqual(self.login("user001").status_code, 200)
        rooms = self.client.get("/api/rooms?include_inactive=true")
        # 一般ユーザーは include_inactive を使えないため、管理者で会議室IDを引く
        self.assertEqual(rooms.status_code, 403)
        self.assertEqual(self.login("admin001").status_code, 200)
        all_rooms = self.client.get("/api/rooms?include_inactive=true").json()["rooms"]
        self.room_b = next(r["room_id"] for r in all_rooms if r["name"] == "会議室B")
        self.room_c = next(r["room_id"] for r in all_rooms if r["name"] == "会議室C")

        # 事前準備2: user001 で会議室Bに「本日+1日」13:00-14:00 の予約を1件作る
        self.assertEqual(self.login("user001").status_code, 200)
        res = self.client.post("/api/reservations", json=self._body("13:00", "14:00"))
        self.assertEqual(res.status_code, 201, res.text)
        self.existing_id = res.json()["reservation"]["reservation_id"]

    def _body(self, start="16:00", end="17:00", room_id=None, reserved_date=None, **extra):
        body = {
            "room_id": self.room_b if room_id is None else room_id,
            "reserved_date": reserved_date or _date(1),
            "start_time": start,
            "end_time": end,
            "title": "打合せ",
            "attendee_user_ids": [],
            "attendee_count": None,
            "note": "",
        }
        body.update(extra)
        return body

    def test_capacity_and_authz(self):
        # 手順1: attendee_count=5 は収容人数(4)超過 → 400 CAPACITY_EXCEEDED
        res = self.client.post("/api/reservations", json=self._body(attendee_count=5))
        self.assertEqual(res.status_code, 400, res.text)
        self.assertEqual(res.json()["error"]["code"], "CAPACITY_EXCEEDED")
        self.assertIn("4", res.json()["error"]["message"])

        # 手順2: attendee_count=4(境界値)は 201
        res = self.client.post("/api/reservations", json=self._body(attendee_count=4))
        self.assertEqual(res.status_code, 201, res.text)
        created_id = res.json()["reservation"]["reservation_id"]

        # 手順3: 取り消してから attendee_count=0 → 400、未指定 → 201
        self.assertEqual(self.client.delete(f"/api/reservations/{created_id}").status_code, 204)
        res = self.client.post("/api/reservations", json=self._body(attendee_count=0))
        self.assertEqual(res.status_code, 400, res.text)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
        res = self.client.post("/api/reservations", json=self._body())
        self.assertEqual(res.status_code, 201, res.text)
        self.assertEqual(
            self.client.delete(
                f"/api/reservations/{res.json()['reservation']['reservation_id']}"
            ).status_code,
            204,
        )

        # 手順4: 無効な会議室C → 400 VALIDATION_ERROR(field == "room_id")
        res = self.client.post("/api/reservations", json=self._body(room_id=self.room_c))
        self.assertEqual(res.status_code, 400, res.text)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(res.json()["error"]["details"][0]["field"], "room_id")

        # 手順5: 「本日-1日」 → 400 VALIDATION_ERROR(field == "reserved_date")
        res = self.client.post("/api/reservations", json=self._body(reserved_date=_date(-1)))
        self.assertEqual(res.status_code, 400, res.text)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(res.json()["error"]["details"][0]["field"], "reserved_date")

        # 手順6・7: 第三者(user002)による PUT / DELETE → 403 FORBIDDEN
        self.assertEqual(self.login("user002").status_code, 200)
        res = self.client.put(
            f"/api/reservations/{self.existing_id}",
            json=self._body("13:00", "14:00", title="乗っ取り"),
        )
        self.assertEqual(res.status_code, 403, res.text)
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")
        res = self.client.delete(f"/api/reservations/{self.existing_id}")
        self.assertEqual(res.status_code, 403, res.text)
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")
        # DBの予約が変化していない
        row = self.db().execute(
            "SELECT title FROM reservations WHERE reservation_id = ?", (self.existing_id,)
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["title"], "打合せ")

        # 手順8: 第三者でも閲覧はできる
        self.assertEqual(
            self.client.get(f"/api/reservations/{self.existing_id}").status_code, 200
        )

        # 手順9: 管理者は他人の予約を PUT / DELETE できる
        self.assertEqual(self.login("admin001").status_code, 200)
        res = self.client.put(
            f"/api/reservations/{self.existing_id}",
            json=self._body("13:00", "14:00", title="管理者更新"),
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(
            self.client.delete(f"/api/reservations/{self.existing_id}").status_code, 204
        )


if __name__ == "__main__":
    unittest.main()
