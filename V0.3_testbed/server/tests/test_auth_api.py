import unittest

from starlette.testclient import TestClient

from app.main import create_app


class TestAuthApi(unittest.TestCase):
    def setUp(self):
        self.app = create_app(":memory:")
        self.client = TestClient(self.app)

    def test_login_success_sets_cookie(self):
        res = self.client.post("/api/auth/login", json={"employee_id": "admin", "password": "admin12345"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("session_id", res.cookies)
        self.assertEqual(res.json()["user"]["role"], "admin")

    def test_login_wrong_password_401(self):
        res = self.client.post("/api/auth/login", json={"employee_id": "admin", "password": "wrong"})
        self.assertEqual(res.status_code, 401)

    def test_login_inactive_user_401(self):
        # u001 を管理者権限で無効化してからログインを試みる
        login = self.client.post("/api/auth/login", json={"employee_id": "admin", "password": "admin12345"})
        users = self.client.get("/api/users").json()
        u001 = next(u for u in users if u["employee_id"] == "u001")
        self.client.put(f"/api/users/{u001['id']}", json={"name": u001["name"], "role": "general", "is_active": False})
        res = self.client.post("/api/auth/login", json={"employee_id": "u001", "password": "password1"})
        self.assertEqual(res.status_code, 401)

    def test_logout_then_me_401(self):
        self.client.post("/api/auth/login", json={"employee_id": "admin", "password": "admin12345"})
        res = self.client.post("/api/auth/logout")
        self.assertEqual(res.status_code, 204)
        res2 = self.client.get("/api/me")
        self.assertEqual(res2.status_code, 401)

    def test_me_without_login_401(self):
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
