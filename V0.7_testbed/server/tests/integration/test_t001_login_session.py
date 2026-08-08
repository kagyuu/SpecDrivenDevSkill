"""T001 — ログインとセッションCookieの発行(docs/P008-test-direction/T001-login-session.md)。"""

import unittest

from meeting_room.repositories import sessions_repo
from tests.integration.support import IntegrationTestCase


class T001LoginSessionTest(IntegrationTestCase):
    def test_login_issues_cookie_and_me_works(self):
        # 手順1: ログイン
        res = self.client.post(
            "/api/auth/login", json={"user_id": "user001", "password": "Passw0rd!23"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {"user": {"user_id": "user001", "name": "山田 太郎", "role": "general"}}
        )
        # 手順2: Set-Cookie の属性
        set_cookie = res.headers["set-cookie"]
        for attr in ("sid=", "HttpOnly", "SameSite=Lax", "Secure", "Path=/"):
            self.assertIn(attr, set_cookie)
        # 手順3: 同じCookieで GET /api/me
        me = self.client.get("/api/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["user"]["user_id"], "user001")
        # 手順4: sessions の行数
        conn = self.db()
        self.assertEqual(sessions_repo.count(conn), 1)
        self.assertEqual(
            conn.execute("SELECT user_id FROM sessions").fetchone()["user_id"], "user001"
        )
        # 手順5: ログアウト後は 401 で行が消える
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        again = self.client.get("/api/me")
        self.assertEqual(again.status_code, 401)
        self.assertEqual(again.json()["error"]["code"], "UNAUTHENTICATED")
        self.assertEqual(sessions_repo.count(self.db()), 0)


if __name__ == "__main__":
    unittest.main()
