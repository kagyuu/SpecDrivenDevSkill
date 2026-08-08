"""T012 — 予約の重複検出と境界時刻(docs/P008-test-direction/T012-reservation-conflict.md)。"""

import unittest
from datetime import datetime, timedelta

from tests.integration.support import IntegrationTestCase


def _date(offset_days: int) -> str:
    return (datetime.now() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


class T012ReservationConflictTest(IntegrationTestCase):
    seed_rooms = True

    def setUp(self):
        super().setUp()
        self.assertEqual(self.login("user001").status_code, 200)
        rooms = self.client.get("/api/rooms").json()["rooms"]
        self.room_a = next(r["room_id"] for r in rooms if r["name"] == "会議室A")
        self.room_b = next(r["room_id"] for r in rooms if r["name"] == "会議室B")
        self.date = _date(1)
        # 事前準備: 既存予約 10:00-11:00 を1件登録する
        res = self._post("10:00", "11:00")
        self.assertEqual(res.status_code, 201, res.text)
        self.existing_id = res.json()["reservation"]["reservation_id"]

    def _body(self, start, end, room_id=None, reserved_date=None, title="定例会議"):
        return {
            "room_id": self.room_a if room_id is None else room_id,
            "reserved_date": reserved_date or self.date,
            "start_time": start,
            "end_time": end,
            "title": title,
            "attendee_user_ids": [],
            "attendee_count": None,
            "note": "",
        }

    def _post(self, start, end, **kwargs):
        return self.client.post("/api/reservations", json=self._body(start, end, **kwargs))

    def _assert_conflict(self, res, step):
        self.assertEqual(res.status_code, 409, f"{step}: {res.text}")
        error = res.json()["error"]
        self.assertEqual(error["code"], "RESERVATION_CONFLICT", step)
        self.assertGreaterEqual(len(error["conflicts"]), 1, step)
        conflict = error["conflicts"][0]
        self.assertEqual(conflict["reservation_id"], self.existing_id, step)
        self.assertEqual(conflict["start_time"], "10:00", step)
        self.assertEqual(conflict["end_time"], "11:00", step)

    def test_conflict_and_boundaries(self):
        # 手順1〜3: 重なりはすべて 409
        self._assert_conflict(self._post("10:00", "11:00"), "手順1(完全一致)")
        self._assert_conflict(self._post("10:30", "11:30"), "手順2(後方部分重複)")
        self._assert_conflict(self._post("09:30", "10:30"), "手順3(前方部分重複)")

        # 手順4・5: 境界が接するだけなら 201
        res4 = self._post("11:00", "12:00")
        self.assertEqual(res4.status_code, 201, f"手順4(境界接触・後): {res4.text}")
        touching_id = res4.json()["reservation"]["reservation_id"]
        res5 = self._post("09:00", "10:00")
        self.assertEqual(res5.status_code, 201, f"手順5(境界接触・前): {res5.text}")

        # 手順6: 会議室違いは 201
        self.assertEqual(self._post("10:00", "11:00", room_id=self.room_b).status_code, 201)

        # 手順7: 日付違いは 201
        self.assertEqual(
            self._post("10:00", "11:00", reserved_date=_date(2)).status_code, 201
        )

        # 手順8: 自分自身は競合として扱わない(時間帯は変えず件名だけ変更)
        res8 = self.client.put(
            f"/api/reservations/{touching_id}",
            json=self._body("11:00", "12:00", title="件名だけ変更"),
        )
        self.assertEqual(res8.status_code, 200, f"手順8(自己除外): {res8.text}")
        self.assertEqual(res8.json()["reservation"]["title"], "件名だけ変更")


if __name__ == "__main__":
    unittest.main()
