import unittest
from datetime import date, timedelta

from app.core.exceptions import OverlapError
from app.repositories import reservation_repository
from tests.helpers import make_test_conn, seed_room, seed_user

TOMORROW = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
DAY_AFTER = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")


class ReservationRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.conn = make_test_conn()
        self.room_id = seed_room(self.conn, "会議室A")
        self.user_id = seed_user(self.conn, "E0001", "Passw0rd1")
        self.other_user_id = seed_user(self.conn, "E0002", "Passw0rd2")

    def tearDown(self):
        self.conn.close()

    def _base_data(self, start="10:00", end="11:00", date_str=TOMORROW):
        return {
            "room_id": self.room_id, "date": date_str, "start_time": start, "end_time": end,
            "title": "定例MTG", "notes": None, "participant_ids": [],
        }

    def test_insert_and_list_by_range(self):
        reservation_repository.insert_with_participants(self.conn, self._base_data(), self.user_id)
        rows = reservation_repository.list_by_range(self.conn, TOMORROW, TOMORROW)
        self.assertEqual(len(rows), 1)

    def test_list_by_range_excludes_out_of_range(self):
        reservation_repository.insert_with_participants(self.conn, self._base_data(), self.user_id)
        rows = reservation_repository.list_by_range(self.conn, DAY_AFTER, DAY_AFTER)
        self.assertEqual(len(rows), 0)

    def test_has_overlap_true_for_fully_overlapping(self):
        reservation_repository.insert_with_participants(self.conn, self._base_data(), self.user_id)
        self.assertTrue(reservation_repository.has_overlap(self.conn, self.room_id, TOMORROW, "10:00", "11:00"))

    def test_has_overlap_true_for_partial_overlap(self):
        reservation_repository.insert_with_participants(self.conn, self._base_data(), self.user_id)
        self.assertTrue(reservation_repository.has_overlap(self.conn, self.room_id, TOMORROW, "10:30", "11:30"))

    def test_has_overlap_false_for_adjacent_boundary(self):
        reservation_repository.insert_with_participants(self.conn, self._base_data(), self.user_id)
        self.assertFalse(reservation_repository.has_overlap(self.conn, self.room_id, TOMORROW, "11:00", "12:00"))

    def test_insert_with_participants_raises_overlap_error(self):
        reservation_repository.insert_with_participants(self.conn, self._base_data(), self.user_id)
        with self.assertRaises(OverlapError):
            reservation_repository.insert_with_participants(
                self.conn, self._base_data(start="10:30", end="11:30"), self.user_id
            )

    def test_find_with_detail_includes_participants_and_creator(self):
        data = self._base_data()
        data["participant_ids"] = [self.other_user_id]
        reservation_id = reservation_repository.insert_with_participants(self.conn, data, self.user_id)
        detail = reservation_repository.find_with_detail(self.conn, reservation_id)
        self.assertEqual(detail["created_by"]["id"], self.user_id)
        self.assertEqual(len(detail["participants"]), 1)
        self.assertEqual(detail["participants"][0]["id"], self.other_user_id)

    def test_find_with_detail_returns_none_for_missing(self):
        self.assertIsNone(reservation_repository.find_with_detail(self.conn, 99999))

    def test_list_by_creator_upcoming_and_past(self):
        past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        reservation_repository.insert_with_participants(self.conn, self._base_data(), self.user_id)
        # 過去日はAPI経由では作れないためシード(直接INSERT)する
        self.conn.execute(
            "INSERT INTO RESERVATIONS (room_id, date, start_time, end_time, title, notes, created_by, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, '2020-01-01T00:00:00Z', '2020-01-01T00:00:00Z')",
            (self.room_id, past_date, "09:00", "09:30", "過去MTG", None, self.user_id),
        )
        upcoming = reservation_repository.list_by_creator(self.conn, self.user_id, "upcoming")
        past = reservation_repository.list_by_creator(self.conn, self.user_id, "past")
        self.assertEqual(len(upcoming), 1)
        self.assertEqual(len(past), 1)
        self.assertEqual(past[0]["title"], "過去MTG")

    def test_update_with_participants_self_excluded_from_overlap(self):
        reservation_id = reservation_repository.insert_with_participants(self.conn, self._base_data(), self.user_id)
        updated_data = self._base_data()
        updated_data["title"] = "定例MTG(変更後)"
        reservation_repository.update_with_participants(self.conn, reservation_id, updated_data)
        detail = reservation_repository.find_with_detail(self.conn, reservation_id)
        self.assertEqual(detail["title"], "定例MTG(変更後)")

    def test_update_with_participants_raises_overlap_for_other_reservation(self):
        r1 = reservation_repository.insert_with_participants(self.conn, self._base_data("10:00", "11:00"), self.user_id)
        reservation_repository.insert_with_participants(self.conn, self._base_data("13:00", "14:00"), self.user_id)
        moved = self._base_data("13:00", "14:00")
        with self.assertRaises(OverlapError):
            reservation_repository.update_with_participants(self.conn, r1, moved)

    def test_delete_cascades_participants(self):
        data = self._base_data()
        data["participant_ids"] = [self.other_user_id]
        reservation_id = reservation_repository.insert_with_participants(self.conn, data, self.user_id)
        reservation_repository.delete(self.conn, reservation_id)
        self.assertIsNone(reservation_repository.find_with_detail(self.conn, reservation_id))
        remaining = self.conn.execute(
            "SELECT * FROM RESERVATION_PARTICIPANTS WHERE reservation_id = ?", (reservation_id,)
        ).fetchall()
        self.assertEqual(len(remaining), 0)


    # --- CR-003(U007-1): attendee_count の永続化・読み出し ---

    def test_insert_persists_attendee_count(self):
        reservation_id = reservation_repository.insert_with_participants(
            self.conn, self._base_data() | {"attendee_count": 7}, self.user_id)
        detail = reservation_repository.find_with_detail(self.conn, reservation_id)
        self.assertEqual(detail["attendee_count"], 7)

    def test_insert_without_attendee_count_stores_none(self):
        reservation_id = reservation_repository.insert_with_participants(
            self.conn, self._base_data(), self.user_id)
        detail = reservation_repository.find_with_detail(self.conn, reservation_id)
        self.assertIsNone(detail["attendee_count"])

    def test_update_persists_attendee_count(self):
        reservation_id = reservation_repository.insert_with_participants(
            self.conn, self._base_data() | {"attendee_count": 3}, self.user_id)
        reservation_repository.update_with_participants(
            self.conn, reservation_id, self._base_data() | {"attendee_count": 9})
        detail = reservation_repository.find_with_detail(self.conn, reservation_id)
        self.assertEqual(detail["attendee_count"], 9)


if __name__ == "__main__":
    unittest.main()
