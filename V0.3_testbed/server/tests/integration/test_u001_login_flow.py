import unittest

from tests._server_helper import RunningServer


class TestU001LoginFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = RunningServer()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_login_me_logout_me_flow(self):
        status, body, cookie = self.server.request(
            "POST", "/api/auth/login", {"employee_id": "admin", "password": "admin12345"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["user"]["role"], "admin")
        self.assertIsNotNone(cookie)

        status, body, _ = self.server.request("GET", "/api/me", cookie=cookie)
        self.assertEqual(status, 200)
        self.assertEqual(body["role"], "admin")

        status, _, _ = self.server.request("POST", "/api/auth/logout", cookie=cookie)
        self.assertEqual(status, 204)

        status, body, _ = self.server.request("GET", "/api/me", cookie=cookie)
        self.assertEqual(status, 401)


if __name__ == "__main__":
    unittest.main()
