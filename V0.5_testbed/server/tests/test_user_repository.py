import unittest

from app.core.password import hash_password
from app.repositories import user_repository
from tests.helpers import make_test_conn


class UserRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.conn = make_test_conn()

    def tearDown(self):
        self.conn.close()

    def test_insert_and_find_by_id(self):
        user = user_repository.insert(self.conn, "E0001", "山田太郎", hash_password("Passw0rd1"), "general", True)
        found = user_repository.find_by_id(self.conn, user["id"])
        self.assertEqual(found["employee_id"], "E0001")

    def test_find_by_employee_id(self):
        user_repository.insert(self.conn, "E0001", "山田太郎", hash_password("Passw0rd1"), "general", True)
        found = user_repository.find_by_employee_id(self.conn, "E0001")
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "山田太郎")

    def test_find_by_id_nonexistent_returns_none(self):
        self.assertIsNone(user_repository.find_by_id(self.conn, 99999))

    def test_update_nonexistent_returns_none(self):
        result = user_repository.update(self.conn, 99999, "X", "general", True)
        self.assertIsNone(result)

    def test_list_defaults_to_include_inactive(self):
        u1 = user_repository.insert(self.conn, "E0001", "山田太郎", hash_password("Passw0rd1"), "general", True)
        u2 = user_repository.insert(self.conn, "E0099", "無効", hash_password("Passw0rd1"), "general", True)
        user_repository.set_active(self.conn, u2["id"], False)
        users = user_repository.list(self.conn)
        self.assertEqual(len(users), 2)

    def test_list_can_exclude_inactive(self):
        u1 = user_repository.insert(self.conn, "E0001", "山田太郎", hash_password("Passw0rd1"), "general", True)
        u2 = user_repository.insert(self.conn, "E0099", "無効", hash_password("Passw0rd1"), "general", True)
        user_repository.set_active(self.conn, u2["id"], False)
        users = user_repository.list(self.conn, include_inactive=False)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["employee_id"], "E0001")

    def test_set_active_updates_flag(self):
        user = user_repository.insert(self.conn, "E0001", "山田太郎", hash_password("Passw0rd1"), "general", True)
        updated = user_repository.set_active(self.conn, user["id"], False)
        self.assertFalse(bool(updated["is_active"]))

    def test_update_changes_password_when_provided(self):
        user = user_repository.insert(self.conn, "E0001", "山田太郎", hash_password("Passw0rd1"), "general", True)
        new_hash = hash_password("NewPassw0rd")
        updated = user_repository.update(self.conn, user["id"], "山田太郎", "general", True, new_hash)
        self.assertEqual(updated["password_hash"], new_hash)


if __name__ == "__main__":
    unittest.main()
