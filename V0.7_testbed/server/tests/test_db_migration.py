"""U001-T1 単体テスト — 差分適用型マイグレーション(P003 3.5 / ADR-009)。"""

import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from meeting_room import db


def _table_names(path: str) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()


def _versions(path: str) -> list[str]:
    conn = sqlite3.connect(path)
    try:
        return [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
    finally:
        conn.close()


def _columns(path: str, table: str) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


class ApplyMigrationsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.db_path = str(self.tmp / "app.db")
        self.addCleanup(self._tmp.cleanup)

    # 正常系1: 空のDBに適用する
    def test_apply_to_empty_db_creates_tables(self):
        applied = db.apply_migrations(db_path=self.db_path)
        self.assertIn("001-init.sql", applied)
        tables = _table_names(self.db_path)
        self.assertIn("users", tables)
        self.assertIn("sessions", tables)
        self.assertIn("schema_migrations", tables)
        self.assertIn("001-init.sql", _versions(self.db_path))

    # 正常系2: 同じDBに2回目を適用しても失敗せず、行数も増えない(冪等性。P006 3.3 V-O-02)
    def test_apply_twice_is_idempotent(self):
        db.apply_migrations(db_path=self.db_path)
        first = _versions(self.db_path)
        db.apply_migrations(db_path=self.db_path)  # 例外が出ないこと
        second = _versions(self.db_path)
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(second))

    # 正常系3: 追加のマイグレーションファイルだけが適用される(ALTER TABLE を含む)
    def test_only_new_migration_is_applied(self):
        mig_dir = self.tmp / "migrations"
        mig_dir.mkdir()
        for src in sorted(db.MIGRATIONS_DIR.glob("*.sql")):
            shutil.copy(src, mig_dir / src.name)
        db.apply_migrations(db_path=self.db_path, migrations_dir=mig_dir)
        before = _versions(self.db_path)
        self.assertNotIn("memo", _columns(self.db_path, "users"))

        (mig_dir / "999-test.sql").write_text(
            "ALTER TABLE users ADD COLUMN memo TEXT;\n", encoding="utf-8"
        )
        applied = db.apply_migrations(db_path=self.db_path, migrations_dir=mig_dir)
        self.assertEqual(applied, ["999-test.sql"])
        self.assertIn("memo", _columns(self.db_path, "users"))
        self.assertEqual(_versions(self.db_path), sorted(before + ["999-test.sql"]))

        # さらにもう一度適用しても失敗しない(ADD COLUMN の再実行が起きない)
        applied_again = db.apply_migrations(db_path=self.db_path, migrations_dir=mig_dir)
        self.assertEqual(applied_again, [])

    # 異常系: 不正なSQLを含むファイルは例外を送出し、version が記録されない(ロールバック)
    def test_broken_migration_rolls_back(self):
        mig_dir = self.tmp / "migrations"
        mig_dir.mkdir()
        for src in sorted(db.MIGRATIONS_DIR.glob("*.sql")):
            shutil.copy(src, mig_dir / src.name)
        (mig_dir / "998-broken.sql").write_text(
            "CREATE TABLE broken_ok (id INTEGER);\nTHIS IS NOT SQL;\n", encoding="utf-8"
        )
        with self.assertRaises(sqlite3.Error):
            db.apply_migrations(db_path=self.db_path, migrations_dir=mig_dir)
        self.assertNotIn("998-broken.sql", _versions(self.db_path))
        self.assertNotIn("broken_ok", _table_names(self.db_path))

    # ※CR-001: 004 が適用され `reservations.meeting_url` が存在する
    def test_004_adds_meeting_url_column(self):
        applied = db.apply_migrations(db_path=self.db_path)
        self.assertIn("004-meeting-url.sql", applied)
        self.assertIn("meeting_url", _columns(self.db_path, "reservations"))
        self.assertEqual(
            _versions(self.db_path),
            ["001-init.sql", "002-rooms.sql", "003-reservations.sql", "004-meeting-url.sql"],
        )

    # ※CR-001: 003 までを適用済みの既存DBに 004 だけが差分適用され、既存行は '' になる
    def test_004_applies_to_existing_db_and_backfills_empty_string(self):
        mig_dir = self.tmp / "migrations"
        mig_dir.mkdir()
        for src in sorted(db.MIGRATIONS_DIR.glob("*.sql")):
            if src.name.startswith("004"):
                continue
            shutil.copy(src, mig_dir / src.name)
        db.apply_migrations(db_path=self.db_path, migrations_dir=mig_dir)
        self.assertNotIn("meeting_url", _columns(self.db_path, "reservations"))
        # CR-001 以前に登録された予約に相当する行を作る
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute(
                "INSERT INTO reservations(room_id, user_id, reserved_date, start_time,"
                " end_time, title, attendee_count, note, created_at, updated_at)"
                " VALUES (1, 'legacy001', '2026-08-10', '09:00', '10:00', '既存予約',"
                " NULL, '', '2026-08-05T00:00:00Z', '2026-08-05T00:00:00Z')"
            )
            conn.commit()
        finally:
            conn.close()

        shutil.copy(db.MIGRATIONS_DIR / "004-meeting-url.sql", mig_dir / "004-meeting-url.sql")
        applied = db.apply_migrations(db_path=self.db_path, migrations_dir=mig_dir)
        self.assertEqual(applied, ["004-meeting-url.sql"])
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT meeting_url FROM reservations WHERE title = '既存予約'"
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(row[0], "")  # NULL ではなく空文字

        # ※CR-001: ADD COLUMN は IF NOT EXISTS を持たないため、2回目の適用で失敗しないことが必須
        self.assertEqual(
            db.apply_migrations(db_path=self.db_path, migrations_dir=mig_dir), []
        )
        self.assertIn("004-meeting-url.sql", _versions(self.db_path))

    # 分割ユーティリティ: `;` 区切り・空文の読み飛ばし
    def test_split_sql_statements_skips_empty(self):
        stmts = db.split_sql_statements("-- comment\nCREATE TABLE a (x INT);\n\n;\nSELECT 1;\n")
        self.assertEqual(len(stmts), 2)


if __name__ == "__main__":
    unittest.main()
