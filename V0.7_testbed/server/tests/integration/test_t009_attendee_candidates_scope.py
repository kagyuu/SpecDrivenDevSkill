"""T009 — 参加者候補スコープの権限と射影(docs/P008-test-direction/T009-attendee-candidates-scope.md)。"""

import unittest

from tests.integration.support import IntegrationTestCase


class T009AttendeeCandidatesScopeTest(IntegrationTestCase):
    def test_attendee_candidates_scope(self):
        # 手順1: 一般ユーザーで scope=attendee_candidates
        self.assertEqual(self.login("user001").status_code, 200)
        res = self.client.get("/api/users?scope=attendee_candidates")
        self.assertEqual(res.status_code, 200)
        users = res.json()["users"]

        # 手順2: キーが user_id と name の2つだけ
        for user in users:
            self.assertEqual(set(user.keys()), {"user_id", "name"})

        # 手順3: 有効ユーザー3件のみ(無効の user003 を含まない)
        self.assertEqual([u["user_id"] for u in users], ["admin001", "user001", "user002"])
        self.assertNotIn("user003", [u["user_id"] for u in users])

        # 手順4: 一般ユーザーの scope=management は 403
        res = self.client.get("/api/users?scope=management")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

        # 手順5: 管理者も同じ射影で取得できる
        self.assertEqual(self.login("admin001").status_code, 200)
        res = self.client.get("/api/users?scope=attendee_candidates")
        self.assertEqual(res.status_code, 200)
        for user in res.json()["users"]:
            self.assertEqual(set(user.keys()), {"user_id", "name"})


if __name__ == "__main__":
    unittest.main()
