import pytest
from pydantic import ValidationError

from app.schemas.reservation import ReservationCreateRequest, ReservationUpdateRequest


def test_reservation_create_request_valid():
    req = ReservationCreateRequest(
        room_id=1,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="定例MTG",
    )
    assert req.title == "定例MTG"
    assert req.participant_ids == []


def test_reservation_create_request_rejects_title_over_100_chars():
    with pytest.raises(ValidationError):
        ReservationCreateRequest(
            room_id=1,
            date="2026-08-12",
            start_time="10:00",
            end_time="11:00",
            title="a" * 101,
        )


def test_reservation_create_request_rejects_empty_title():
    with pytest.raises(ValidationError):
        ReservationCreateRequest(
            room_id=1,
            date="2026-08-12",
            start_time="10:00",
            end_time="11:00",
            title="",
        )


def test_reservation_update_request_valid():
    req = ReservationUpdateRequest(
        room_id=1,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="更新後の件名",
    )
    assert req.title == "更新後の件名"


# ※CR-001により追加。internal_memoは300文字以内(docs/P901-cr-direction/CR-001.md)。


def test_reservation_create_request_accepts_internal_memo():
    req = ReservationCreateRequest(
        room_id=1,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="定例MTG",
        internal_memo="社内向けの非公開メモ",
    )
    assert req.internal_memo == "社内向けの非公開メモ"


def test_reservation_create_request_internal_memo_defaults_to_none():
    req = ReservationCreateRequest(
        room_id=1,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="定例MTG",
    )
    assert req.internal_memo is None


def test_reservation_create_request_accepts_internal_memo_at_300_chars():
    req = ReservationCreateRequest(
        room_id=1,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="定例MTG",
        internal_memo="あ" * 300,
    )
    assert len(req.internal_memo) == 300


def test_reservation_create_request_rejects_internal_memo_over_300_chars():
    with pytest.raises(ValidationError):
        ReservationCreateRequest(
            room_id=1,
            date="2026-08-12",
            start_time="10:00",
            end_time="11:00",
            title="定例MTG",
            internal_memo="あ" * 301,
        )


def test_reservation_update_request_accepts_internal_memo():
    req = ReservationUpdateRequest(
        room_id=1,
        date="2026-08-12",
        start_time="10:00",
        end_time="11:00",
        title="更新後の件名",
        internal_memo="更新後の非公開メモ",
    )
    assert req.internal_memo == "更新後の非公開メモ"


def test_reservation_update_request_rejects_internal_memo_over_300_chars():
    with pytest.raises(ValidationError):
        ReservationUpdateRequest(
            room_id=1,
            date="2026-08-12",
            start_time="10:00",
            end_time="11:00",
            title="更新後の件名",
            internal_memo="い" * 301,
        )
