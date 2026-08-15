"""S01ログイン画面の入力バリデーション。docs/P002-frontend-spec.md §3 S01。"""

from __future__ import annotations


def validate_login_input(employee_id: str, password: str) -> list[str]:
    errors: list[str] = []
    if not employee_id:
        errors.append("社員IDを入力してください")
    if not password:
        errors.append("パスワードを入力してください")
    return errors
