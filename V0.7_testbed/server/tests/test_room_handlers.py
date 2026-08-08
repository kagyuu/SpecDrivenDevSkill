"""U002-T2 単体テスト — 会議室API(API-04〜API-07。P002 5.5)。"""

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from meeting_room import db, main, security
from meeting_room.repositories import rooms_repo, users_repo

NOW = "2026-08-05T00:00:00Z"
ROOM = {"name": "会議室A", "capacity": 10, "equipment": "プロジェクタ", "description": "窓側の大会議室"}


class RoomApiTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        self.app = main.create_app(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)
        self._add_user("user001", "山田 太郎", "general")
        self._add_user("adminx001", "管理 太郎", "admin")
        self.client = TestClient(self.app, base_url="https://testserver")
        self.addCleanup(self.client.close)

    def _add_user(self, user_id, name, role, is_active=True):
        with db.transaction(self.conn):
            users_repo.insert(
                self.conn, user_id, name, security.hash_password("Passw0rd!23"), role,
                is_active, NOW,
            )

    def login(self, user_id):
        self.client.cookies.clear()
        res = self.client.post(
            "/api/auth/login", json={"user_id": user_id, "password": "Passw0rd!23"}
        )
        self.assertEqual(res.status_code, 200)


class RoomApiTest(RoomApiTestBase):
    # 正常系: 登録は 201、レスポンス形状が P002 5.3 の Room
    def test_create_room(self):
        self.login("adminx001")
        res = self.client.post("/api/rooms", json=ROOM)
        self.assertEqual(res.status_code, 201)
        room = res.json()["room"]
        self.assertIsInstance(room["room_id"], int)
        self.assertEqual(room["name"], "会議室A")
        self.assertIs(room["is_active"], True)
        self.assertTrue(room["created_at"])
        self.assertTrue(room["updated_at"])

    # 正常系: 更新は 200
    def test_update_room(self):
        self.login("adminx001")
        room_id = self.client.post("/api/rooms", json=ROOM).json()["room"]["room_id"]
        res = self.client.put(f"/api/rooms/{room_id}", json={**ROOM, "capacity": 12})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["room"]["capacity"], 12)

    # 正常系: 無効化は 204 で is_active=0、行は残る
    def test_deactivate_room(self):
        self.login("adminx001")
        room_id = self.client.post("/api/rooms", json=ROOM).json()["room"]["room_id"]
        res = self.client.delete(f"/api/rooms/{room_id}")
        self.assertEqual(res.status_code, 204)
        self.assertIs(rooms_repo.find_by_id(self.conn, room_id)["is_active"], False)
        # 冪等
        self.assertEqual(self.client.delete(f"/api/rooms/{room_id}").status_code, 204)

    # 正常系: 一般ユーザーは有効な会議室のみを room_id 昇順で取得できる
    def test_list_rooms_for_general_user(self):
        self.login("adminx001")
        first = self.client.post("/api/rooms", json=ROOM).json()["room"]["room_id"]
        self.client.post("/api/rooms", json={**ROOM, "name": "会議室B", "capacity": 4})
        self.client.delete(f"/api/rooms/{first}")
        self.login("user001")
        res = self.client.get("/api/rooms")
        self.assertEqual(res.status_code, 200)
        self.assertEqual([r["name"] for r in res.json()["rooms"]], ["会議室B"])

    # 正常系: 管理者の include_inactive=true は無効分も返す
    def test_list_rooms_include_inactive_for_admin(self):
        self.login("adminx001")
        room_id = self.client.post("/api/rooms", json=ROOM).json()["room"]["room_id"]
        self.client.delete(f"/api/rooms/{room_id}")
        res = self.client.get("/api/rooms?include_inactive=true")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["rooms"]), 1)

    # 異常系: 入力値の検証(P002 3.6)
    def test_validation_errors(self):
        self.login("adminx001")
        cases = [
            ({**ROOM, "name": ""}, "name"),
            ({**ROOM, "name": "あ" * 51}, "name"),
            ({**ROOM, "capacity": 0}, "capacity"),
            ({**ROOM, "capacity": 501}, "capacity"),
            ({**ROOM, "capacity": 1.5}, "capacity"),
            ({**ROOM, "description": "あ" * 201}, "description"),
            ({**ROOM, "equipment": "あ" * 201}, "equipment"),
        ]
        for body, field in cases:
            with self.subTest(field=field, value=body[field]):
                res = self.client.post("/api/rooms", json=body)
                self.assertEqual(res.status_code, 400)
                error = res.json()["error"]
                self.assertEqual(error["code"], "VALIDATION_ERROR")
                self.assertEqual(error["details"][0]["field"], field)

    # 異常系: 一般ユーザーの書き込みは 403
    def test_general_user_is_forbidden(self):
        self.login("adminx001")
        room_id = self.client.post("/api/rooms", json=ROOM).json()["room"]["room_id"]
        self.login("user001")
        for res in (
            self.client.post("/api/rooms", json={**ROOM, "name": "会議室Z"}),
            self.client.put(f"/api/rooms/{room_id}", json=ROOM),
            self.client.delete(f"/api/rooms/{room_id}"),
            self.client.get("/api/rooms?include_inactive=true"),
        ):
            self.assertEqual(res.status_code, 403)
            self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    # 異常系: 同名登録は 409 DUPLICATE_KEY
    def test_duplicate_name(self):
        self.login("adminx001")
        self.client.post("/api/rooms", json=ROOM)
        res = self.client.post("/api/rooms", json=ROOM)
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "DUPLICATE_KEY")
        self.assertEqual(res.json()["error"]["message"], "同じ名前の会議室がすでに登録されています。")

    # 異常系: 存在しない room_id は 404
    def test_missing_room_is_404(self):
        self.login("adminx001")
        self.assertEqual(self.client.put("/api/rooms/999", json=ROOM).status_code, 404)
        self.assertEqual(self.client.delete("/api/rooms/999").status_code, 404)

    # 異常系: 未認証は 401
    def test_unauthenticated(self):
        self.client.cookies.clear()
        for res in (
            self.client.get("/api/rooms"),
            self.client.post("/api/rooms", json=ROOM),
            self.client.put("/api/rooms/1", json=ROOM),
            self.client.delete("/api/rooms/1"),
        ):
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json()["error"]["code"], "UNAUTHENTICATED")


if __name__ == "__main__":
    unittest.main()
