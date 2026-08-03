import os
import tempfile
import unittest

from starlette.testclient import TestClient

from app.db.connection import get_connection, init_db
from app.main import create_app
from tests.helpers import seed_user


def _make_client(db_path: str) -> TestClient:
    app = create_app(db_path=db_path)
    return TestClient(app, base_url="https://testserver")


class UsersApiTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)
        init_db(self.db_path)
        self.client = _make_client(self.db_path)

        conn = get_connection(self.db_path)
        self.admin_id = seed_user(conn, "A0001", "Passw0rd1", name="管理者", role="admin")
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _login_admin(self):
        r = self.client.post("/api/auth/login", json={"employee_id": "A0001", "password": "Passw0rd1"})
        self.assertEqual(r.status_code, 200, r.text)

    def test_create_then_login(self):
        self._login_admin()
        r = self.client.post("/api/users", json={
            "employee_id": "E0002", "name": "鈴木花子", "role": "general",
            "is_active": True, "initial_password": "Passw0rd2",
        })
        self.assertEqual(r.status_code, 201, r.text)
        self.assertNotIn("initial_password", r.json())

        other_client = _make_client(self.db_path)
        r2 = other_client.post("/api/auth/login", json={"employee_id": "E0002", "password": "Passw0rd2"})
        self.assertEqual(r2.status_code, 200, r2.text)

    def test_duplicate_employee_id_rejected(self):
        self._login_admin()
        data = {"employee_id": "E0002", "name": "鈴木花子", "role": "general",
                "is_active": True, "initial_password": "Passw0rd2"}
        self.client.post("/api/users", json=data)
        r = self.client.post("/api/users", json={**data, "name": "重複太郎", "initial_password": "Passw0rd3"})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "VALIDATION_ERROR")

    def test_self_deactivation_blocked(self):
        self._login_admin()
        r = self.client.delete(f"/api/users/{self.admin_id}")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["error"]["code"], "VALIDATION_ERROR")

        conn = get_connection(self.db_path)
        row = conn.execute("SELECT is_active FROM USERS WHERE id = ?", (self.admin_id,)).fetchone()
        conn.close()
        self.assertTrue(bool(row["is_active"]))


if __name__ == "__main__":
    unittest.main()
