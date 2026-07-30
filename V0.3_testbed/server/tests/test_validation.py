import unittest

from app.validation import time_ranges_overlap, validate_reservation_input


class TestValidation(unittest.TestCase):
    def test_overlap_true(self):
        self.assertTrue(time_ranges_overlap("10:00", "11:00", "10:30", "11:30"))

    def test_overlap_false_no_overlap(self):
        self.assertFalse(time_ranges_overlap("10:00", "11:00", "12:00", "13:00"))

    def test_adjacent_not_overlap(self):
        # 隣接(終了=開始)は重複としない
        self.assertFalse(time_ranges_overlap("10:00", "11:00", "11:00", "12:00"))

    def test_valid_payload_no_errors(self):
        errors = validate_reservation_input(
            {"date": "2026-08-01", "start_time": "10:00", "end_time": "11:00", "subject": "定例MTG"}
        )
        self.assertEqual(errors, [])

    def test_missing_subject(self):
        errors = validate_reservation_input(
            {"date": "2026-08-01", "start_time": "10:00", "end_time": "11:00", "subject": ""}
        )
        self.assertTrue(any("subject" in e for e in errors))

    def test_end_before_start(self):
        errors = validate_reservation_input(
            {"date": "2026-08-01", "start_time": "11:00", "end_time": "10:00", "subject": "x"}
        )
        self.assertTrue(any("end_time" in e for e in errors))

    def test_subject_too_long(self):
        errors = validate_reservation_input(
            {"date": "2026-08-01", "start_time": "10:00", "end_time": "11:00", "subject": "a" * 101}
        )
        self.assertTrue(any("100文字" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
