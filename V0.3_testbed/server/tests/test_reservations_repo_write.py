import unittest

from app.db import get_connection
from app.repositories import reservations as res_repo
from app.repositories import rooms as rooms_repo
from app.repositories import users as users_repo


class TestReservationsRepoWrite(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        self.user = users_repo.create_user(self.conn, "u1", "太郎", "general", "password1")
        self.other = users_repo.create_user(self.conn, "u2", "花子", "general", "password2")
        self.room = rooms_repo.create_room(self.conn, "会議室A", 4, None)

    def test_create_reservation_success(self):
        r = res_repo.create_reservation(
            self.conn, self.room["id"], "2099-01-01", "10:00", "11:00", "MTG", None, self.user["id"], []
        )
        self.assertIsNotNone(r["id"])
        self.assertIn(self.user["id"], r["participant_ids"])

    def test_create_reservation_conflict_raises(self):
        res_repo.create_reservation(
            self.conn, self.room["id"], "2099-01-01", "10:00", "11:00", "MTG1", None, self.user["id"], []
        )
        with self.assertRaises(res_repo.ConflictError):
            res_repo.create_reservation(
                self.conn, self.room["id"], "2099-01-01", "10:30", "11:30", "MTG2", None, self.other["id"], []
            )

    def test_update_excludes_self_from_conflict_check(self):
        r = res_repo.create_reservation(
            self.conn, self.room["id"], "2099-01-01", "10:00", "11:00", "MTG", None, self.user["id"], []
        )
        updated = res_repo.update_reservation(
            self.conn, r["id"], self.room["id"], "2099-01-01", "10:15", "11:15", "MTG更新", None, self.user["id"], []
        )
        self.assertEqual(updated["subject"], "MTG更新")

    def test_delete_reservation_removes_from_list(self):
        r = res_repo.create_reservation(
            self.conn, self.room["id"], "2099-01-01", "10:00", "11:00", "MTG", None, self.user["id"], []
        )
        res_repo.delete_reservation(self.conn, r["id"])
        self.assertIsNone(res_repo.get_reservation(self.conn, r["id"]))

    def test_find_missing_participant_ids_detects_nonexistent(self):
        # F001相当: 存在しない参加者IDを検出できること(このチェックがないとFKエラーで500になる)。
        missing = res_repo.find_missing_participant_ids(self.conn, [999999])
        self.assertEqual(missing, [999999])

    def test_find_missing_participant_ids_detects_inactive(self):
        users_repo.deactivate_user(self.conn, self.other["id"])
        missing = res_repo.find_missing_participant_ids(self.conn, [self.other["id"]])
        self.assertEqual(missing, [self.other["id"]])

    def test_find_missing_participant_ids_empty_for_valid(self):
        missing = res_repo.find_missing_participant_ids(self.conn, [self.other["id"]])
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
