import unittest

from app.core.validators import (
    validate_employee_id,
    validate_password_policy,
    validate_room_name,
    validate_capacity,
    validate_room_description,
    validate_user_name,
    validate_role,
    validate_time_range,
    validate_title,
    validate_notes,
)


class EmployeeIdValidatorTest(unittest.TestCase):
    def test_valid_employee_id(self):
        self.assertTrue(validate_employee_id("E0001"))
        self.assertTrue(validate_employee_id("A" * 20))

    def test_too_long_employee_id_rejected(self):
        self.assertFalse(validate_employee_id("A" * 21))

    def test_symbol_in_employee_id_rejected(self):
        self.assertFalse(validate_employee_id("E-0001"))


class PasswordPolicyValidatorTest(unittest.TestCase):
    def test_valid_password(self):
        self.assertTrue(validate_password_policy("Passw0rd"))

    def test_too_short_password_rejected(self):
        self.assertFalse(validate_password_policy("Pw0rd12"))  # 7 chars

    def test_digits_only_password_rejected(self):
        self.assertFalse(validate_password_policy("12345678"))

    def test_alpha_only_password_rejected(self):
        self.assertFalse(validate_password_policy("abcdefgh"))


class RoomAndUserValidatorTest(unittest.TestCase):
    def test_room_name_valid(self):
        self.assertTrue(validate_room_name("会議室A"))

    def test_room_name_too_long_rejected(self):
        self.assertFalse(validate_room_name("A" * 51))

    def test_capacity_valid(self):
        self.assertTrue(validate_capacity(1))
        self.assertTrue(validate_capacity(6))

    def test_capacity_zero_or_negative_rejected(self):
        self.assertFalse(validate_capacity(0))
        self.assertFalse(validate_capacity(-1))

    def test_user_name_valid(self):
        self.assertTrue(validate_user_name("山田太郎"))

    def test_user_name_too_long_rejected(self):
        self.assertFalse(validate_user_name("A" * 51))

    def test_role_valid(self):
        self.assertTrue(validate_role("general"))
        self.assertTrue(validate_role("admin"))

    def test_role_invalid_rejected(self):
        self.assertFalse(validate_role("manager"))

    # --- CR-002: 会議室説明文(description) ---

    def test_room_description_none_allowed(self):
        self.assertTrue(validate_room_description(None))

    def test_room_description_empty_string_allowed(self):
        self.assertTrue(validate_room_description(""))

    def test_room_description_valid(self):
        self.assertTrue(validate_room_description("役員会議専用の個室です。"))
        self.assertTrue(validate_room_description("A" * 200))

    def test_room_description_too_long_rejected(self):
        self.assertFalse(validate_room_description("A" * 201))


class ReservationValidatorTest(unittest.TestCase):
    def test_time_range_valid(self):
        self.assertTrue(validate_time_range("10:00", "11:00"))

    def test_time_range_equal_rejected(self):
        self.assertFalse(validate_time_range("10:00", "10:00"))

    def test_time_range_reversed_rejected(self):
        self.assertFalse(validate_time_range("11:00", "10:00"))

    def test_title_valid(self):
        self.assertTrue(validate_title("定例MTG"))

    def test_title_too_long_rejected(self):
        self.assertFalse(validate_title("A" * 101))

    def test_notes_none_allowed(self):
        self.assertTrue(validate_notes(None))

    def test_notes_too_long_rejected(self):
        self.assertFalse(validate_notes("A" * 501))


if __name__ == "__main__":
    unittest.main()
