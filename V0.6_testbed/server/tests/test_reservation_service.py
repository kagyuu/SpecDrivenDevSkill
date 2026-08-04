import unittest
from datetime import date, timedelta

from app.core.exceptions import ForbiddenError, NotFoundError, OverlapError, ValidationError
from app.services import reservation_service
from tests.helpers import make_test_conn, seed_room, seed_user

TOMORROW = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
YESTERDAY = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")


def _user_row(conn, user_id):
    from app.repositories import user_repository
    return user_repository.find_by_id(conn, user_id)


class ReservationServiceCreateTest(unittest.TestCase):
    def setUp(self):
        self.conn = make_test_conn()
        self.room_id = seed_room(self.conn)
        self.user_id = seed_user(self.conn, "E0001", "Passw0rd1")
        self.user = _user_row(self.conn, self.user_id)

    def tearDown(self):
        self.conn.close()

    def _data(self, **overrides):
        base = {
            "room_id": self.room_id, "date": TOMORROW, "start_time": "10:00", "end_time": "11:00",
            "title": "定例MTG", "notes": None, "participant_ids": [],
        }
        base.update(overrides)
        return base

    def test_create_success(self):
        result = reservation_service.create(self.conn, self._data(), self.user)
        self.assertEqual(result["title"], "定例MTG")

    def test_create_room_not_found_raises(self):
        with self.assertRaises(NotFoundError):
            reservation_service.create(self.conn, self._data(room_id=99999), self.user)

    def test_create_inactive_room_raises_validation_error(self):
        from app.repositories import room_repository
        room_repository.set_active(self.conn, self.room_id, False)
        with self.assertRaises(ValidationError):
            reservation_service.create(self.conn, self._data(), self.user)

    def test_create_unknown_participant_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            reservation_service.create(self.conn, self._data(participant_ids=[99999]), self.user)

    def test_create_overlap_raises_overlap_error(self):
        reservation_service.create(self.conn, self._data(), self.user)
        with self.assertRaises(OverlapError):
            reservation_service.create(self.conn, self._data(start_time="10:30", end_time="11:30"), self.user)

    def test_create_past_date_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            reservation_service.create(self.conn, self._data(date=YESTERDAY), self.user)

    # --- CR-003(U007-1): 参加予定人数と会議室の収容人数 ---

    def test_create_with_attendee_count_within_capacity_succeeds(self):
        # seed_room の既定 capacity は 6
        result = reservation_service.create(self.conn, self._data(attendee_count=5), self.user)
        self.assertEqual(result["attendee_count"], 5)

    def test_create_with_attendee_count_equal_to_capacity_succeeds(self):
        result = reservation_service.create(self.conn, self._data(attendee_count=6), self.user)
        self.assertEqual(result["attendee_count"], 6)

    def test_create_with_attendee_count_exceeding_capacity_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            reservation_service.create(self.conn, self._data(attendee_count=7), self.user)
        self.assertIn("attendee_count", [d.get("field") for d in ctx.exception.details])

    def test_create_with_invalid_attendee_count_raises(self):
        with self.assertRaises(ValidationError):
            reservation_service.create(self.conn, self._data(attendee_count=0), self.user)

    def test_create_without_attendee_count_succeeds(self):
        result = reservation_service.create(self.conn, self._data(), self.user)
        self.assertIsNone(result["attendee_count"])


class ReservationServiceEditTest(unittest.TestCase):
    def setUp(self):
        self.conn = make_test_conn()
        self.room_id = seed_room(self.conn)
        self.owner_id = seed_user(self.conn, "E0001", "Passw0rd1")
        self.other_id = seed_user(self.conn, "E0002", "Passw0rd2")
        self.admin_id = seed_user(self.conn, "A0001", "Passw0rd1", role="admin")
        self.owner = _user_row(self.conn, self.owner_id)
        self.other = _user_row(self.conn, self.other_id)
        self.admin = _user_row(self.conn, self.admin_id)
        data = {
            "room_id": self.room_id, "date": TOMORROW, "start_time": "10:00", "end_time": "11:00",
            "title": "定例MTG", "notes": None, "participant_ids": [],
        }
        self.reservation = reservation_service.create(self.conn, data, self.owner)
        self.reservation_id = self.reservation["id"]

    def tearDown(self):
        self.conn.close()

    def _update_data(self, **overrides):
        base = {
            "room_id": self.room_id, "date": TOMORROW, "start_time": "10:00", "end_time": "11:00",
            "title": "定例MTG(変更後)", "notes": None, "participant_ids": [],
        }
        base.update(overrides)
        return base

    def test_owner_can_update(self):
        result = reservation_service.update(self.conn, self.reservation_id, self._update_data(), self.owner)
        self.assertEqual(result["title"], "定例MTG(変更後)")

    def test_admin_can_update(self):
        result = reservation_service.update(self.conn, self.reservation_id, self._update_data(), self.admin)
        self.assertEqual(result["title"], "定例MTG(変更後)")

    def test_other_user_cannot_update(self):
        with self.assertRaises(ForbiddenError):
            reservation_service.update(self.conn, self.reservation_id, self._update_data(), self.other)

    def test_other_user_cannot_delete(self):
        with self.assertRaises(ForbiddenError):
            reservation_service.delete(self.conn, self.reservation_id, self.other)

    def test_owner_can_delete(self):
        reservation_service.delete(self.conn, self.reservation_id, self.owner)
        with self.assertRaises(NotFoundError):
            reservation_service.get_detail(self.conn, self.reservation_id)

    def test_update_nonexistent_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            reservation_service.update(self.conn, 99999, self._update_data(), self.owner)

    def test_update_overlap_raises_overlap_error(self):
        other_data = {
            "room_id": self.room_id, "date": TOMORROW, "start_time": "13:00", "end_time": "14:00",
            "title": "別会議", "notes": None, "participant_ids": [],
        }
        reservation_service.create(self.conn, other_data, self.owner)
        with self.assertRaises(OverlapError):
            reservation_service.update(self.conn, self.reservation_id,
                                        self._update_data(start_time="13:00", end_time="14:00"), self.owner)

    def test_list_mine_returns_only_own_upcoming(self):
        mine = reservation_service.list_mine(self.conn, self.owner_id, "upcoming")
        self.assertEqual(len(mine), 1)

    def test_get_detail_returns_full_information(self):
        detail = reservation_service.get_detail(self.conn, self.reservation_id)
        self.assertEqual(detail["created_by"]["id"], self.owner_id)


    # --- CR-003(U007-1): 更新時の参加予定人数と収容人数 ---

    def test_update_persists_attendee_count(self):
        result = reservation_service.update(
            self.conn, self.reservation_id, self._update_data(attendee_count=4), self.owner)
        self.assertEqual(result["attendee_count"], 4)

    def test_update_with_attendee_count_exceeding_capacity_raises(self):
        with self.assertRaises(ValidationError) as ctx:
            reservation_service.update(
                self.conn, self.reservation_id, self._update_data(attendee_count=7), self.owner)
        self.assertIn("attendee_count", [d.get("field") for d in ctx.exception.details])

    def test_update_checks_capacity_of_the_new_room(self):
        """会議室を変更する更新では、変更後の会議室の収容人数で判定する。"""
        small_room_id = seed_room(self.conn, "小会議室", capacity=2)
        with self.assertRaises(ValidationError):
            reservation_service.update(
                self.conn, self.reservation_id,
                self._update_data(room_id=small_room_id, attendee_count=5), self.owner)
        # 変更後の会議室の収容人数以下なら成功する
        result = reservation_service.update(
            self.conn, self.reservation_id,
            self._update_data(room_id=small_room_id, attendee_count=2), self.owner)
        self.assertEqual(result["attendee_count"], 2)

    def test_update_omitting_attendee_count_clears_it(self):
        """全量更新のため、省略した場合は null で上書きされる(docs/P002-frontend-spec.md §4.12)。"""
        reservation_service.update(
            self.conn, self.reservation_id, self._update_data(attendee_count=3), self.owner)
        result = reservation_service.update(
            self.conn, self.reservation_id, self._update_data(), self.owner)
        self.assertIsNone(result["attendee_count"])


if __name__ == "__main__":
    unittest.main()
