import unittest

from app.core.password import hash_password, verify_password


class PasswordTest(unittest.TestCase):
    def test_verify_password_true_for_correct_password(self):
        hashed = hash_password("Passw0rd1")
        self.assertTrue(verify_password("Passw0rd1", hashed))

    def test_verify_password_false_for_wrong_password(self):
        hashed = hash_password("Passw0rd1")
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_hash_does_not_contain_plaintext(self):
        hashed = hash_password("Passw0rd1")
        self.assertNotIn("Passw0rd1", hashed)


if __name__ == "__main__":
    unittest.main()
