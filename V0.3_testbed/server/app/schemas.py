"""Pydanticスキーマ定義。docs/02-frontend-spec.md 2章の外部仕様に対応。"""
from typing import List, Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    employee_id: str
    password: str


class RoomCreateRequest(BaseModel):
    name: str
    capacity: int
    equipment: Optional[str] = None


class RoomUpdateRequest(BaseModel):
    name: str
    capacity: int
    equipment: Optional[str] = None
    is_active: bool = True


class ReservationWriteRequest(BaseModel):
    room_id: int
    date: str
    start_time: str
    end_time: str
    subject: str
    notes: Optional[str] = None
    participant_ids: List[int] = []


class UserCreateRequest(BaseModel):
    employee_id: str
    name: str
    role: str
    password: str


class UserUpdateRequest(BaseModel):
    name: str
    role: str
    is_active: bool = True
    password: Optional[str] = None
