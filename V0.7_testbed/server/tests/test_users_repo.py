"""U001-T3 単体テスト — `users` Repository と初期管理者シード(P003 3.6 / 6.3)。"""

import tempfile
import unittest
from pathlib import Path

from meeting_room import config, db, security
from meeting_room.repositories import users_repo

NOW = "2026-08-05T00:00:00Z"


class UsersRepoTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        db.apply_migrations(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)

    def _insert(self, user_id, name="山田 太郎", role="general", is_active=True):
        with db.transaction(self.conn):
            users_repo.insert(
                self.conn, user_id, name, security.hash_password("Passw0rd!23"), role,
                is_active, NOW,
            )


class UsersRepoTest(UsersRepoTestBase):
    # 正常系: insert → find_by_id で同じ行が返る
    def test_insert_then_find(self):
        self._insert("user001")
        user = users_repo.find_by_id(self.conn, "user001")
        self.assertEqual(user["user_id"], "user001")
        self.assertEqual(user["name"], "山田 太郎")
        self.assertEqual(user["role"], "general")
        self.assertIs(user["is_active"], True)
        # password_hash を含めない(P002 5.3)
        self.assertNotIn("password_hash", user)

    # 正常系: find_by_id_with_hash だけが password_hash を返す
    def test_find_by_id_with_hash(self):
        self._insert("user001")
        user = users_repo.find_by_id_with_hash(self.conn, "user001")
        self.assertTrue(user["password_hash"].startswith("scrypt$"))

    # 正常系: set_active(False) 後は include_inactive=False の一覧に出ない
    def test_set_active_hides_from_active_list(self):
        self._insert("user001")
        self._insert("user002", name="鈴木 花子")
        with db.transaction(self.conn):
            users_repo.set_active(self.conn, "user002", False, NOW)
        active = [u["user_id"] for u in users_repo.list_users(self.conn, include_inactive=False)]
        allu = [u["user_id"] for u in users_repo.list_users(self.conn, include_inactive=True)]
        self.assertEqual(active, ["user001"])
        self.assertEqual(allu, ["user001", "user002"])

    # 正常系: count_active_admins が期待値を返す
    def test_count_active_admins(self):
        self._insert("admin001", role="admin")
        self._insert("admin002", role="admin")
        self._insert("user001")
        self.assertEqual(users_repo.count_active_admins(self.conn), 2)
        self.assertEqual(users_repo.count_active_admins(self.conn, exclude_user_id="admin001"), 1)
        with db.transaction(self.conn):
            users_repo.set_active(self.conn, "admin002", False, NOW)
        self.assertEqual(users_repo.count_active_admins(self.conn), 1)

    # 正常系: list_active_id_and_name は user_id と name だけを返す
    def test_list_active_id_and_name_projection(self):
        self._insert("user001")
        self._insert("user002", name="鈴木 花子", is_active=False)
        rows = users_repo.list_active_id_and_name(self.conn)
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(rows[0].keys()), {"user_id", "name"})

    # 正常系: update は password 未指定ならハッシュを変えない
    def test_update_keeps_hash_when_password_omitted(self):
        self._insert("user001")
        before = users_repo.find_by_id_with_hash(self.conn, "user001")["password_hash"]
        with db.transaction(self.conn):
            users_repo.update(self.conn, "user001", "新しい 氏名", "admin", True, "2026-08-06T00:00:00Z")
        after = users_repo.find_by_id_with_hash(self.conn, "user001")
        self.assertEqual(after["password_hash"], before)
        self.assertEqual(after["name"], "新しい 氏名")
        self.assertEqual(after["role"], "admin")
        self.assertEqual(after["updated_at"], "2026-08-06T00:00:00Z")

    # 異常系: 存在しない user_id は None
    def test_find_missing_user(self):
        self.assertIsNone(users_repo.find_by_id(self.conn, "nosuchuser"))
        self.assertIsNone(users_repo.find_by_id_with_hash(self.conn, "nosuchuser"))


class SeedInitialAdminTest(UsersRepoTestBase):
    def setUp(self):
        super().setUp()
        self._orig = (config.INITIAL_ADMIN_ID, config.INITIAL_ADMIN_PASSWORD)
        config.INITIAL_ADMIN_ID = "admin001"
        config.INITIAL_ADMIN_PASSWORD = "Passw0rd!23"

        def restore():
            config.INITIAL_ADMIN_ID, config.INITIAL_ADMIN_PASSWORD = self._orig

        self.addCleanup(restore)

    # シード: 空DBに1回呼ぶと管理者が1人
    def test_seed_creates_one_admin(self):
        self.assertTrue(db.seed_initial_admin(db_path=self.db_path))
        admins = [u for u in users_repo.list_users(self.conn) if u["role"] == "admin"]
        self.assertEqual(len(admins), 1)
        self.assertEqual(admins[0]["user_id"], "admin001")
        self.assertEqual(admins[0]["name"], "初期管理者")

    # シード: 2回呼んでも1人のまま(冪等)
    def test_seed_is_idempotent(self):
        db.seed_initial_admin(db_path=self.db_path)
        self.assertFalse(db.seed_initial_admin(db_path=self.db_path))
        self.assertEqual(len(users_repo.list_users(self.conn)), 1)

    # シード: 既に別の管理者がいる場合は追加しない
    def test_seed_skipped_when_another_admin_exists(self):
        self._insert("boss0001", name="既存 管理者", role="admin")
        self.assertFalse(db.seed_initial_admin(db_path=self.db_path))
        self.assertEqual([u["user_id"] for u in users_repo.list_users(self.conn)], ["boss0001"])

    # シード: 投入されたパスワードで検証が通る
    def test_seeded_password_is_verifiable(self):
        db.seed_initial_admin(db_path=self.db_path)
        stored = users_repo.find_by_id_with_hash(self.conn, "admin001")["password_hash"]
        self.assertTrue(security.verify_password("Passw0rd!23", stored))


if __name__ == "__main__":
    unittest.main()
