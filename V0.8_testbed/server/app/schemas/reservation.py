"""Pydantic request/response models for app/routers/reservations.py (U003-T3,
docs/P007-impl-direction/U003-reservation-core-and-calendar.md).

Shapes match docs/P002-frontend-spec.md 4.6〜4.9節.

★実施メモ: `ReservationDetailResponse` is defined here already, one sprint
earlier than U004-T2's own file list says ("server/app/schemas/reservation.py
(ReservationDetailResponse, ReservationUpdateRequest,
MyReservationListItemResponseを追加)") - docs/P002-frontend-spec.md 4.7節
requires POST /api/reservations (this task) to return "作成された予約の詳細
(4.9節と同形式)", so the detail shape is needed now, not just from U004. When
U004-T2 is implemented, this class already exists and is reused as-is; only
ReservationUpdateRequest and MyReservationListItemResponse are new there.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class ReservationCreateRequest(BaseModel):
    room_id: int
    date: str
    start_time: str
    end_time: str
    title: str
    participant_user_ids: list[str] = []
    attendee_count: int | None = None
    notes: str | None = None
    meeting_url: str | None = None
    """CR-001 (docs/P901-cr-direction/CR-001.md, U003-T7): optional online
    meeting URL. Format/length validation happens in
    app/services/reservation_service.py, not here - kept consistent with how
    title/notes/attendee_count are already validated at the Service layer
    rather than via Pydantic validators, so all reservation field validation
    lives in one place."""

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("件名を入力してください")
        return value


class ReservationListItemResponse(BaseModel):
    reservation_id: int
    room_id: int
    room_name: str
    organizer_user_id: str
    organizer_name: str
    title: str
    start_datetime: str
    end_datetime: str


class ReservationParticipant(BaseModel):
    employee_id: str
    name: str


class ReservationDetailResponse(BaseModel):
    reservation_id: int
    room_id: int
    room_name: str
    organizer_user_id: str
    organizer_name: str
    date: str
    start_time: str
    end_time: str
    title: str
    participants: list[ReservationParticipant]
    attendee_count: int | None
    notes: str | None
    meeting_url: str | None = None
    """CR-001 (U003-T7): null when not set. Deliberately NOT added to
    ReservationListItemResponse/MyReservationListItemResponse - docs/P002-frontend-spec.md
    4.6節 requires the calendar list response to keep excluding it."""
    editable: bool


class ReservationUpdateRequest(BaseModel):
    """U004-T2, docs/P007-impl-direction/U004-reservation-detail-and-mylist.md.
    Same shape as ReservationCreateRequest (docs/P002-frontend-spec.md 4.9.1節:
    "リクエストボディ: 4.7節と同形式")."""

    room_id: int
    date: str
    start_time: str
    end_time: str
    title: str
    participant_user_ids: list[str] = []
    attendee_count: int | None = None
    notes: str | None = None
    meeting_url: str | None = None
    """CR-001 (U004-T6)."""

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("件名を入力してください")
        return value


class MyReservationListItemResponse(BaseModel):
    reservation_id: int
    room_id: int
    room_name: str
    date: str
    start_time: str
    end_time: str
    title: str
