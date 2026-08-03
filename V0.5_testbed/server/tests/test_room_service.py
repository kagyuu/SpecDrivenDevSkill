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

    # --- CR-002: 会議室説明文(description) ---

    def test_create_persists_description(self):
        room = room_service.create(self.conn, {"name": "会議室A", "capacity": 6, "equipment": [],
                                                "is_active": True, "description": "役員会議専用の個室です。"})
        self.assertEqual(room["description"], "役員会議専用の個室です。")

    def test_create_without_description_is_none(self):
        room = room_service.create(self.conn, {"name": "会議室A", "capacity": 6, "equipment": [],
                                                "is_active": True})
        self.assertIsNone(room["description"])

    def test_create_too_long_description_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            room_service.create(self.conn, {"name": "会議室A", "capacity": 6, "equipment": [],
                                             "is_active": True, "description": "A" * 201})

    # 注記: room_service.update() が description をどう扱うか(更新後に反映されるか)の結合的な
    # 確認は、本ファイル(単体テスト)ではなくAPI結合テスト T022/T023
    # (server/tests/test_api_rooms.py, docs/P008-test-direction/T022-*.md, T023-*.md)で行う。


if __name__ == "__main__":
    unittest.main()
