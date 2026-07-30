import unittest

from tests._server_helper import RunningServer


class TestT002CrossCuttingAuthorization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = RunningServer()
        _, _, cls.admin_cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "admin", "password": "admin12345"}
        )
        _, _, cls.u1_cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "u001", "password": "password1"}
        )
        _, rooms, _ = cls.server.request("GET", "/api/rooms", cookie=cls.admin_cookie)
        cls.room_id = rooms[0]["id"]
        # u002が予約を作成しておく(手順4で使う「他人の予約」)
        _, _, cls.u2_cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "u002", "password": "password2"}
        )
        _, cls.other_reservation, _ = cls.server.request(
            "POST",
            "/api/reservations",
            {
                "room_id": cls.room_id,
                "date": "2099-08-01",
                "start_time": "09:00",
                "end_time": "10:00",
                "subject": "u002予約",
                "notes": "",
                "participant_ids": [],
            },
            cookie=cls.u2_cookie,
        )

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_general_user_blocked_from_room_admin_apis(self):
        s = self.server
        status, _, _ = s.request(
            "POST", "/api/rooms", {"name": "拒否確認室", "capacity": 2}, cookie=self.u1_cookie
        )
        self.assertEqual(status, 403)
        status, _, _ = s.request(
            "PUT", f"/api/rooms/{self.room_id}", {"name": "x", "capacity": 2, "is_active": True}, cookie=self.u1_cookie
        )
        self.assertEqual(status, 403)
        status, _, _ = s.request("DELETE", f"/api/rooms/{self.room_id}", cookie=self.u1_cookie)
        self.assertEqual(status, 403)

    def test_general_user_blocked_from_user_admin_apis(self):
        s = self.server
        status, _, _ = s.request("GET", "/api/users", cookie=self.u1_cookie)
        self.assertEqual(status, 403)
        status, _, _ = s.request(
            "POST",
            "/api/users",
            {"employee_id": "hack", "name": "x", "role": "general", "password": "password0"},
            cookie=self.u1_cookie,
        )
        self.assertEqual(status, 403)
        status, _, _ = s.request(
            "PUT", "/api/users/1", {"name": "x", "role": "general", "is_active": True}, cookie=self.u1_cookie
        )
        self.assertEqual(status, 403)
        status, _, _ = s.request("DELETE", "/api/users/1", cookie=self.u1_cookie)
        self.assertEqual(status, 403)

    def test_general_user_cannot_edit_or_delete_others_reservation(self):
        s = self.server
        reservation_id = self.other_reservation["id"]
        status, _, _ = s.request(
            "PUT",
            f"/api/reservations/{reservation_id}",
            {
                "room_id": self.room_id,
                "date": "2099-08-01",
                "start_time": "09:00",
                "end_time": "10:00",
                "subject": "改ざん試行",
                "notes": "",
                "participant_ids": [],
            },
            cookie=self.u1_cookie,
        )
        self.assertEqual(status, 403)
        status, _, _ = s.request("DELETE", f"/api/reservations/{reservation_id}", cookie=self.u1_cookie)
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
