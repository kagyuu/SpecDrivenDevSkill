import os
import sqlite3
import tempfile
import unittest

from app.db.connection import init_db

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


if __name__ == "__main__":
    unittest.main()
