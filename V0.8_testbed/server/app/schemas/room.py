"""Pydantic request/response models for app/routers/rooms.py (U002-T2,
docs/P007-impl-direction/U002-room-management.md).

Shapes match docs/P002-frontend-spec.md 4.4〜4.5.2節 exactly.
"""

from __future__ import annotations

from pydantic import BaseModel


class RoomCreateRequest(BaseModel):
    name: str
    capacity: int
    equipment: list[str] = []
    description: str | None = None


class RoomUpdateRequest(BaseModel):
    name: str
    capacity: int
    equipment: list[str] = []
    description: str | None = None
    is_active: bool


class RoomResponse(BaseModel):
    room_id: int
    name: str
    capacity: int
    equipment: list[str]
    description: str | None
    is_active: bool
