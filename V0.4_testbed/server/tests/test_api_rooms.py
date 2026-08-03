import os
import tempfile
import unittest

from starlette.testclient import TestClient

from app.db.connection import init_db
from app.main import create_app
from tests.helpers import make_test_conn, seed_user  # noqa: F401 (make_test_conn unused, kept for parity)


def _make_client(db_path: str) -> TestClient:
    app = create_app(db_path=db_path)
    return TestClient(app, base_url="https://testserver")


class RoomsApiTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)
        init_db(self.db_path)
        self.client = _make_client(self.db_path)

        # 管理者・一般ユーザーをAPI経由ではなく直接シード(U001のパスワードハッシュを再利用)
        from app.db.connection import get_connection
        conn = get_connection(self.db_path)
        seed_user(conn, "A0001", "Passw0rd1", name="管理者", role="admin")
        seed_user(conn, "E0001", "Passw0rd1", name="山田太郎", role="general")
        conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _login(self, employee_id, password="Passw0rd1"):
        r = self.client.post("/api/auth/login", json={"employee_id": employee_id, "password": password})
        self.assertEqual(r.status_code, 200, r.text)

    def test_create_and_list(self):
        self._login("A0001")
        r = self.client.post("/api/rooms", json={
            "name": "会議室A", "capacity": 6, "equipment": ["プロジェクタ"], "is_active": True,
        })
        self.assertEqual(r.status_code, 201, r.text)
        r2 = self.client.get("/api/rooms")
        self.assertEqual(r2.status_code, 200)
        names = [room["name"] for room in r2.json()["rooms"]]
        self.assertIn("会議室A", names)

    def test_duplicate_name_rejected(self):
        self._login("A0001")
        self.client.post("/api/rooms", json={"name": "会議室A", "capacity": 6, "equipment": [], "is_active": True})
        r = self.client.post("/api/rooms", json={"name": "会議室A", "capacity": 4, "equipment": [], "is_active": True})
        self.assertEqual(r.status_code, 400)
        body = r.json()
        self.assertEqual(body["error"]["code"], "VALIDATION_ERROR")
        fields = [d["field"] for d in body["error"].get("details", [])]
        self.assertIn("name", fields)

    def test_forbidden_for_general_user(self):
        self._login("A0001")
        r0 = self.client.post("/api/rooms", json={"name": "会議室A", "capacity": 6, "equipment": [], "is_active": True})
        self.assertEqual(r0.status_code, 201)
        self.client.post("/api/auth/logout")

        self._login("E0001")
        r1 = self.client.post("/api/rooms", json={"name": "会議室B", "capacity": 4, "equipment": [], "is_active": True})
        r2 = self.client.put("/api/rooms/1", json={"name": "会議室C", "capacity": 4, "equipment": [], "is_active": True})
        r3 = self.client.delete("/api/rooms/1")
        self.assertEqual(r1.status_code, 403)
        self.assertEqual(r2.status_code, 403)
        self.assertEqual(r3.status_code, 403)


if __name__ == "__main__":
    unittest.main()
