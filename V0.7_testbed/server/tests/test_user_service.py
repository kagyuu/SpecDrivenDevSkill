"""U002-T3 単体テスト — ユーザーの業務ルール(P003 6.3)。"""

import tempfile
import unittest
from pathlib import Path

from meeting_room import db, security
from meeting_room.errors import ApiError
from meeting_room.repositories import sessions_repo, users_repo
from meeting_room.schemas import UserCreateRequest, UserUpdateRequest, validate
from meeting_room.services import user_service

NOW = "2026-08-05T00:00:00Z"


def create_payload(**overrides):
    data = {"user_id": "user900", "name": "新規 太郎", "role": "general",
            "password": "Passw0rd!23", "is_active": True}
    data.update(overrides)
    return validate(UserCreateRequest, data)


def update_payload(**overrides):
    data = {"name": "更新 太郎", "role": "general", "is_active": True}
    data.update(overrides)
    return validate(UserUpdateRequest, data)


class UserServiceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        db.apply_migrations(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)
        self._add("admin001", "初期管理者", "admin", True)
        self._add("user001", "山田 太郎", "general", True)
        self._add("user002", "鈴木 花子", "general", True)
        self._add("user003", "無効 三郎", "general", False)
        self.admin = users_repo.find_by_id(self.conn, "admin001")

    def _add(self, user_id, name, role, is_active):
        with db.transaction(self.conn):
            users_repo.insert(
                self.conn, user_id, name, security.hash_password("Passw0rd!23"), role,
                is_active, NOW,
            )

    # 正常系: 登録するとハッシュが scrypt$ で始まる
    def test_create_user(self):
        user = user_service.create_user(self.conn, create_payload())
        self.assertEqual(user["user_id"], "user900")
        self.assertNotIn("password", user)
        self.assertNotIn("password_hash", user)
        stored = users_repo.find_by_id_with_hash(self.conn, "user900")
        self.assertTrue(stored["password_hash"].startswith("scrypt$"))

    # 異常系: 既存ID(有効・無効の両方)は 409 DUPLICATE_KEY
    def test_duplicate_user_id(self):
        for existing in ("user001", "user003"):
            with self.subTest(user_id=existing):
                with self.assertRaises(ApiError) as ctx:
                    user_service.create_user(self.conn, create_payload(user_id=existing))
                self.assertEqual((ctx.exception.status, ctx.exception.code), (409, "DUPLICATE_KEY"))

    # 正常系: password 省略の更新はハッシュを変えない
    def test_update_without_password_keeps_hash(self):
        before = users_repo.find_by_id_with_hash(self.conn, "user001")["password_hash"]
        user = user_service.update_user(self.conn, "user001", update_payload(name="山田 次郎"))
        self.assertEqual(user["name"], "山田 次郎")
        self.assertEqual(users_repo.find_by_id_with_hash(self.conn, "user001")["password_hash"], before)

    # 正常系: password 指定の更新は新しいパスワードで検証できる
    def test_update_with_password(self):
        user_service.update_user(self.conn, "user001", update_payload(password="NewPassw0rd!"))
        stored = users_repo.find_by_id_with_hash(self.conn, "user001")["password_hash"]
        self.assertTrue(security.verify_password("NewPassw0rd!", stored))

    # 正常系: 権限変更でセッションが全削除される(P003 4.3)
    def test_role_change_deletes_sessions(self):
        with db.transaction(self.conn):
            sessions_repo.create(self.conn, "s1", "user001", NOW, NOW, "2099-01-01T00:00:00Z")
        user_service.update_user(self.conn, "user001", update_payload(role="admin"))
        self.assertIsNone(sessions_repo.find(self.conn, "s1"))

    # 正常系: 無効化でセッションが消え、冪等
    def test_deactivate_user(self):
        with db.transaction(self.conn):
            sessions_repo.create(self.conn, "s2", "user002", NOW, NOW, "2099-01-01T00:00:00Z")
        user_service.deactivate_user(self.conn, self.admin, "user002")
        self.assertIs(users_repo.find_by_id(self.conn, "user002")["is_active"], False)
        self.assertIsNone(sessions_repo.find(self.conn, "s2"))
        user_service.deactivate_user(self.conn, self.admin, "user002")  # 冪等

    # 異常系: 自分自身の無効化は 409
    def test_cannot_deactivate_self(self):
        with self.assertRaises(ApiError) as ctx:
            user_service.deactivate_user(self.conn, self.admin, "admin001")
        self.assertEqual((ctx.exception.status, ctx.exception.code), (409, "CONSTRAINT_VIOLATION"))
        self.assertEqual(ctx.exception.message, "自分自身を無効化することはできません。")

    # 異常系: 最後の有効な管理者の降格・無効化は 409
    def test_last_admin_is_protected(self):
        for payload in (update_payload(role="general"), update_payload(role="admin", is_active=False)):
            with self.subTest(payload=payload):
                with self.assertRaises(ApiError) as ctx:
                    user_service.update_user(self.conn, "admin001", payload)
                self.assertEqual(ctx.exception.code, "CONSTRAINT_VIOLATION")
        # 管理者がもう1人いれば降格できる
        user_service.create_user(self.conn, create_payload(user_id="admin900", role="admin"))
        updated = user_service.update_user(self.conn, "admin001", update_payload(role="general"))
        self.assertEqual(updated["role"], "general")

    # 異常系: 存在しないユーザーは 404
    def test_missing_user(self):
        with self.assertRaises(ApiError) as ctx:
            user_service.update_user(self.conn, "nosuchuser", update_payload())
        self.assertEqual(ctx.exception.status, 404)
        with self.assertRaises(ApiError) as ctx:
            user_service.deactivate_user(self.conn, self.admin, "nosuchuser")
        self.assertEqual(ctx.exception.status, 404)

    # 正常系: scope=attendee_candidates の射影と対象
    def test_attendee_candidates_projection(self):
        rows = user_service.list_users(
            self.conn, {"user_id": "user001", "role": "general"},
            user_service.SCOPE_ATTENDEE_CANDIDATES,
        )
        self.assertEqual([r["user_id"] for r in rows], ["admin001", "user001", "user002"])
        for row in rows:
            self.assertEqual(set(row.keys()), {"user_id", "name"})

    # 正常系: scope=management は全項目・無効ユーザーを含む
    def test_management_scope(self):
        rows = user_service.list_users(
            self.conn, self.admin, user_service.SCOPE_MANAGEMENT, include_inactive=True
        )
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            set(rows[0].keys()),
            {"user_id", "name", "role", "is_active", "created_at", "updated_at"},
        )
        active_only = user_service.list_users(
            self.conn, self.admin, user_service.SCOPE_MANAGEMENT, include_inactive=False
        )
        self.assertEqual(len(active_only), 3)


if __name__ == "__main__":
    unittest.main()
