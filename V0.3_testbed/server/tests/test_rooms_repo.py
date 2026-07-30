import unittest

from app.db import get_connection
from app.repositories import rooms as rooms_repo


class TestRoomsRepo(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")

    def test_create_and_list(self):
        rooms_repo.create_room(self.conn, "会議室X", 4, "プロジェクタ")
        rooms = rooms_repo.list_rooms(self.conn)
        self.assertEqual(len(rooms), 1)
        self.assertEqual(rooms[0]["name"], "会議室X")

    def test_name_duplicate_detected(self):
        rooms_repo.create_room(self.conn, "会議室X", 4, None)
        self.assertTrue(rooms_repo.name_exists(self.conn, "会議室X"))

    def test_deactivate_hides_from_default_list(self):
        room = rooms_repo.create_room(self.conn, "会議室X", 4, None)
        rooms_repo.deactivate_room(self.conn, room["id"])
        self.assertEqual(rooms_repo.list_rooms(self.conn), [])

    def test_include_inactive_shows_deleted(self):
        room = rooms_repo.create_room(self.conn, "会議室X", 4, None)
        rooms_repo.deactivate_room(self.conn, room["id"])
        rooms = rooms_repo.list_rooms(self.conn, include_inactive=True)
        self.assertEqual(len(rooms), 1)
        self.assertFalse(rooms[0]["is_active"])


if __name__ == "__main__":
    unittest.main()
