"""Unit tests for U001-T3 (docs/P007-impl-direction/U001-foundation-and-auth.md).

Target: app/security/password.py hash_password() / verify_password()
"""

from __future__ import annotations

from app.security.password import hash_password, verify_password


def test_verify_password_true_for_correct_password():
    hashed = hash_password("correct-horse-battery-staple")

    assert verify_password("correct-horse-battery-staple", hashed) is True


def test_verify_password_false_for_incorrect_password():
    hashed = hash_password("correct-horse-battery-staple")

    assert verify_password("wrong-password", hashed) is False


def test_hash_password_uses_random_salt_each_time():
    # Two hashes of the same plaintext must differ (random salt), and both
    # must still verify against that same plaintext.
    first = hash_password("ChangeMe123!")
    second = hash_password("ChangeMe123!")

    assert first != second
    assert verify_password("ChangeMe123!", first) is True
    assert verify_password("ChangeMe123!", second) is True


def test_verify_password_false_for_malformed_hash():
    # Defensive case, not in the task's own Unit Test list but cheap to add:
    # a corrupted/foreign password_hash value must not raise, just fail closed.
    assert verify_password("anything", "not-a-valid-hash") is False
