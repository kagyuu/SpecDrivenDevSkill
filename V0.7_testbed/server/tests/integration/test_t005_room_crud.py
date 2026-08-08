"""T005 — 会議室CRUDの一気通貫(docs/P008-test-direction/T005-room-crud.md)。"""

import unittest

from tests.integration.support import IntegrationTestCase

ROOM = {"name": "会議室A", "capacity": 10, "equipment": "プロジェクタ", "description": "窓側の大会議室"}


class T005RoomCrudTest(IntegrationTestCase):
    def test_room_crud(self):
        self.assertEqual(self.login("admin001").status_code, 200)

        # 手順1: 登録
        res = self.client.post("/api/rooms", json=ROOM)
        self.assertEqual(res.status_code, 201)
        room = res.json()["room"]
        room_id = room["room_id"]
        self.assertIsInstance(room_id, int)
        self.assertEqual(room["description"], "窓側の大会議室")

        # 手順2: 一覧に1件
        res = self.client.get("/api/rooms")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["rooms"]), 1)

        # 手順3: 更新(収容人数 10→12、説明文の変更)
        res = self.client.put(
            f"/api/rooms/{room_id}", json={**ROOM, "capacity": 12, "description": "改装後"}
        )
        self.assertEqual(res.status_code, 200)
        updated = res.json()["room"]
        self.assertEqual(updated["capacity"], 12)
        self.assertGreaterEqual(updated["updated_at"], updated["created_at"])

        # 手順4: 一覧に反映
        listed = self.client.get("/api/rooms").json()["rooms"][0]
        self.assertEqual((listed["capacity"], listed["description"]), (12, "改装後"))

        # 手順5: 無効化(論理削除。行は残る)
        self.assertEqual(self.client.delete(f"/api/rooms/{room_id}").status_code, 204)
        row = self.db().execute(
            "SELECT is_active FROM rooms WHERE room_id = ?", (room_id,)
        ).fetchone()
        self.assertIsNotNone(row, "行が物理削除されていないこと")
        self.assertEqual(row["is_active"], 0)

        # 手順6: 既定の一覧には出ず、include_inactive=true には出る
        self.assertEqual(self.client.get("/api/rooms").json()["rooms"], [])
        self.assertEqual(len(self.client.get("/api/rooms?include_inactive=true").json()["rooms"]), 1)

        # 手順7: もう一度の無効化も 204(冪等)
        self.assertEqual(self.client.delete(f"/api/rooms/{room_id}").status_code, 204)


if __name__ == "__main__":
    unittest.main()
