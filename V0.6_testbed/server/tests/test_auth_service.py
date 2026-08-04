import time
import unittest

from app.core.exceptions import InvalidCredentialsError
from app.repositories import session_repository
from app.services import auth_service
from tests.helpers import make_test_conn, seed_user


class AuthServiceTest(unittest.TestCase):
    def setUp(self):
        self.conn = make_test_conn()
        self.user_id = seed_user(self.conn, "E0001", "Passw0rd1")

    def tearDown(self):
        self.conn.close()

    def test_login_success_creates_session(self):
        user, session_id = auth_service.login(self.conn, "E0001", "Passw0rd1")
        self.assertEqual(user["employee_id"], "E0001")
        self.assertTrue(session_id)

    def test_resolve_current_user_after_login(self):
        _, session_id = auth_service.login(self.conn, "E0001", "Passw0rd1")
        resolved = auth_service.resolve_current_user(self.conn, session_id)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved["employee_id"], "E0001")

    def test_login_wrong_password_raises(self):
        with self.assertRaises(InvalidCredentialsError):
            auth_service.login(self.conn, "E0001", "WrongPassword")

    def test_login_unknown_employee_id_raises(self):
        with self.assertRaises(InvalidCredentialsError):
            auth_service.login(self.conn, "NOT_EXIST", "Passw0rd1")

    def test_login_inactive_user_raises(self):
        seed_user(self.conn, "E0099", "Passw0rd1", is_active=False)
        with self.assertRaises(InvalidCredentialsError):
            auth_service.login(self.conn, "E0099", "Passw0rd1")

    def test_resolve_current_user_expired_session_returns_none(self):
        _, session_id = auth_service.login(self.conn, "E0001", "Passw0rd1")
        # 強制的に期限切れにする
        self.conn.execute(
            "UPDATE SESSIONS SET expires_at = '2000-01-01T00:00:00Z' WHERE session_id = ?",
            (session_id,),
        )
        self.conn.commit()
        resolved = auth_service.resolve_current_user(self.conn, session_id)
        self.assertIsNone(resolved)

    def test_resolve_current_user_deactivated_user_returns_none_and_deletes_session(self):
        user_id = seed_user(self.conn, "E0002", "Passw0rd1")
        _, session_id = auth_service.login(self.conn, "E0002", "Passw0rd1")
        self.conn.execute("UPDATE USERS SET is_active = 0 WHERE id = ?", (user_id,))
        self.conn.commit()
        resolved = auth_service.resolve_current_user(self.conn, session_id)
        self.assertIsNone(resolved)
        self.assertIsNone(session_repository.find_valid(self.conn, session_id))

    def test_logout_removes_session(self):
        _, session_id = auth_service.login(self.conn, "E0001", "Passw0rd1")
        auth_service.logout(self.conn, session_id)
        self.assertIsNone(session_repository.find_valid(self.conn, session_id))

    def test_logout_nonexistent_session_does_not_raise(self):
        auth_service.logout(self.conn, "nonexistent-session-id")


if __name__ == "__main__":
    unittest.main()
