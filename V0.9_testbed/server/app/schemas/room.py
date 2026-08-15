from pydantic import BaseModel, Field


class RoomResponse(BaseModel):
    id: int
    name: str
    capacity: int
    equipment: list[str]
    description: str | None
    is_active: bool


class RoomCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    capacity: int = Field(ge=1)
    equipment: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=200)
    is_active: bool = True


class RoomUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    capacity: int = Field(ge=1)
    equipment: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=200)
    is_active: bool = True
