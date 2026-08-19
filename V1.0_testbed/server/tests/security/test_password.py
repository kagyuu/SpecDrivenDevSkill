from app.security.password import hash_password, verify_password


def test_verify_password_true_for_matching_raw():
    raw = "TestPassw0rd!"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed) is True


def test_verify_password_false_for_different_raw():
    hashed = hash_password("TestPassw0rd!")
    assert verify_password("WrongPassword1", hashed) is False


def test_hash_password_is_randomized():
    raw = "TestPassw0rd!"
    assert hash_password(raw) != hash_password(raw)
