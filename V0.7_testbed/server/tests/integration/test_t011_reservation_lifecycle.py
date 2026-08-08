"""T011 — 予約の登録→一覧→詳細→更新→取消(docs/P008-test-direction/T011-reservation-lifecycle.md)。"""

import unittest
from datetime import datetime, timedelta

from tests.integration.support import IntegrationTestCase


def _date(offset_days: int) -> str:
    return (datetime.now() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


class T011ReservationLifecycleTest(IntegrationTestCase):
    seed_rooms = True

    def test_reservation_lifecycle(self):
        # 事前準備: user001 でログイン
        self.assertEqual(self.login("user001").status_code, 200)
        room_a = self.client.get("/api/rooms").json()["rooms"][0]
        self.assertEqual(room_a["name"], "会議室A")
        reserved_date = _date(1)
        body = {
            "room_id": room_a["room_id"],
            "reserved_date": reserved_date,
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例会議",
            "attendee_user_ids": ["user002"],
            "attendee_count": 8,
            "note": "",
        }

        # 手順1: 登録 → 201。予約者はセッションのユーザー
        res = self.client.post("/api/reservations", json=body)
        self.assertEqual(res.status_code, 201, res.text)
        reservation = res.json()["reservation"]
        reservation_id = reservation["reservation_id"]
        self.assertEqual(reservation["user_id"], "user001")

        # 手順2: 期間一覧 → 該当予約が1件、room_name / user_name が入り attendees は空配列
        res = self.client.get(
            f"/api/reservations?date_from={_date(0)}&date_to={_date(6)}"
        )
        self.assertEqual(res.status_code, 200)
        listed = [r for r in res.json()["reservations"] if r["reservation_id"] == reservation_id]
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["room_name"], "会議室A")
        self.assertEqual(listed[0]["user_name"], "山田 太郎")
        self.assertEqual(listed[0]["attendees"], [])

        # 手順3: 詳細 → attendees に user002 が1件
        res = self.client.get(f"/api/reservations/{reservation_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json()["reservation"]["attendees"],
            [{"user_id": "user002", "name": "鈴木 花子"}],
        )

        # 手順4: マイ予約 → 1件
        res = self.client.get("/api/reservations/mine?period=upcoming")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["reservations"]), 1)

        # 手順5: 更新(件名変更 + 参加者を空に) → 200
        res = self.client.put(
            f"/api/reservations/{reservation_id}",
            json={**body, "title": "臨時会議", "attendee_user_ids": []},
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["reservation"]["title"], "臨時会議")

        # 手順6: 反映確認 → attendees は空配列
        res = self.client.get(f"/api/reservations/{reservation_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["reservation"]["title"], "臨時会議")
        self.assertEqual(res.json()["reservation"]["attendees"], [])

        # 手順7: 取消 → 204、その後 404
        self.assertEqual(
            self.client.delete(f"/api/reservations/{reservation_id}").status_code, 204
        )
        self.assertEqual(
            self.client.get(f"/api/reservations/{reservation_id}").status_code, 404
        )

        # 手順8: reservation_attendees が0件
        row = self.db().execute(
            "SELECT COUNT(*) AS c FROM reservation_attendees"
        ).fetchone()
        self.assertEqual(row["c"], 0)


if __name__ == "__main__":
    unittest.main()
