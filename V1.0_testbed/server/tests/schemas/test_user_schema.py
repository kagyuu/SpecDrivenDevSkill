import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreateRequest


def test_user_create_request_valid():
    req = UserCreateRequest(employee_id="user003", name="新人太郎", role="general", initial_password="Passw0rd1")
    assert req.is_active is True


def test_user_create_request_rejects_short_password():
    with pytest.raises(ValidationError):
        UserCreateRequest(employee_id="user003", name="新人太郎", role="general", initial_password="short")


def test_user_create_request_rejects_invalid_role():
    with pytest.raises(ValidationError):
        UserCreateRequest(employee_id="user003", name="新人太郎", role="owner", initial_password="Passw0rd1")
