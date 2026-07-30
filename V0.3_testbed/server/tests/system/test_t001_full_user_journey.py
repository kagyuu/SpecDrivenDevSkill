import unittest

from tests._server_helper import RunningServer


class TestT001FullUserJourney(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = RunningServer()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_full_journey(self):
        s = self.server

        status, _, admin_cookie = s.request(
            "POST", "/api/auth/login", {"employee_id": "admin", "password": "admin12345"}
        )
        self.assertEqual(status, 200, "手順1: adminログイン失敗")

        status, room, _ = s.request(
            "POST", "/api/rooms", {"name": "T001会議室", "capacity": 6, "equipment": None}, cookie=admin_cookie
        )
        self.assertEqual(status, 201, "手順1: 会議室登録失敗")

        status, _, u_cookie = s.request(
            "POST", "/api/auth/login", {"employee_id": "u001", "password": "password1"}
        )
        self.assertEqual(status, 200, "手順2: 一般ユーザーログイン失敗")

        status, rooms, _ = s.request("GET", "/api/rooms", cookie=u_cookie)
        self.assertEqual(status, 200)
        self.assertTrue(any(r["name"] == "T001会議室" for r in rooms), "手順2: 新規会議室が見えない")

        status, created, _ = s.request(
            "POST",
            "/api/reservations",
            {
                "room_id": room["id"],
                "date": "2099-07-01",
                "start_time": "13:00",
                "end_time": "14:00",
                "subject": "T001予約",
                "notes": "",
                "participant_ids": [],
            },
            cookie=u_cookie,
        )
        self.assertEqual(status, 201, "手順3: 予約作成失敗")
        reservation_id = created["id"]

        status, calendar, _ = s.request(
            "GET", "/api/reservations?date_from=2099-07-01&date_to=2099-07-01", cookie=u_cookie
        )
        self.assertEqual(status, 200)
        self.assertTrue(any(r["id"] == reservation_id for r in calendar), "手順4: カレンダーに反映されない")

        status, mine, _ = s.request("GET", "/api/reservations/mine?period=future", cookie=u_cookie)
        self.assertEqual(status, 200)
        self.assertTrue(any(r["id"] == reservation_id for r in mine), "手順5: マイ予約に反映されない")

        status, updated, _ = s.request(
            "PUT",
            f"/api/reservations/{reservation_id}",
            {
                "room_id": room["id"],
                "date": "2099-07-01",
                "start_time": "13:00",
                "end_time": "14:00",
                "subject": "T001予約(更新済み)",
                "notes": "",
                "participant_ids": [],
            },
            cookie=u_cookie,
        )
        self.assertEqual(status, 200, "手順6: 予約更新失敗")
        self.assertEqual(updated["subject"], "T001予約(更新済み)")

        status, _, _ = s.request("DELETE", f"/api/reservations/{reservation_id}", cookie=u_cookie)
        self.assertEqual(status, 204, "手順7: 予約取消失敗")

        status, _, _ = s.request("GET", f"/api/reservations/{reservation_id}", cookie=u_cookie)
        self.assertEqual(status, 404, "手順8: 取消後も404にならない")


if __name__ == "__main__":
    unittest.main()
