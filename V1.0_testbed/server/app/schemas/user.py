from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    employee_id: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=50)
    role: str = Field(pattern="^(general|admin)$")
    is_active: bool = True
    initial_password: str = Field(min_length=8)


class UserUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    role: str = Field(pattern="^(general|admin)$")
    is_active: bool = True


class UserResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    role: str
    is_active: bool
