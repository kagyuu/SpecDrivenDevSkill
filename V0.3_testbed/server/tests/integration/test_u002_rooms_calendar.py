import unittest

from tests._server_helper import RunningServer


class TestU002RoomsCalendar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = RunningServer()
        _, body, cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "admin", "password": "admin12345"}
        )
        cls.admin_cookie = cookie
        _, _, cookie2 = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "u001", "password": "password1"}
        )
        cls.general_cookie = cookie2

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_admin_can_create_room(self):
        status, body, _ = self.server.request(
            "POST",
            "/api/rooms",
            {"name": "会議室X", "capacity": 5, "equipment": "モニタ"},
            cookie=self.admin_cookie,
        )
        self.assertEqual(status, 201)
        self.assertEqual(body["name"], "会議室X")

    def test_general_user_cannot_create_room(self):
        status, _, _ = self.server.request(
            "POST",
            "/api/rooms",
            {"name": "会議室Y", "capacity": 5, "equipment": None},
            cookie=self.general_cookie,
        )
        self.assertEqual(status, 403)

    def test_rooms_list_reflects_created_room(self):
        status, body, _ = self.server.request("GET", "/api/rooms", cookie=self.general_cookie)
        self.assertEqual(status, 200)
        self.assertTrue(any(r["name"] == "会議室X" for r in body))

    def test_reservations_empty_before_any_created(self):
        status, body, _ = self.server.request(
            "GET", "/api/reservations?date_from=2000-01-01&date_to=2000-01-02", cookie=self.general_cookie
        )
        self.assertEqual(status, 200)
        self.assertEqual(body, [])


if __name__ == "__main__":
    unittest.main()
