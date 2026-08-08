"""Pydantic v2 のリクエスト/レスポンスモデル(P003 4.2、ADR-002)。

* 制約値は `docs/P002-frontend-spec.md` 3章の表と1対1で一致させる。
* エラーメッセージはP002 3章の日本語文言を使う(Pydanticの既定英語メッセージを返さない)。
* FastAPIの自動バインドが無いため、ハンドラから `validate()` を明示的に呼ぶ。
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from pydantic_core import PydanticCustomError

from .errors import ApiError

USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{4,20}$")


def _fail(message: str) -> None:
    """P002の日本語文言をそのまま `msg` にする(既定の英語メッセージを使わない)。"""
    raise PydanticCustomError("invalid", message)  # noqa: TRY301


def _as_text(value: Any, required_message: str) -> str:
    if value is None:
        _fail(required_message)
    if not isinstance(value, str):
        value = str(value)
    return value


def validate(model: type[BaseModel], data: Any) -> BaseModel:
    """Pydanticの `ValidationError` を 400 `VALIDATION_ERROR` に変換する(P003 4.2)。"""
    if not isinstance(data, dict):
        raise ApiError(
            400,
            "VALIDATION_ERROR",
            "入力内容に誤りがあります。",
            details=[{"field": "body", "message": "リクエストの形式が正しくありません。"}],
        )
    try:
        return model(**data)
    except ValidationError as exc:
        details = [
            {
                "field": str(err["loc"][-1]) if err["loc"] else "body",
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        raise ApiError(400, "VALIDATION_ERROR", "入力内容に誤りがあります。", details=details) from exc


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore")


class LoginRequest(_Base):
    """API-01 のリクエスト(P002 3.1 / 5.4)。"""

    # 未入力(キー欠落)でも必須チェックを働かせるため既定値も検証する
    model_config = ConfigDict(extra="ignore", validate_default=True)

    user_id: Any = None
    password: Any = None

    @field_validator("user_id")
    @classmethod
    def _check_user_id(cls, value: Any) -> str:
        text = _as_text(value, "ユーザーIDを入力してください。")
        if text == "":
            _fail("ユーザーIDを入力してください。")
        if not USER_ID_PATTERN.match(text):
            _fail("ユーザーIDは半角英数字4〜20文字で入力してください。")
        return text

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: Any) -> str:
        text = _as_text(value, "パスワードを入力してください。")
        if text == "":
            _fail("パスワードを入力してください。")
        if not 8 <= len(text) <= 64:
            _fail("パスワードは8〜64文字で入力してください。")
        return text


class UserResponse(_Base):
    """API-01・API-03 が返すログイン中ユーザー(P002 5.4)。"""

    user_id: str
    name: str
    role: str

    @classmethod
    def of(cls, user: dict) -> dict:
        return {"user_id": user["user_id"], "name": user["name"], "role": user["role"]}


class RoomRequest(_Base):
    """API-05・API-06 のリクエスト(P002 3.6 / 5.5)。全項目送信の全置換更新。"""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    name: Any = None
    capacity: Any = None
    equipment: Any = ""
    description: Any = ""
    is_active: Any = True

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: Any) -> str:
        text = _as_text(value, "会議室名を入力してください。")
        if text.strip() == "":
            _fail("会議室名を入力してください。")
        if len(text) > 50:
            # ★FIXME★ 50文字超過時の文言はP002 3.6に記載がないため、他項目の言い回しに合わせた
            _fail("会議室名は50文字以内で入力してください。")
        return text

    @field_validator("capacity")
    @classmethod
    def _check_capacity(cls, value: Any) -> int:
        message = "収容人数は1以上500以下の整数で入力してください。"
        if isinstance(value, bool) or not isinstance(value, int):
            _fail(message)
        if not 1 <= value <= 500:
            _fail(message)
        return value

    @field_validator("equipment")
    @classmethod
    def _check_equipment(cls, value: Any) -> str:
        text = "" if value is None else str(value)
        if len(text) > 200:
            _fail("設備は200文字以内で入力してください。")
        return text

    @field_validator("description")
    @classmethod
    def _check_description(cls, value: Any) -> str:
        text = "" if value is None else str(value)
        if len(text) > 200:
            _fail("説明文は200文字以内で入力してください。")
        return text

    @field_validator("is_active")
    @classmethod
    def _check_is_active(cls, value: Any) -> bool:
        if value is None:
            return True
        if not isinstance(value, bool):
            _fail("有効フラグは true または false で指定してください。")
        return value


class UserCreateRequest(_Base):
    """API-09 のリクエスト(P002 3.7 / 5.6)。"""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    user_id: Any = None
    name: Any = None
    role: Any = None
    password: Any = None
    is_active: Any = True

    @field_validator("user_id")
    @classmethod
    def _check_user_id(cls, value: Any) -> str:
        text = _as_text(value, "社員IDは半角英数字4〜20文字で入力してください。")
        if not USER_ID_PATTERN.match(text):
            _fail("社員IDは半角英数字4〜20文字で入力してください。")
        return text

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: Any) -> str:
        text = _as_text(value, "氏名を入力してください。")
        if text.strip() == "":
            _fail("氏名を入力してください。")
        if len(text) > 50:
            _fail("氏名は50文字以内で入力してください。")
        return text

    @field_validator("role")
    @classmethod
    def _check_role(cls, value: Any) -> str:
        if value not in ("general", "admin"):
            _fail("権限を選択してください。")
        return value

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: Any) -> str:
        text = _as_text(value, "パスワードは8〜64文字で入力してください。")
        if not 8 <= len(text) <= 64:
            _fail("パスワードは8〜64文字で入力してください。")
        return text

    @field_validator("is_active")
    @classmethod
    def _check_is_active(cls, value: Any) -> bool:
        if value is None:
            return True
        if not isinstance(value, bool):
            _fail("有効フラグは true または false で指定してください。")
        return value


class UserUpdateRequest(_Base):
    """API-10 のリクエスト(`user_id` は変更不可。`password` は省略可)。"""

    model_config = ConfigDict(extra="ignore", validate_default=True)

    name: Any = None
    role: Any = None
    is_active: Any = True
    password: Any = None

    _check_name = field_validator("name")(UserCreateRequest._check_name.__func__)
    _check_role = field_validator("role")(UserCreateRequest._check_role.__func__)
    _check_is_active = field_validator("is_active")(UserCreateRequest._check_is_active.__func__)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: Any) -> str | None:
        # 空欄なら変更しない(P002 3.7)
        if value is None or value == "":
            return None
        text = str(value)
        if not 8 <= len(text) <= 64:
            _fail("パスワードは8〜64文字で入力してください。")
        return text


DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

#: ※CR-001 オンライン会議URLの検証(P002 3.3。スキームの前方一致のみ。ADR-011)
MEETING_URL_MAX_LENGTH = 500
MEETING_URL_SCHEMES = ("http://", "https://")
MEETING_URL_LENGTH_MESSAGE = "オンライン会議URLは500文字以内で入力してください。"
MEETING_URL_SCHEME_MESSAGE = (
    "オンライン会議URLは http:// または https:// で始まるURLを入力してください。"
)

#: P002 3.3 に文言が無い入力エラーのメッセージ(U003-T2 でAgentの想定により補った)
# ★FIXME★ 30分刻み違反の文言はP002 3.3に記載がないため、他項目の言い回しに合わせた
TIME_STEP_MESSAGE = "時刻は30分単位で選択してください。"
# ★FIXME★ 業務時間外の文言はP002 3.3に記載がないため、表示範囲(08:00〜20:00)から補った
BUSINESS_HOURS_MESSAGE = "時刻は08:00〜20:00の範囲で選択してください。"
# ★FIXME★ 参加者の重複選択時の文言はP002 3.3に記載がない(「重複選択不可」の指定のみ)ため補った
DUPLICATE_ATTENDEE_MESSAGE = "参加者を重複して選択することはできません。"


class ReservationRequest(_Base):
    """API-15・API-16 のリクエスト(P002 3.3 / 5.7)。全項目送信の全置換更新。

    予約者(`user_id`)はリクエストに含めない(常にセッションのユーザー。P002 5.7)。
    """

    model_config = ConfigDict(extra="ignore", validate_default=True)

    room_id: Any = None
    reserved_date: Any = None
    start_time: Any = None
    end_time: Any = None
    title: Any = None
    attendee_user_ids: Any = None
    attendee_count: Any = None
    # ※CR-001 オンライン会議URL(任意)。キー欠落・None・空文字はいずれも空文字に正規化する
    meeting_url: Any = ""
    note: Any = ""

    @field_validator("room_id")
    @classmethod
    def _check_room_id(cls, value: Any) -> int:
        message = "会議室を選択してください。"
        if value is None or isinstance(value, bool) or not isinstance(value, int):
            _fail(message)
        return value

    @field_validator("reserved_date")
    @classmethod
    def _check_reserved_date(cls, value: Any) -> str:
        text = _as_text(value, "日付を入力してください。")
        if not DATE_PATTERN.match(text):
            _fail("日付を入力してください。")
        return text

    @field_validator("start_time")
    @classmethod
    def _check_start_time(cls, value: Any) -> str:
        text = _as_text(value, "開始時刻を選択してください。")
        if not TIME_PATTERN.match(text):
            _fail("開始時刻を選択してください。")
        return text

    @field_validator("end_time")
    @classmethod
    def _check_end_time(cls, value: Any) -> str:
        text = _as_text(value, "終了時刻は開始時刻より後にしてください。")
        if not TIME_PATTERN.match(text):
            _fail("終了時刻は開始時刻より後にしてください。")
        return text

    @field_validator("title")
    @classmethod
    def _check_title(cls, value: Any) -> str:
        text = _as_text(value, "件名を入力してください。")
        if text.strip() == "":
            _fail("件名を入力してください。")
        if len(text) > 100:
            _fail("件名は100文字以内で入力してください。")
        return text

    @field_validator("attendee_user_ids")
    @classmethod
    def _check_attendee_user_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            _fail("参加者は50名以内で選択してください。")
        if len(value) > 50:
            _fail("参加者は50名以内で選択してください。")
        ids = [str(v) for v in value]
        if len(set(ids)) != len(ids):
            _fail(DUPLICATE_ATTENDEE_MESSAGE)
        return ids

    @field_validator("attendee_count")
    @classmethod
    def _check_attendee_count(cls, value: Any) -> int | None:
        # 任意項目。未入力(None)はそのままNULLで保存する(P002 6.2)
        if value is None or value == "":
            return None
        message = "参加予定人数は1以上の整数で入力してください。"
        if isinstance(value, bool) or not isinstance(value, int):
            _fail(message)
        if not 1 <= value <= 9999:
            _fail(message)
        return value

    @field_validator("meeting_url")
    @classmethod
    def _check_meeting_url(cls, value: Any) -> str:
        """※CR-001。任意項目。空欄はエラーとせず空文字で保存する(P002 3.3 / 5.3、ADR-011)。

        判定順序は P002 3.3 の規定どおり「文字数 → スキーム」。両方に違反する場合は
        文字数のメッセージを返す。スキームは前方一致のみで判定し、URLの構文解析はしない。
        """
        if value is None:
            return ""
        text = str(value)
        if text == "":
            return ""
        if len(text) > MEETING_URL_MAX_LENGTH:
            _fail(MEETING_URL_LENGTH_MESSAGE)
        if not text.startswith(MEETING_URL_SCHEMES):
            _fail(MEETING_URL_SCHEME_MESSAGE)
        return text

    @field_validator("note")
    @classmethod
    def _check_note(cls, value: Any) -> str:
        text = "" if value is None else str(value)
        if len(text) > 500:
            _fail("備考は500文字以内で入力してください。")
        return text
