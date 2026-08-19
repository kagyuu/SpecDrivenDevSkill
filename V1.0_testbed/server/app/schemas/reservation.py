from pydantic import BaseModel, Field


class ReservationCreateRequest(BaseModel):
    room_id: int
    date: str
    start_time: str
    end_time: str
    title: str = Field(min_length=1, max_length=100)
    participant_ids: list[int] = Field(default_factory=list)
    expected_attendees: int | None = Field(default=None, ge=1)
    notes: str | None = Field(default=None, max_length=500)
    internal_memo: str | None = Field(default=None, max_length=300)  # ※CR-001により追加


class ReservationUpdateRequest(BaseModel):
    room_id: int
    date: str
    start_time: str
    end_time: str
    title: str = Field(min_length=1, max_length=100)
    participant_ids: list[int] = Field(default_factory=list)
    expected_attendees: int | None = Field(default=None, ge=1)
    notes: str | None = Field(default=None, max_length=500)
    internal_memo: str | None = Field(default=None, max_length=300)  # ※CR-001により追加


class ReservationResponse(BaseModel):
    id: int
    room_id: int
    room_name: str
    user_id: int
    user_name: str
    date: str
    start_time: str
    end_time: str
    title: str
    participant_ids: list[int]
    expected_attendees: int | None
    notes: str | None
    internal_memo: str | None  # ※CR-001により追加。所有者・管理者以外にはRouter層でnullにマスキングされる
