import unittest

from app.repositories import room_repository
from tests.helpers import make_test_conn


class RoomRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.conn = make_test_conn()

    def tearDown(self):
        self.conn.close()

    def test_insert_and_find(self):
        room = room_repository.insert(self.conn, "会議室A", 6, "プロジェクタ", True)
        found = room_repository.find(self.conn, room["id"])
        self.assertEqual(found["name"], "会議室A")
        self.assertEqual(found["capacity"], 6)

    def test_find_nonexistent_returns_none(self):
        self.assertIsNone(room_repository.find(self.conn, 99999))

    def test_update_nonexistent_returns_none(self):
        result = room_repository.update(self.conn, 99999, "X", 1, "", True)
        self.assertIsNone(result)

    def test_list_excludes_inactive_by_default(self):
        room_repository.insert(self.conn, "会議室A", 6, "", True)
        inactive = room_repository.insert(self.conn, "会議室B", 4, "", True)
        room_repository.set_active(self.conn, inactive["id"], False)
        rooms = room_repository.list(self.conn, include_inactive=False)
        self.assertEqual(len(rooms), 1)
        self.assertEqual(rooms[0]["name"], "会議室A")

    def test_list_includes_inactive_when_requested(self):
        room_repository.insert(self.conn, "会議室A", 6, "", True)
        inactive = room_repository.insert(self.conn, "会議室B", 4, "", True)
        room_repository.set_active(self.conn, inactive["id"], False)
        rooms = room_repository.list(self.conn, include_inactive=True)
        self.assertEqual(len(rooms), 2)

    def test_find_by_name_active_ignores_inactive(self):
        room = room_repository.insert(self.conn, "会議室A", 6, "", True)
        room_repository.set_active(self.conn, room["id"], False)
        self.assertIsNone(room_repository.find_by_name_active(self.conn, "会議室A"))

    def test_set_active_updates_flag(self):
        room = room_repository.insert(self.conn, "会議室A", 6, "", True)
        updated = room_repository.set_active(self.conn, room["id"], False)
        self.assertFalse(bool(updated["is_active"]))


if __name__ == "__main__":
    unittest.main()
