"""T006 — 会議室名の一意性と無効化後の再登録(部分ユニークインデックス)。"""

import unittest

from tests.integration.support import IntegrationTestCase

ROOM_A = {"name": "会議室A", "capacity": 10}
ROOM_B = {"name": "会議室B", "capacity": 4}


class T006RoomNameUniquenessTest(IntegrationTestCase):
    def test_name_unique_only_among_active_rooms(self):
        self.assertEqual(self.login("admin001").status_code, 200)

        # 手順1: 会議室A を登録
        first = self.client.post("/api/rooms", json=ROOM_A)
        self.assertEqual(first.status_code, 201)
        first_id = first.json()["room"]["room_id"]

        # 手順2: 同名をもう一度 → 409 DUPLICATE_KEY
        res = self.client.post("/api/rooms", json=ROOM_A)
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "DUPLICATE_KEY")
        self.assertEqual(res.json()["error"]["message"], "同じ名前の会議室がすでに登録されています。")

        # 手順3: 会議室B を登録し、名前を 会議室A に変更 → 409
        second_id = self.client.post("/api/rooms", json=ROOM_B).json()["room"]["room_id"]
        res = self.client.put(f"/api/rooms/{second_id}", json=ROOM_A)
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "DUPLICATE_KEY")

        # 手順4: 会議室A を無効化
        self.assertEqual(self.client.delete(f"/api/rooms/{first_id}").status_code, 204)

        # 手順5: 同名を再登録 → 201
        res = self.client.post("/api/rooms", json=ROOM_A)
        self.assertEqual(res.status_code, 201, "無効化済みの同名があっても登録できること")
        third_id = res.json()["room"]["room_id"]
        self.assertNotEqual(third_id, first_id)

        # 手順6: include_inactive=true で 会議室A が2件(1件は無効)
        rooms = self.client.get("/api/rooms?include_inactive=true").json()["rooms"]
        room_a = [r for r in rooms if r["name"] == "会議室A"]
        self.assertEqual(len(room_a), 2)
        self.assertEqual(sorted(r["is_active"] for r in room_a), [False, True])


if __name__ == "__main__":
    unittest.main()
