import unittest

from app.db import get_connection
from app.seed import seed


class TestDb(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")

    def test_schema_creates_five_tables(self):
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        names = {r["name"] for r in rows}
        self.assertEqual(
            names, {"users", "rooms", "reservations", "reservation_participants", "sessions"}
        )

    def test_seed_creates_admin(self):
        seed(self.conn)
        row = self.conn.execute("SELECT * FROM users WHERE employee_id='admin'").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["role"], "admin")

    def test_seed_is_idempotent(self):
        seed(self.conn)
        seed(self.conn)
        count = self.conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        self.assertEqual(count, 3)


if __name__ == "__main__":
    unittest.main()
