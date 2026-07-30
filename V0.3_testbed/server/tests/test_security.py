import unittest
from datetime import datetime, timedelta, timezone

from app.db import get_connection
from app.security import (
    create_session,
    get_session_user,
    hash_password,
    verify_password,
)


class TestSecurity(unittest.TestCase):
    def test_verify_password_success(self):
        hashed = hash_password("mypassword")
        self.assertTrue(verify_password("mypassword", hashed))

    def test_verify_password_failure(self):
        hashed = hash_password("mypassword")
        self.assertFalse(verify_password("wrongpassword", hashed))

    def test_hash_is_salted_and_differs_each_time(self):
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        self.assertNotEqual(h1, h2)
        self.assertTrue(verify_password("samepassword", h1))
        self.assertTrue(verify_password("samepassword", h2))

    def test_session_valid_immediately_after_creation(self):
        conn = get_connection(":memory:")
        conn.execute(
            "INSERT INTO users (employee_id, name, password_hash, role, is_active) VALUES ('e1','n','h','general',1)"
        )
        conn.commit()
        user_id = conn.execute("SELECT id FROM users").fetchone()["id"]
        session_id = create_session(conn, user_id)
        user = get_session_user(conn, session_id)
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], user_id)

    def test_expired_session_returns_none(self):
        conn = get_connection(":memory:")
        conn.execute(
            "INSERT INTO users (employee_id, name, password_hash, role, is_active) VALUES ('e1','n','h','general',1)"
        )
        conn.commit()
        user_id = conn.execute("SELECT id FROM users").fetchone()["id"]
        session_id = create_session(conn, user_id)
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        conn.execute("UPDATE sessions SET expires_at = ? WHERE session_id = ?", (past, session_id))
        conn.commit()
        user = get_session_user(conn, session_id)
        self.assertIsNone(user)


if __name__ == "__main__":
    unittest.main()
