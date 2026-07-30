import unittest

from tests._server_helper import RunningServer


class TestU003ReservationFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = RunningServer()
        _, _, cls.admin_cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "admin", "password": "admin12345"}
        )
        status, body, _ = cls.server.request(
            "GET", "/api/rooms", cookie=cls.admin_cookie
        )
        cls.room_id = body[0]["id"]

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_create_conflict_update_cancel_flow(self):
        status, created, _ = self.server.request(
            "POST",
            "/api/reservations",
            {
                "room_id": self.room_id,
                "date": "2099-05-01",
                "start_time": "10:00",
                "end_time": "11:00",
                "subject": "結合確認MTG",
                "notes": "",
                "participant_ids": [],
            },
            cookie=self.admin_cookie,
        )
        self.assertEqual(status, 201)
        reservation_id = created["id"]

        status, body, _ = self.server.request(
            "POST",
            "/api/reservations",
            {
                "room_id": self.room_id,
                "date": "2099-05-01",
                "start_time": "10:30",
                "end_time": "11:30",
                "subject": "重複MTG",
                "notes": "",
                "participant_ids": [],
            },
            cookie=self.admin_cookie,
        )
        self.assertEqual(status, 409)
        self.assertEqual(body["error"]["code"], "CONFLICT")

        status, updated, _ = self.server.request(
            "PUT",
            f"/api/reservations/{reservation_id}",
            {
                "room_id": self.room_id,
                "date": "2099-05-01",
                "start_time": "10:15",
                "end_time": "11:15",
                "subject": "結合確認MTG更新",
                "notes": "",
                "participant_ids": [],
            },
            cookie=self.admin_cookie,
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["subject"], "結合確認MTG更新")

        status, _, _ = self.server.request(
            "DELETE", f"/api/reservations/{reservation_id}", cookie=self.admin_cookie
        )
        self.assertEqual(status, 204)

        status, body, _ = self.server.request(
            "GET", f"/api/reservations/{reservation_id}", cookie=self.admin_cookie
        )
        self.assertEqual(status, 404)

    def test_nonexistent_participant_returns_400_not_500(self):
        # F001相当のケース: これは最初から400になる(V0.2のバグを再現しない)。
        status, body, _ = self.server.request(
            "POST",
            "/api/reservations",
            {
                "room_id": self.room_id,
                "date": "2099-06-01",
                "start_time": "09:00",
                "end_time": "10:00",
                "subject": "参加者不正MTG",
                "notes": "",
                "participant_ids": [999999],
            },
            cookie=self.admin_cookie,
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")


if __name__ == "__main__":
    unittest.main()
