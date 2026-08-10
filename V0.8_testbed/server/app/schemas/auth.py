"""Pydantic request/response models for app/routers/auth.py (U001-T4,
docs/P007-impl-direction/U001-foundation-and-auth.md).

Field/response shapes match docs/P002-frontend-spec.md 4.1〜4.3節 exactly.
Note the external field name is "employee_id", not the DB column name
"user_id" (app/repositories/user_repository.py's UserRow keeps "user_id" as
its key) - the rename happens in app/routers/auth.py's response construction.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    employee_id: str
    password: str

    @field_validator("employee_id")
    @classmethod
    def _employee_id_not_blank(cls, value: str) -> str:
        # docs/P002-frontend-spec.md 3.1節: 「社員IDを入力してください」(未入力時)
        if not value.strip():
            raise ValueError("社員IDを入力してください")
        return value

    @field_validator("password")
    @classmethod
    def _password_not_blank(cls, value: str) -> str:
        # docs/P002-frontend-spec.md 3.1節: 「パスワードを入力してください」(未入力時)
        if not value:
            raise ValueError("パスワードを入力してください")
        return value


class LoginResponse(BaseModel):
    employee_id: str
    name: str
    role: Literal["general", "admin"]


class MeResponse(BaseModel):
    employee_id: str
    name: str
    role: Literal["general", "admin"]
