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

    # --- CR-002: 会議室説明文(description)。docs/P008-test-direction/T021〜T023参照 ---

    def test_create_room_with_description_then_list(self):
        """T021: docs/P008-test-direction/T021-room-description-create-and-list.md"""
        self._login("A0001")
        r = self.client.post("/api/rooms", json={
            "name": "会議室D", "capacity": 8, "equipment": [], "is_active": True,
            "description": "役員会議専用の個室です。",
        })
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["description"], "役員会議専用の個室です。")
        r2 = self.client.get("/api/rooms")
        self.assertEqual(r2.status_code, 200)
        room = next(x for x in r2.json()["rooms"] if x["name"] == "会議室D")
        self.assertEqual(room["description"], "役員会議専用の個室です。")

    def test_update_room_description_then_fetch(self):
        """T022: docs/P008-test-direction/T022-room-description-update-and-fetch.md"""
        self._login("A0001")
        r0 = self.client.post("/api/rooms", json={
            "name": "会議室E", "capacity": 4, "equipment": [], "is_active": True, "description": "",
        })
        self.assertEqual(r0.status_code, 201, r0.text)
        room_id = r0.json()["id"]
        r1 = self.client.put(f"/api/rooms/{room_id}", json={
            "name": "会議室E", "capacity": 4, "equipment": [], "is_active": True,
            "description": "予約前に清掃予約が必要です。",
        })
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r1.json()["description"], "予約前に清掃予約が必要です。")
        r2 = self.client.get("/api/rooms")
        room = next(x for x in r2.json()["rooms"] if x["id"] == room_id)
        self.assertEqual(room["description"], "予約前に清掃予約が必要です。")

    def test_update_room_preserves_description_when_capacity_changes(self):
        """T023: docs/P008-test-direction/T023-room-description-preserved-on-unrelated-update.md"""
        self._login("A0001")
        r0 = self.client.post("/api/rooms", json={
            "name": "会議室F", "capacity": 4, "equipment": [], "is_active": True,
            "description": "窓なし・防音仕様。",
        })
        self.assertEqual(r0.status_code, 201, r0.text)
        room_id = r0.json()["id"]
        r1 = self.client.put(f"/api/rooms/{room_id}", json={
            "name": "会議室F", "capacity": 10, "equipment": [], "is_active": True,
            "description": "窓なし・防音仕様。",
        })
        self.assertEqual(r1.status_code, 200, r1.text)
        self.assertEqual(r1.json()["capacity"], 10)
        self.assertEqual(r1.json()["description"], "窓なし・防音仕様。")
        r2 = self.client.get("/api/rooms")
        room = next(x for x in r2.json()["rooms"] if x["id"] == room_id)
        self.assertEqual(room["description"], "窓なし・防音仕様。")

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
