"""A006 — 認証セッションのライフサイクル(API側)。

docs/P009-acceptance-direction/A006-session-lifecycle.md
手順5(画面遷移とメッセージ)は `client/tests/acceptance/test_a006_session_ui.js` が確認する。
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from tests.acceptance.base import AcceptanceTestCase


def _iso(delta_seconds: int) -> str:
    """`security.now_utc()` と同じ形式で、現在からの相対時刻を作る。"""
    from meeting_room.security import now_utc

    sample = now_utc()
    moment = datetime.now(timezone.utc) + timedelta(seconds=delta_seconds)
    # now_utc() の書式("YYYY-MM-DDTHH:MM:SSZ" 等)に合わせる
    if sample.endswith("Z"):
        return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    return moment.isoformat()


class A006SessionLifecycleTest(AcceptanceTestCase):
    seed_rooms = False

    def _sid(self, client) -> str:
        return client.cookie.split("=", 1)[1]

    def _set_session(self, sid: str, **columns) -> None:
        conn = self.db()
        for column, value in columns.items():
            conn.execute(
                f"UPDATE sessions SET {column} = ? WHERE session_id = ?", (value, sid)
            )

    def test_session_lifecycle(self):
        # 手順1: ログインし Set-Cookie の属性を確認する
        res = self.client.login("user001")
        self.assertEqual(res.status, 200, res.text)
        cookie_header = "; ".join(res.set_cookies)
        for attribute in ("HttpOnly", "SameSite=Lax", "Secure", "Path=/"):
            self.assertIn(attribute, cookie_header, cookie_header)
        sid = self._sid(self.client)

        # 手順2: last_accessed_at を30分前に巻き戻してもセッションは維持される
        self._set_session(sid, last_accessed_at=_iso(-30 * 60))
        self.assertEqual(self.client.get("/api/me").status, 200)

        # 手順3: last_accessed_at を9時間前(無操作タイムアウト8時間超)→ 401
        self._set_session(sid, last_accessed_at=_iso(-9 * 3600))
        res = self.client.get("/api/me")
        self.assertEqual(res.status, 401, res.text)
        self.assertEqual(res.error_code(), "UNAUTHENTICATED")

        # 手順4: 再ログインし expires_at を過去にする(絶対期限)→ 401
        self.assertEqual(self.client.login("user001").status, 200)
        sid = self._sid(self.client)
        self._set_session(sid, expires_at=_iso(-60))
        res = self.client.get("/api/me")
        self.assertEqual(res.status, 401, res.text)
        self.assertEqual(res.error_code(), "UNAUTHENTICATED")

        # 手順6: 再ログイン → admin001 が user001 を無効化 → 401
        self.assertEqual(self.client.login("user001").status, 200)
        admin = self.new_client()
        self.assertEqual(admin.login("admin001").status, 200)
        res = admin.put(
            "/api/users/user001", {"name": "山田 太郎", "role": "general", "is_active": False}
        )
        self.assertEqual(res.status, 200, res.text)
        res = self.client.get("/api/me")
        self.assertEqual(res.status, 401, res.text)
        self.assertEqual(res.error_code(), "UNAUTHENTICATED")

        # 手順7: user001 を有効に戻して再ログイン → role を admin に変更 → 401
        res = admin.put(
            "/api/users/user001", {"name": "山田 太郎", "role": "general", "is_active": True}
        )
        self.assertEqual(res.status, 200, res.text)
        self.assertEqual(self.client.login("user001").status, 200)
        res = admin.put(
            "/api/users/user001", {"name": "山田 太郎", "role": "admin", "is_active": True}
        )
        self.assertEqual(res.status, 200, res.text)
        res = self.client.get("/api/me")
        self.assertEqual(res.status, 401, res.text)
        self.assertEqual(res.error_code(), "UNAUTHENTICATED")

        # 手順8: ログアウトしてから同じCookieでアクセス → 401
        self.assertEqual(self.client.login("user001").status, 200)
        stale = self.client.cookie
        self.assertEqual(self.client.post("/api/auth/logout").status, 204)
        res = self.client.get("/api/me", cookie=stale)
        self.assertEqual(res.status, 401, res.text)
        self.assertEqual(res.error_code(), "UNAUTHENTICATED")


if __name__ == "__main__":
    unittest.main()
