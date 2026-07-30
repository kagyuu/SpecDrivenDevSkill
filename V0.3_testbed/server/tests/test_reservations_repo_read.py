import unittest

from app.db import get_connection
from app.repositories import reservations as res_repo
from app.repositories import rooms as rooms_repo
from app.repositories import users as users_repo


class TestReservationsRepoRead(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        self.user = users_repo.create_user(self.conn, "u1", "太郎", "general", "password1")
        self.other = users_repo.create_user(self.conn, "u2", "花子", "general", "password2")
        self.room = rooms_repo.create_room(self.conn, "会議室A", 4, None)
        self.res_future = res_repo.create_reservation(
            self.conn, self.room["id"], "2099-01-01", "10:00", "11:00", "未来MTG", None, self.user["id"], []
        )
        self.res_past = res_repo.create_reservation(
            self.conn, self.room["id"], "2000-01-01", "10:00", "11:00", "過去MTG", None, self.user["id"], []
        )

    def test_list_reservations_by_date_range(self):
        results = res_repo.list_reservations(self.conn, "2099-01-01", "2099-01-31", None)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["subject"], "未来MTG")

    def test_list_reservations_room_filter(self):
        other_room = rooms_repo.create_room(self.conn, "会議室B", 4, None)
        results = res_repo.list_reservations(self.conn, "2000-01-01", "2099-12-31", other_room["id"])
        self.assertEqual(results, [])

    def test_list_mine_future(self):
        results = res_repo.list_mine(self.conn, self.user["id"], "future", "2050-01-01")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["subject"], "未来MTG")

    def test_list_mine_past(self):
        results = res_repo.list_mine(self.conn, self.user["id"], "past", "2050-01-01")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["subject"], "過去MTG")

    def test_get_reservation_includes_participants(self):
        detail = res_repo.get_reservation(self.conn, self.res_future["id"])
        self.assertIn(self.user["id"], detail["participant_ids"])

    def test_get_nonexistent_reservation_returns_none(self):
        self.assertIsNone(res_repo.get_reservation(self.conn, 999999))


if __name__ == "__main__":
    unittest.main()
