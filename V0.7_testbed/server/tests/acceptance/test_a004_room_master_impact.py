"""A004 — 会議室マスタ変更の予約への波及(API側)。

docs/P009-acceptance-direction/A004-room-master-impact.md
画面側(手順6・8・9)は `client/tests/acceptance/test_a004_room_master_impact_ui.js` が確認する。

手順4は【合否判定基準】により**合否に含めず実際の挙動を記録する**(仕様の確認事項)。
"""

from __future__ import annotations

import unittest

from tests.acceptance.base import AcceptanceTestCase, day


class A004RoomMasterImpactTest(AcceptanceTestCase):
    def setUp(self):
        super().setUp()
        self.room_a = self.room_ids()["会議室A"]
        self.date = day(1)
        # 事前準備2: user001 で会議室Aに予約(参加予定人数 8)
        self.user = self.new_client()
        self.assertEqual(self.user.login("user001").status, 200)
        res = self.user.post(
            "/api/reservations",
            self.reservation_body(self.room_a, self.date, "10:00", "11:00", attendee_count=8),
        )
        self.assertEqual(res.status, 201, res.text)
        self.reservation_id = res.json()["reservation"]["reservation_id"]
        # 事前準備3: admin001 でログイン
        self.admin = self.new_client()
        self.assertEqual(self.admin.login("admin001").status, 200)
        self.step4_observed = None

    def tearDown(self):
        if self.step4_observed is not None:
            print(f"[A004 手順4 実測(合否対象外)] {self.step4_observed}")
        super().tearDown()

    def test_room_master_impact(self):
        # 手順1: 今後の予約が1件ある会議室Aの無効化 → 409 CONSTRAINT_VIOLATION
        res = self.admin.delete(f"/api/rooms/{self.room_a}")
        self.assertEqual(res.status, 409, res.text)
        self.assertEqual(res.error_code(), "CONSTRAINT_VIOLATION")

        # 手順2: 収容人数 10 → 5 に変更 → 200
        res = self.admin.put(
            f"/api/rooms/{self.room_a}",
            {"name": "会議室A", "capacity": 5, "equipment": "プロジェクタ", "description": ""},
        )
        self.assertEqual(res.status, 200, res.text)
        self.assertEqual(res.json()["room"]["capacity"], 5)

        # 手順3: 既存予約は壊れず、参加予定人数 8 のまま取得できる
        res = self.user.get(f"/api/reservations/{self.reservation_id}")
        self.assertEqual(res.status, 200, res.text)
        self.assertEqual(res.json()["reservation"]["attendee_count"], 8)

        # 手順4: 件名だけ変更して PUT(合否対象外。実際の挙動を記録する)
        res = self.user.put(
            f"/api/reservations/{self.reservation_id}",
            self.reservation_body(
                self.room_a, self.date, "10:00", "11:00", title="件名変更", attendee_count=8
            ),
        )
        self.step4_observed = f"status={res.status} code={res.error_code()} body={res.text[:200]}"

        # 手順5: 新規予約(参加予定人数 6 > 収容人数 5) → 400 CAPACITY_EXCEEDED
        res = self.user.post(
            "/api/reservations",
            self.reservation_body(self.room_a, self.date, "14:00", "15:00", attendee_count=6),
        )
        self.assertEqual(res.status, 400, res.text)
        self.assertEqual(res.error_code(), "CAPACITY_EXCEEDED")

        # 手順7: 予約を取り消してから会議室Aを無効化 → 204
        self.assertEqual(self.user.delete(f"/api/reservations/{self.reservation_id}").status, 204)
        res = self.admin.delete(f"/api/rooms/{self.room_a}")
        self.assertEqual(res.status, 204, res.text)

        # 手順8・9の前提: 一般ユーザーの GET /api/rooms に会議室Aが現れない
        rooms = self.user.get("/api/rooms").json()["rooms"]
        self.assertNotIn("会議室A", [r["name"] for r in rooms])


if __name__ == "__main__":
    unittest.main()
