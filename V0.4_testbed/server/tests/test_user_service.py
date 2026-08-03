import unittest

from app.core.exceptions import NotFoundError, ValidationError
from app.services import user_service
from tests.helpers import make_test_conn


class UserServiceTest(unittest.TestCase):
    def setUp(self):
        self.conn = make_test_conn()

    def tearDown(self):
        self.conn.close()

    def test_create_success(self):
        user = user_service.create(self.conn, {
            "employee_id": "E0002", "name": "鈴木花子", "role": "general",
            "is_active": True, "initial_password": "Passw0rd2",
        })
        self.assertEqual(user["employee_id"], "E0002")

    def test_create_duplicate_employee_id_raises_validation_error(self):
        data = {"employee_id": "E0002", "name": "鈴木花子", "role": "general",
                "is_active": True, "initial_password": "Passw0rd2"}
        user_service.create(self.conn, data)
        with self.assertRaises(ValidationError):
            user_service.create(self.conn, {**data, "name": "重複太郎"})

    def test_create_weak_password_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            user_service.create(self.conn, {
                "employee_id": "E0003", "name": "テスト", "role": "general",
                "is_active": True, "initial_password": "weak",
            })

    def test_deactivate_self_raises_validation_error(self):
        admin = user_service.create(self.conn, {
            "employee_id": "A0001", "name": "管理者", "role": "admin",
            "is_active": True, "initial_password": "Passw0rd1",
        })
        with self.assertRaises(ValidationError):
            user_service.deactivate(self.conn, admin["id"], admin["id"])

    def test_deactivate_other_user_succeeds(self):
        admin = user_service.create(self.conn, {
            "employee_id": "A0001", "name": "管理者", "role": "admin",
            "is_active": True, "initial_password": "Passw0rd1",
        })
        target = user_service.create(self.conn, {
            "employee_id": "E0002", "name": "鈴木花子", "role": "general",
            "is_active": True, "initial_password": "Passw0rd2",
        })
        result = user_service.deactivate(self.conn, target["id"], admin["id"])
        self.assertFalse(bool(result["is_active"]))

    def test_deactivate_nonexistent_raises_not_found(self):
        admin = user_service.create(self.conn, {
            "employee_id": "A0001", "name": "管理者", "role": "admin",
            "is_active": True, "initial_password": "Passw0rd1",
        })
        with self.assertRaises(NotFoundError):
            user_service.deactivate(self.conn, 99999, admin["id"])


if __name__ == "__main__":
    unittest.main()
