import os
import tempfile
import unittest

from starlette.testclient import TestClient

from app.core.password import hash_password
from app.db.connection import get_connection, init_db
from app.main import create_app


def _make_client(db_path: str) -> TestClient:
    app = create_app(db_path=db_path)
    return TestClient(app, base_url="https://testserver")


class AuthApiTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)
        init_db(self.db_path)
        conn = get_connection(self.db_path)
        now = "2026-01-01T00:00:00Z"
        conn.execute(
            "INSERT INTO USERS (employee_id, name, password_hash, role, is_active, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 1, ?, ?)",
            ("E0001", "山田太郎", hash_password("Passw0rd1"), "general", now, now),
        )
        conn.execute(
            "INSERT INTO USERS (employee_id, name, password_hash, role, is_active, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 0, ?, ?)",
            ("E0099", "無効ユーザー", hash_password("Passw0rd1"), "general", now, now),
        )
        conn.commit()
        conn.close()
        self.client = _make_client(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_login_success_then_me(self):
        r = self.client.post("/api/auth/login", json={"employee_id": "E0001", "password": "Passw0rd1"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["user"]["employee_id"], "E0001")
        self.assertIn("session_id", r.cookies)

        r2 = self.client.get("/api/me")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["user"]["employee_id"], "E0001")

    def test_login_invalid_credentials(self):
        r = self.client.post("/api/auth/login", json={"employee_id": "E0001", "password": "WrongPassword"})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"]["code"], "AUTH_INVALID_CREDENTIALS")

        r2 = self.client.post("/api/auth/login", json={"employee_id": "NOT_EXIST", "password": "Passw0rd1"})
        self.assertEqual(r2.status_code, 401)
        self.assertEqual(r2.json()["error"]["code"], "AUTH_INVALID_CREDENTIALS")

    def test_login_inactive_user(self):
        r = self.client.post("/api/auth/login", json={"employee_id": "E0099", "password": "Passw0rd1"})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"]["code"], "AUTH_INVALID_CREDENTIALS")

    def test_login_missing_fields_returns_400(self):
        r = self.client.post("/api/auth/login", json={"employee_id": "E0001"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "VALIDATION_ERROR")

    def test_me_without_cookie_returns_401(self):
        r = self.client.get("/api/me")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"]["code"], "AUTH_REQUIRED")

    def test_logout_invalidates_session(self):
        self.client.post("/api/auth/login", json={"employee_id": "E0001", "password": "Passw0rd1"})
        r = self.client.post("/api/auth/logout")
        self.assertEqual(r.status_code, 200)
        r2 = self.client.get("/api/me")
        self.assertEqual(r2.status_code, 401)

    def test_logout_without_login_returns_200(self):
        r = self.client.post("/api/auth/logout")
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
