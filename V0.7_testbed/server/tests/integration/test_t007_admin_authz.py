"""T007 — 管理者専用APIの認可(一般ユーザーは 403 FORBIDDEN)。"""

import unittest

from tests.integration.support import IntegrationTestCase

ROOM = {"name": "会議室Z", "capacity": 10}


class T007AdminAuthzTest(IntegrationTestCase):
    seed_rooms = True

    def test_general_user_is_forbidden_everywhere(self):
        room_id = self.db().execute("SELECT MIN(room_id) AS id FROM rooms").fetchone()["id"]
        before = self.db().execute("SELECT COUNT(*) AS c FROM rooms").fetchone()["c"]
        users_before = self.db().execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]

        self.assertEqual(self.login("user001").status_code, 200)
        responses = {
            "POST /api/rooms": self.client.post("/api/rooms", json=ROOM),
            "PUT /api/rooms/{id}": self.client.put(f"/api/rooms/{room_id}", json=ROOM),
            "DELETE /api/rooms/{id}": self.client.delete(f"/api/rooms/{room_id}"),
            "GET /api/rooms?include_inactive=true": self.client.get("/api/rooms?include_inactive=true"),
            "GET /api/users": self.client.get("/api/users"),
            "POST /api/users": self.client.post(
                "/api/users",
                json={"user_id": "user900", "name": "新規 太郎", "role": "general",
                      "password": "Passw0rd!23"},
            ),
            "PUT /api/users/user002": self.client.put(
                "/api/users/user002", json={"name": "x", "role": "general", "is_active": True}
            ),
            "DELETE /api/users/user002": self.client.delete("/api/users/user002"),
        }
        for label, res in responses.items():
            with self.subTest(endpoint=label):
                self.assertEqual(res.status_code, 403, label)
                self.assertEqual(res.json()["error"]["code"], "FORBIDDEN", label)

        # DBの状態が変化していない
        self.assertEqual(self.db().execute("SELECT COUNT(*) AS c FROM rooms").fetchone()["c"], before)
        self.assertEqual(
            self.db().execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"], users_before
        )
        self.assertEqual(
            self.db().execute(
                "SELECT is_active FROM rooms WHERE room_id = ?", (room_id,)
            ).fetchone()["is_active"],
            1,
        )

        # 手順7: 既定の会議室一覧は一般ユーザーでも 200
        res = self.client.get("/api/rooms")
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
