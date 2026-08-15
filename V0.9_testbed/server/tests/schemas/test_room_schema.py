import pytest
from pydantic import ValidationError

from app.schemas.room import RoomCreateRequest


def test_room_create_request_valid():
    req = RoomCreateRequest(name="会議室A", capacity=10)
    assert req.is_active is True
    assert req.equipment == []


def test_room_create_request_rejects_capacity_zero():
    with pytest.raises(ValidationError):
        RoomCreateRequest(name="会議室A", capacity=0)


def test_room_create_request_rejects_name_over_50_chars():
    with pytest.raises(ValidationError):
        RoomCreateRequest(name="a" * 51, capacity=10)
