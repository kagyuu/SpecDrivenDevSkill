"""U002-T1 単体テスト — `002-rooms.sql` の適用と `rooms` Repository(P003 3.4 / 3.5)。"""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from meeting_room import db
from meeting_room.repositories import rooms_repo

NOW = "2026-08-05T00:00:00Z"


class RoomsRepoTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        db.apply_migrations(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)

    def _insert(self, name="会議室A", capacity=10, equipment="", description="", is_active=True):
        with db.transaction(self.conn):
            return rooms_repo.insert(
                self.conn, name, capacity, equipment, description, is_active, NOW
            )


class MigrationTest(RoomsRepoTestBase):
    # 正常系: 全マイグレーション適用で rooms が作られ、先頭2件のマイグレーションが記録される
    def test_rooms_table_created(self):
        tables = {
            r["name"]
            for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        self.assertIn("rooms", tables)
        versions = [r["version"] for r in self.conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        )]
        # 後続スプリントでマイグレーションが増えても壊れないよう先頭2件のみを固定で確認する
        # (U003で 003-reservations.sql を追加した。P007 5章「未解決事項」#10)
        self.assertEqual(versions[:2], ["001-init.sql", "002-rooms.sql"])

    # 正常系: 再適用しても行数が増えない(冪等)
    def test_reapply_is_idempotent(self):
        before = self.conn.execute("SELECT COUNT(*) AS c FROM schema_migrations").fetchone()["c"]
        applied = db.apply_migrations(db_path=self.db_path)
        self.assertEqual(applied, [])
        after = self.conn.execute("SELECT COUNT(*) AS c FROM schema_migrations").fetchone()["c"]
        self.assertEqual(after, before)

    # 正常系: 部分ユニークインデックスが存在する
    def test_partial_unique_index_exists(self):
        indexes = {
            r["name"]
            for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
        self.assertIn("uq_rooms_name_active", indexes)


class RoomsRepoTest(RoomsRepoTestBase):
    # 正常系: insert → find_by_id で一致
    def test_insert_then_find(self):
        room_id = self._insert(equipment="プロジェクタ", description="窓側の大会議室")
        room = rooms_repo.find_by_id(self.conn, room_id)
        self.assertEqual(room["name"], "会議室A")
        self.assertEqual(room["capacity"], 10)
        self.assertEqual(room["equipment"], "プロジェクタ")
        self.assertEqual(room["description"], "窓側の大会議室")
        self.assertIs(room["is_active"], True)
        self.assertEqual(room["created_at"], NOW)

    # 正常系: set_active(False) 後の一覧の出し分け
    def test_set_active_controls_listing(self):
        active_id = self._insert(name="会議室A")
        inactive_id = self._insert(name="会議室C")
        with db.transaction(self.conn):
            rooms_repo.set_active(self.conn, inactive_id, False, NOW)
        self.assertEqual(
            [r["room_id"] for r in rooms_repo.list_rooms(self.conn, include_inactive=False)],
            [active_id],
        )
        self.assertEqual(
            [r["room_id"] for r in rooms_repo.list_rooms(self.conn, include_inactive=True)],
            [active_id, inactive_id],
        )

    # 正常系: update で全項目が置換される
    def test_update_replaces_all_columns(self):
        room_id = self._insert()
        with db.transaction(self.conn):
            rooms_repo.update(
                self.conn, room_id, "会議室A2", 12, "ホワイトボード", "改装後", True,
                "2026-08-06T00:00:00Z",
            )
        room = rooms_repo.find_by_id(self.conn, room_id)
        self.assertEqual((room["name"], room["capacity"]), ("会議室A2", 12))
        self.assertEqual(room["updated_at"], "2026-08-06T00:00:00Z")
        self.assertEqual(room["created_at"], NOW)

    # 正常系: find_active_by_name は自分自身を除外できる
    def test_find_active_by_name_excludes_self(self):
        room_id = self._insert(name="会議室A")
        self.assertIsNotNone(rooms_repo.find_active_by_name(self.conn, "会議室A"))
        self.assertIsNone(
            rooms_repo.find_active_by_name(self.conn, "会議室A", exclude_room_id=room_id)
        )

    # 異常系: 有効な同名会議室は2件登録できない
    def test_duplicate_active_name_rejected(self):
        self._insert(name="会議室A")
        with self.assertRaises(sqlite3.IntegrityError):
            self._insert(name="会議室A")

    # 正常系: 片方を無効化すれば同名を登録できる(部分ユニーク)
    def test_same_name_allowed_after_deactivation(self):
        first = self._insert(name="会議室A")
        with db.transaction(self.conn):
            rooms_repo.set_active(self.conn, first, False, NOW)
        second = self._insert(name="会議室A")
        self.assertNotEqual(first, second)
        names = [r["name"] for r in rooms_repo.list_rooms(self.conn, include_inactive=True)]
        self.assertEqual(names, ["会議室A", "会議室A"])

    # 異常系: capacity の CHECK 制約
    def test_capacity_check_constraint(self):
        for capacity in (0, 501):
            with self.subTest(capacity=capacity):
                with self.assertRaises(sqlite3.IntegrityError):
                    self._insert(name=f"会議室{capacity}", capacity=capacity)

    # 異常系: 存在しない room_id
    def test_find_missing_room(self):
        self.assertIsNone(rooms_repo.find_by_id(self.conn, 999))


if __name__ == "__main__":
    unittest.main()
