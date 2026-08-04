"""予約関連のPydanticモデル (docs/P002-frontend-spec.md §4.8, §4.11)."""
from __future__ import annotations

from pydantic import BaseModel


class ReservationCreateRequest(BaseModel):
    room_id: int
    date: str
    start_time: str
    end_time: str
    title: str
    participant_ids: list[int] = []
    notes: str | None = None
    attendee_count: int | None = None  # CR-003: 参加予定人数(任意)


class CreatedByRef(BaseModel):
    id: int
    name: str


class ReservationListItem(BaseModel):
    id: int
    room_id: int
    date: str
    start_time: str
    end_time: str
    title: str
    created_by: CreatedByRef
