import unittest

from app.db import get_connection
from app.repositories import users as users_repo


class TestUsersRepo(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")

    def test_create_and_get(self):
        u = users_repo.create_user(self.conn, "e1", "太郎", "general", "password1")
        fetched = users_repo.get_user(self.conn, u["id"])
        self.assertEqual(fetched["employee_id"], "e1")
        self.assertNotIn("password_hash", fetched)

    def test_employee_id_duplicate_detected(self):
        users_repo.create_user(self.conn, "e1", "太郎", "general", "password1")
        self.assertTrue(users_repo.employee_id_exists(self.conn, "e1"))

    def test_update_without_password_keeps_hash(self):
        u = users_repo.create_user(self.conn, "e1", "太郎", "general", "password1")
        before = users_repo.get_user_by_employee_id(self.conn, "e1")["password_hash"]
        users_repo.update_user(self.conn, u["id"], "太郎2", "general", True, None)
        after = users_repo.get_user_by_employee_id(self.conn, "e1")["password_hash"]
        self.assertEqual(before, after)

    def test_update_with_password_changes_hash(self):
        u = users_repo.create_user(self.conn, "e1", "太郎", "general", "password1")
        before = users_repo.get_user_by_employee_id(self.conn, "e1")["password_hash"]
        users_repo.update_user(self.conn, u["id"], "太郎", "general", True, "newpassword")
        after = users_repo.get_user_by_employee_id(self.conn, "e1")["password_hash"]
        self.assertNotEqual(before, after)

    def test_deactivate_disables_login_eligibility(self):
        u = users_repo.create_user(self.conn, "e1", "太郎", "general", "password1")
        users_repo.deactivate_user(self.conn, u["id"])
        row = users_repo.get_user_by_employee_id(self.conn, "e1")
        self.assertFalse(row["is_active"])


if __name__ == "__main__":
    unittest.main()
