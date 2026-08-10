"""Shared domain exception classes (introduced U002), mapped to HTTP
responses by app/errors.py.

U001-T3's app/services/auth_service.py predates this module and keeps its
own InvalidCredentialsError/UnauthorizedError (auth-specific concepts, not
generic instances of these) - that is intentional, not an inconsistency to
"fix"; app/errors.py handles both styles.

Every class here carries `code`/`message`(/`fields`) as instance
attributes so app/errors.py can map them generically instead of writing one
bespoke handler per exception class (docs/P002-frontend-spec.md 4章冒頭 common
error envelope: {"error": {"code", "message", "fields"?}}).
"""

from __future__ import annotations


class ValidationError(Exception):
    """400 VALIDATION_ERROR. `fields` maps field name -> message, matching
    docs/P002-frontend-spec.md 4章冒頭's envelope."""

    code = "VALIDATION_ERROR"

    def __init__(self, message: str = "入力内容を確認してください", fields: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.fields = fields or {}


class NotFoundError(Exception):
    """404 NOT_FOUND."""

    code = "NOT_FOUND"

    def __init__(self, message: str = "リソースが見つかりません") -> None:
        super().__init__(message)
        self.message = message


class ForbiddenError(Exception):
    """403 FORBIDDEN. Used both for "not an admin" (require_admin) and for
    resource-level authorization failures (e.g. editing someone else's
    reservation, docs/P003-backend-spec.md 4.9.1節)."""

    code = "FORBIDDEN"

    def __init__(self, message: str = "権限がありません") -> None:
        super().__init__(message)
        self.message = message


class ReservationConflictError(Exception):
    """409 RESERVATION_CONFLICT (docs/P002-frontend-spec.md 4.7節)."""

    code = "RESERVATION_CONFLICT"

    def __init__(self, message: str = "選択した会議室・時間帯は既に予約されています") -> None:
        super().__init__(message)
        self.message = message


class SelfDeactivationForbiddenError(Exception):
    """400 SELF_DEACTIVATION_FORBIDDEN (docs/P002-frontend-spec.md 3.7節/4.11.1節)."""

    code = "SELF_DEACTIVATION_FORBIDDEN"

    def __init__(self, message: str = "自分自身は無効化できません") -> None:
        super().__init__(message)
        self.message = message


class LastAdminProtectedError(Exception):
    """400 LAST_ADMIN_PROTECTED (docs/P002-frontend-spec.md 3.7節/4.11.1節)."""

    code = "LAST_ADMIN_PROTECTED"

    def __init__(self, message: str = "最後の管理者アカウントは無効化できません") -> None:
        super().__init__(message)
        self.message = message
