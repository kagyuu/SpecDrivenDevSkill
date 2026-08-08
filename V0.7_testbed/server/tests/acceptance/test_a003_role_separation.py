"""A003 — 権限分離の横断確認(API側。docs/P009-acceptance-direction/A003-role-separation.md)。

画面側(手順1・2)は `client/tests/acceptance/test_a003_role_separation_ui.js` が確認する。
"""

from __future__ import annotations

import unittest

from tests.acceptance.base import AcceptanceTestCase, day


class A003RoleSeparationTest(AcceptanceTestCase):
    def setUp(self):
        super().setUp()
        rooms = self.room_ids()
        self.room_a = rooms["会議室A"]
        self.room_b = rooms["会議室B"]
        # 事前準備1: user002 の予約1件
        other = self.new_client()
        self.assertEqual(other.login("user002").status, 200)
        res = other.post(
            "/api/reservations", self.reservation_body(self.room_a, day(1), "09:00", "10:00")
        )
        self.assertEqual(res.status, 201, res.text)
        self.other_reservation_id = res.json()["reservation"]["reservation_id"]
        # 事前準備2: user001 でログイン
        self.assertEqual(self.login("user001").status, 200)

    def _admin_only_calls(self, room_id=None, room_name="会議室A"):
        """管理者専用API 8本(A003 手順3の列挙どおり)。

        `room_id` は認可の確認対象であり、業務制約(今後の予約が残る会議室は無効化できない)
        に引っかからない会議室を手順7では指定する(認可以外の理由で失敗させないため)。
        """
        room_id = self.room_a if room_id is None else room_id
        return [
            ("POST /api/rooms", lambda c: c.post("/api/rooms", {"name": "会議室X", "capacity": 5})),
            (
                "PUT /api/rooms/{id}",
                lambda c: c.put(f"/api/rooms/{room_id}", {"name": room_name, "capacity": 10}),
            ),
            ("DELETE /api/rooms/{id}", lambda c: c.delete(f"/api/rooms/{room_id}")),
            ("GET /api/users?scope=management", lambda c: c.get("/api/users?scope=management")),
            (
                "POST /api/users",
                lambda c: c.post(
                    "/api/users",
                    {
                        "user_id": "newuser1",
                        "name": "新規 一郎",
                        "role": "general",
                        "password": "Passw0rd!23",
                    },
                ),
            ),
            (
                "PUT /api/users/{id}",
                lambda c: c.put(
                    "/api/users/user002", {"name": "鈴木 花子", "role": "general", "is_active": True}
                ),
            ),
            ("DELETE /api/users/{id}", lambda c: c.delete("/api/users/user002")),
            (
                "GET /api/rooms?include_inactive=true",
                lambda c: c.get("/api/rooms?include_inactive=true"),
            ),
        ]

    def test_role_separation(self):
        # 手順3: 一般ユーザーのCookieで管理者専用API 8本 → すべて 403 FORBIDDEN
        for label, call in self._admin_only_calls():
            with self.subTest(api=label):
                res = call(self.client)
                self.assertEqual(res.status, 403, f"{label}: {res.status} {res.text}")
                self.assertEqual(res.error_code(), "FORBIDDEN", label)

        # 手順4: 他人の予約への PUT / DELETE → 403 FORBIDDEN
        res = self.client.put(
            f"/api/reservations/{self.other_reservation_id}",
            self.reservation_body(self.room_a, day(1), "09:00", "10:00", title="乗っ取り"),
        )
        self.assertEqual(res.status, 403, res.text)
        self.assertEqual(res.error_code(), "FORBIDDEN")
        res = self.client.delete(f"/api/reservations/{self.other_reservation_id}")
        self.assertEqual(res.status, 403, res.text)
        self.assertEqual(res.error_code(), "FORBIDDEN")

        # 手順5: 他人の予約の GET → 200(閲覧は許可)
        res = self.client.get(f"/api/reservations/{self.other_reservation_id}")
        self.assertEqual(res.status, 200, res.text)

        # 手順6: Cookieなし → すべて 401 UNAUTHENTICATED
        anon = self.new_client()
        for label, call in self._admin_only_calls():
            with self.subTest(api=f"anon {label}"):
                res = call(anon)
                self.assertEqual(res.status, 401, f"{label}: {res.status} {res.text}")
                self.assertEqual(res.error_code(), "UNAUTHENTICATED", label)
        res = anon.get(f"/api/reservations?date_from={day(0)}&date_to={day(6)}")
        self.assertEqual(res.status, 401, res.text)
        self.assertEqual(res.error_code(), "UNAUTHENTICATED")

        # 手順7: admin001 で同じ8本 → すべて成功(200 / 201 / 204)
        admin = self.new_client()
        self.assertEqual(admin.login("admin001").status, 200)
        for label, call in self._admin_only_calls(self.room_b, "会議室B"):
            with self.subTest(api=f"admin {label}"):
                res = call(admin)
                self.assertIn(res.status, (200, 201, 204), f"{label}: {res.status} {res.text}")


if __name__ == "__main__":
    unittest.main()
