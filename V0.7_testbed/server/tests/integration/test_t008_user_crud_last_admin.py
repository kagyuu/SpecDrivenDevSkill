"""T008 — ユーザーCRUDと最後の管理者の保護(docs/P008-test-direction/T008-user-crud-last-admin.md)。"""

import unittest

from tests.integration.support import IntegrationTestCase

NEW_USER = {"user_id": "user900", "name": "新規 太郎", "role": "general", "password": "Passw0rd!23"}


class T008UserCrudLastAdminTest(IntegrationTestCase):
    def test_user_crud_and_last_admin_protection(self):
        self.assertEqual(self.login("admin001").status_code, 200)
        admin_cookies = dict(self.client.cookies)

        # 手順1: 登録
        res = self.client.post("/api/users", json=NEW_USER)
        self.assertEqual(res.status_code, 201)
        self.assertNotIn("password", res.json()["user"])
        stored = self.db().execute(
            "SELECT password_hash FROM users WHERE user_id = 'user900'"
        ).fetchone()["password_hash"]
        self.assertTrue(stored.startswith("scrypt$"))

        # 手順2: 同じIDをもう一度 → 409
        self._use(admin_cookies)
        res = self.client.post("/api/users", json=NEW_USER)
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "DUPLICATE_KEY")

        # 手順3: 登録したユーザーでログインできる
        self.assertEqual(self.login("user900").status_code, 200)

        # 手順4: password を省略した更新後も、元のパスワードでログインできる
        self._use(admin_cookies)
        res = self.client.put(
            "/api/users/user900", json={"name": "新規 次郎", "role": "general", "is_active": True}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user"]["name"], "新規 次郎")
        self.assertEqual(self.login("user900").status_code, 200)

        # 手順5: 最後の有効な管理者の降格 → 409
        self._use(admin_cookies)
        res = self.client.put(
            "/api/users/admin001", json={"name": "管理 太郎", "role": "general", "is_active": True}
        )
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "CONSTRAINT_VIOLATION")

        # 手順6: 自分自身の無効化 → 409
        res = self.client.delete("/api/users/admin001")
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "CONSTRAINT_VIOLATION")
        self.assertEqual(res.json()["error"]["message"], "自分自身を無効化することはできません。")

        # 手順7: user001 のセッションを作ってから無効化 → セッションが消えて 401
        self.assertEqual(self.login("user001").status_code, 200)
        user_cookies = dict(self.client.cookies)
        self._use(admin_cookies)
        self.assertEqual(self.client.delete("/api/users/user001").status_code, 204)
        self._use(user_cookies)
        self.assertEqual(self.client.get("/api/me").status_code, 401)

        # 手順8: もう一度の無効化も 204(冪等)
        self._use(admin_cookies)
        self.assertEqual(self.client.delete("/api/users/user001").status_code, 204)

    def _use(self, cookies):
        self.client.cookies.clear()
        for name, value in cookies.items():
            self.client.cookies.set(name, value)


if __name__ == "__main__":
    unittest.main()
