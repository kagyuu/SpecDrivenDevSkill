import os
import sqlite3
import tempfile
import unittest

from app.db.connection import MIGRATIONS_DIR, init_db

EXPECTED_TABLES = {"USERS", "ROOMS", "RESERVATIONS", "RESERVATION_PARTICIPANTS", "SESSIONS"}


class InitDbTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.path)  # init_db should create it fresh

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_creates_all_tables(self):
        init_db(self.path)
        conn = sqlite3.connect(self.path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {row[0] for row in rows}
            self.assertTrue(EXPECTED_TABLES.issubset(table_names))
        finally:
            conn.close()

    def test_idempotent_when_run_twice(self):
        init_db(self.path)
        # Running again must not raise.
        init_db(self.path)
        conn = sqlite3.connect(self.path)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {row[0] for row in rows}
            self.assertTrue(EXPECTED_TABLES.issubset(table_names))
        finally:
            conn.close()


class DbInitIdempotencyTest(unittest.TestCase):
    """T028: 初期化処理の冪等性(再起動耐性)。

    `docs/P006-test-plan.md` §3「運用(再起動耐性)」の観点を自動化したもの。
    CR-003で追加した `ALTER TABLE RESERVATIONS ADD COLUMN attendee_count INTEGER` は
    非冪等なDDLであり、テストごとに新しい一時DBを作る他のテストでは
    構造的に検出できない(常に初回実行になるため)。
    """

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def _columns(self, table: str) -> set:
        conn = sqlite3.connect(self.path)
        try:
            return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        finally:
            conn.close()

    def test_init_db_twice_succeeds_and_keeps_schema(self):
        init_db(self.path)          # 手順1: 1回目(初回起動相当)
        init_db(self.path)          # 手順2: 2回目(再起動相当)。例外を送出しないこと
        self.assertIn("attendee_count", self._columns("RESERVATIONS"))
        self.assertIn("description", self._columns("ROOMS"))

    def test_data_survives_restart(self):
        init_db(self.path)
        conn = sqlite3.connect(self.path)
        conn.execute(
            "INSERT INTO ROOMS (name, capacity, equipment, is_active, created_at, updated_at) "
            "VALUES ('会議室X', 5, '', 1, '2026-08-04T00:00:00Z', '2026-08-04T00:00:00Z')")
        conn.commit()
        conn.close()

        init_db(self.path)          # 再起動相当
        conn = sqlite3.connect(self.path)
        try:
            names = [row[0] for row in conn.execute("SELECT name FROM ROOMS")]
        finally:
            conn.close()
        self.assertIn("会議室X", names)

    def test_migrations_are_recorded(self):
        init_db(self.path)
        conn = sqlite3.connect(self.path)
        try:
            recorded = {row[0] for row in conn.execute("SELECT filename FROM SCHEMA_MIGRATIONS")}
        finally:
            conn.close()
        self.assertIn("0001_initial.sql", recorded)
        self.assertIn("0003_add_reservation_attendee_count.sql", recorded)

    def test_migrates_from_pre_cr003_database(self):
        """CR-003以前(SCHEMA_MIGRATIONS無し、0001・0002適用済み)のDBからの移行。"""
        migrations_dir = MIGRATIONS_DIR
        conn = sqlite3.connect(self.path)
        for name in ("0001_initial.sql", "0002_add_room_description.sql"):
            conn.executescript((migrations_dir / name).read_text(encoding="utf-8"))
        conn.commit()
        conn.close()
        self.assertNotIn("attendee_count", self._columns("RESERVATIONS"))

        init_db(self.path)          # 移行1回目
        init_db(self.path)          # 移行後の再起動
        self.assertIn("attendee_count", self._columns("RESERVATIONS"))
        self.assertIn("description", self._columns("ROOMS"))


if __name__ == "__main__":
    unittest.main()
