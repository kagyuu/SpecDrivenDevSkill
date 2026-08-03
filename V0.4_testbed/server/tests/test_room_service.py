import unittest

from app.core.exceptions import NotFoundError, ValidationError
from app.services import room_service
from tests.helpers import make_test_conn


class RoomServiceTest(unittest.TestCase):
    def setUp(self):
        self.conn = make_test_conn()

    def tearDown(self):
        self.conn.close()

    def test_create_success(self):
        room = room_service.create(self.conn, {"name": "会議室A", "capacity": 6,
                                                "equipment": ["プロジェクタ"], "is_active": True})
        self.assertEqual(room["name"], "会議室A")

    def test_create_duplicate_name_raises_validation_error(self):
        room_service.create(self.conn, {"name": "会議室A", "capacity": 6, "equipment": [], "is_active": True})
        with self.assertRaises(ValidationError):
            room_service.create(self.conn, {"name": "会議室A", "capacity": 4, "equipment": [], "is_active": True})

    def test_create_invalid_capacity_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            room_service.create(self.conn, {"name": "会議室B", "capacity": 0, "equipment": [], "is_active": True})

    def test_deactivate_success(self):
        room = room_service.create(self.conn, {"name": "会議室A", "capacity": 6, "equipment": [], "is_active": True})
        result = room_service.deactivate(self.conn, room["id"])
        self.assertFalse(bool(result["is_active"]))

    def test_deactivate_nonexistent_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            room_service.deactivate(self.conn, 99999)


if __name__ == "__main__":
    unittest.main()
