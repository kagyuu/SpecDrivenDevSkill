"""T002 — 認証失敗と未認証アクセス(docs/P008-test-direction/T002-auth-failure.md)。"""

import unittest

from meeting_room import db, security
from meeting_room.repositories import sessions_repo
from meeting_room.services import auth_service
from tests.integration.support import IntegrationTestCase


class T002AuthFailureTest(IntegrationTestCase):
    def test_auth_failures(self):
        # 手順1〜3: ID不明・パスワード不一致・無効アカウント
        messages = set()
        for user_id, password in (
            ("nosuchuser", "Passw0rd!23"),
            ("user001", "WrongPass123"),
            ("user003", "Passw0rd!23"),
        ):
            res = self.login(user_id, password)
            self.assertEqual(res.status_code, 401, f"{user_id} のステータス")
            self.assertEqual(res.json()["error"]["code"], "AUTH_FAILED")
            messages.add(res.json()["error"]["message"])
        self.assertEqual(messages, {"ユーザーIDまたはパスワードが正しくありません。"})

        # 手順4: Cookieなしの GET /api/me
        self.client.cookies.clear()
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], "UNAUTHENTICATED")

        # 手順5: last_accessed_at を9時間前に書き換える
        self.assertEqual(self.login("user001").status_code, 200)
        conn = self.db()
        nine_hours_ago = auth_service.shift(security.now_utc(), -9 * 3600)
        with db.transaction(conn):
            conn.execute("UPDATE sessions SET last_accessed_at = ?", (nine_hours_ago,))
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], "UNAUTHENTICATED")

        # 手順6: 期限切れセッション行が削除されている
        self.assertEqual(sessions_repo.count(self.db()), 0)

        # 手順7: user_id が2文字
        res = self.login("ab")
        self.assertEqual(res.status_code, 400)
        error = res.json()["error"]
        self.assertEqual(error["code"], "VALIDATION_ERROR")
        self.assertEqual(error["details"][0]["field"], "user_id")
        self.assertEqual(
            error["details"][0]["message"], "ユーザーIDは半角英数字4〜20文字で入力してください。"
        )


if __name__ == "__main__":
    unittest.main()
