import unittest

from tests._server_helper import RunningServer


class TestU004UsersAndAuthz(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = RunningServer()
        _, _, cls.admin_cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "admin", "password": "admin12345"}
        )
        _, _, cls.general_cookie = cls.server.request(
            "POST", "/api/auth/login", {"employee_id": "u001", "password": "password1"}
        )

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_admin_can_create_user(self):
        status, body, _ = self.server.request(
            "POST",
            "/api/users",
            {"employee_id": "u099", "name": "新規太郎", "role": "general", "password": "password9"},
            cookie=self.admin_cookie,
        )
        self.assertEqual(status, 201)
        self.assertNotIn("password_hash", body)

    def test_general_user_cannot_list_users(self):
        status, _, _ = self.server.request("GET", "/api/users", cookie=self.general_cookie)
        self.assertEqual(status, 403)

    def test_general_user_cannot_create_room(self):
        status, _, _ = self.server.request(
            "POST", "/api/rooms", {"name": "権限確認室", "capacity": 2}, cookie=self.general_cookie
        )
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
