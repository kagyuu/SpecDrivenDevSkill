"""U001-T4 単体テスト — セッション管理と認証サービス(P003 2.2 / 4.3 / 6.1)。"""

import tempfile
import unittest
from pathlib import Path

from meeting_room import config, db, security
from meeting_room.errors import ApiError
from meeting_room.repositories import sessions_repo, users_repo
from meeting_room.services import auth_service

NOW = "2026-08-05T00:00:00Z"


class AuthServiceTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        db.apply_migrations(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)
        self._add_user("user001", "山田 太郎", "general", True)
        self._add_user("admin001", "初期管理者", "admin", True)
        self._add_user("user003", "無効 三郎", "general", False)

    def _add_user(self, user_id, name, role, is_active, password="Passw0rd!23"):
        with db.transaction(self.conn):
            users_repo.insert(
                self.conn, user_id, name, security.hash_password(password), role, is_active, NOW
            )


class LoginTest(AuthServiceTestBase):
    # 正常系: 正しい資格情報でセッション行が作られる
    def test_login_creates_session(self):
        with db.transaction(self.conn):
            session_id, user = auth_service.login(self.conn, "user001", "Passw0rd!23")
        self.assertEqual(user["user_id"], "user001")
        self.assertEqual(user["name"], "山田 太郎")
        self.assertEqual(user["role"], "general")
        row = sessions_repo.find(self.conn, session_id)
        self.assertIsNotNone(row)
        self.assertEqual(row["user_id"], "user001")
        # 絶対有効期限は created_at + SESSION_ABSOLUTE_SECONDS(P003 2.2)
        self.assertEqual(
            row["expires_at"],
            auth_service.shift(row["created_at"], config.SESSION_ABSOLUTE_SECONDS),
        )

    # 異常系: 3ケースとも同一の 401 AUTH_FAILED メッセージ(P002 3.1)
    def test_login_failures_share_identical_message(self):
        cases = [("nosuchuser", "Passw0rd!23"), ("user001", "WrongPass123"), ("user003", "Passw0rd!23")]
        messages = set()
        for user_id, password in cases:
            with self.subTest(user_id=user_id):
                with self.assertRaises(ApiError) as ctx:
                    with db.transaction(self.conn):
                        auth_service.login(self.conn, user_id, password)
                self.assertEqual(ctx.exception.status, 401)
                self.assertEqual(ctx.exception.code, "AUTH_FAILED")
                messages.add(ctx.exception.message)
        self.assertEqual(messages, {"ユーザーIDまたはパスワードが正しくありません。"})
        self.assertEqual(sessions_repo.count(self.conn), 0)

    # 正常系: ログイン時に期限切れセッションが掃除される(P003 2.2)
    def test_login_deletes_expired_sessions(self):
        with db.transaction(self.conn):
            sessions_repo.create(
                self.conn, "stale", "user001", "2020-01-01T00:00:00Z",
                "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z",
            )
        with db.transaction(self.conn):
            auth_service.login(self.conn, "user001", "Passw0rd!23")
        self.assertIsNone(sessions_repo.find(self.conn, "stale"))


class ResolveSessionTest(AuthServiceTestBase):
    def _login(self, user_id="user001"):
        with db.transaction(self.conn):
            session_id, _ = auth_service.login(self.conn, user_id, "Passw0rd!23")
        return session_id

    # 正常系: 有効なセッションはユーザーを返し last_accessed_at を更新する
    def test_resolve_valid_session_touches(self):
        session_id = self._login()
        # 無操作タイムアウト内(60秒前)に巻き戻し、touch で更新されることを確認する
        one_minute_ago = auth_service.shift(security.now_utc(), -60)
        with db.transaction(self.conn):
            self.conn.execute(
                "UPDATE sessions SET last_accessed_at = ? WHERE session_id = ?",
                (one_minute_ago, session_id),
            )
        with db.transaction(self.conn):
            user = auth_service.resolve_session(self.conn, session_id)
        self.assertEqual(user["user_id"], "user001")
        self.assertNotEqual(
            sessions_repo.find(self.conn, session_id)["last_accessed_at"], one_minute_ago
        )

    # 異常系: 無操作9時間で無効になり、行が削除される
    def test_idle_timeout_deletes_row(self):
        session_id = self._login()
        nine_hours_ago = auth_service.shift(security.now_utc(), -9 * 3600)
        with db.transaction(self.conn):
            self.conn.execute(
                "UPDATE sessions SET last_accessed_at = ? WHERE session_id = ?",
                (nine_hours_ago, session_id),
            )
        with db.transaction(self.conn):
            self.assertIsNone(auth_service.resolve_session(self.conn, session_id))
        self.assertIsNone(sessions_repo.find(self.conn, session_id))

    # 異常系: 絶対有効期限切れ
    def test_absolute_expiry_deletes_row(self):
        session_id = self._login()
        with db.transaction(self.conn):
            self.conn.execute(
                "UPDATE sessions SET expires_at = ? WHERE session_id = ?",
                ("2020-01-01T00:00:00Z", session_id),
            )
        with db.transaction(self.conn):
            self.assertIsNone(auth_service.resolve_session(self.conn, session_id))
        self.assertIsNone(sessions_repo.find(self.conn, session_id))

    # 異常系: 所有ユーザーが無効化されたセッション
    def test_inactive_owner_invalidates_session(self):
        session_id = self._login()
        with db.transaction(self.conn):
            users_repo.set_active(self.conn, "user001", False, NOW)
        with db.transaction(self.conn):
            self.assertIsNone(auth_service.resolve_session(self.conn, session_id))
        self.assertIsNone(sessions_repo.find(self.conn, session_id))

    # 異常系: 未知・空のセッションID
    def test_unknown_session_id(self):
        with db.transaction(self.conn):
            self.assertIsNone(auth_service.resolve_session(self.conn, "unknown"))
            self.assertIsNone(auth_service.resolve_session(self.conn, None))

    # 正常系: ログアウトで行が消える
    def test_logout_deletes_session(self):
        session_id = self._login()
        with db.transaction(self.conn):
            auth_service.logout(self.conn, session_id)
        self.assertIsNone(sessions_repo.find(self.conn, session_id))
        # 存在しないセッションのログアウトも例外にしない
        with db.transaction(self.conn):
            auth_service.logout(self.conn, session_id)


if __name__ == "__main__":
    unittest.main()
