from pydantic import BaseModel


class LoginRequest(BaseModel):
    employee_id: str
    password: str


class MeResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    role: str
