from app.validation.auth import validate_login_input


def test_validate_login_input_both_missing():
    errors = validate_login_input("", "")
    assert errors == ["社員IDを入力してください", "パスワードを入力してください"]


def test_validate_login_input_valid():
    errors = validate_login_input("user001", "TestPassw0rd!")
    assert errors == []
