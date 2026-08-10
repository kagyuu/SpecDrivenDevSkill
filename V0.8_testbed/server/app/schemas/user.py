"""Pydantic request/response models for the admin-only /api/users CRUD
(U005-T2, docs/P007-impl-direction/U005-user-management-and-hardening.md).

Shapes match docs/P002-frontend-spec.md 4.10〜4.11.2節. UserResponse
deliberately has no password_hash field - that omission is what keeps the
hash out of API responses (this task's own 実装内容: "レスポンスは
password_hashを含めない...UserResponseにpassword_hashフィールドを含めないこと
で担保する").

Distinct from app/schemas/reservation.py's directory-lookup path
(GET /api/users/directory, U003-T3) which returns only
{employee_id, name} - see app/routers/users.py's own module docstring for
why the two endpoints/authorization levels are kept clearly separate.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class UserCreateRequest(BaseModel):
    employee_id: str
    name: str
    password: str
    role: Literal["general", "admin"] = "general"

    @field_validator("employee_id")
    @classmethod
    def _employee_id_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("社員IDを入力してください")
        return value

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("氏名を入力してください")
        return value


class UserUpdateRequest(BaseModel):
    name: str
    password: str | None = None
    role: Literal["general", "admin"]
    is_active: bool

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("氏名を入力してください")
        return value


class UserResponse(BaseModel):
    employee_id: str
    name: str
    role: Literal["general", "admin"]
    is_active: bool
