"""docs/P009-acceptance-direction/A008-security-password-exposure.md

パスワード(平文・ハッシュ値とも)がAPIレスポンス・アプリケーションログに露出しないことを確認する。
"""

from __future__ import annotations

import json
import logging


def _login(client, employee_id, password="TestPassw0rd!"):
    return client.post("/api/auth/login", json={"employee_id": employee_id, "password": password})


def test_password_not_exposed_in_responses_or_logs(client, caplog):
    with caplog.at_level(logging.INFO, logger="app"):
        login_resp = _login(client, "admin001")
        assert login_resp.status_code == 200

        create_resp = client.post(
            "/api/users",
            json={
                "employee_id": "a008user",
                "name": "露出確認太郎",
                "role": "general",
                "initial_password": "SuperSecret1",
            },
        )
        assert create_resp.status_code == 201

        users_resp = client.get("/api/users")
        assert users_resp.status_code == 200

    sensitive_substrings = ["SuperSecret1", "TestPassw0rd!", "password_hash", "$2b$"]

    # 手順2: GET /api/users のレスポンス全体
    users_text = json.dumps(users_resp.json(), ensure_ascii=False)
    for needle in sensitive_substrings:
        assert needle not in users_text, f"'{needle}' が /api/users レスポンスに含まれている"

    create_text = json.dumps(create_resp.json(), ensure_ascii=False)
    for needle in sensitive_substrings:
        assert needle not in create_text, f"'{needle}' が /api/users 作成レスポンスに含まれている"

    # 手順3: POST /api/auth/login のレスポンス
    login_text = json.dumps(login_resp.json(), ensure_ascii=False)
    for needle in sensitive_substrings:
        assert needle not in login_text, f"'{needle}' が /api/auth/login レスポンスに含まれている"

    # 手順4: アプリケーションログ
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    for needle in sensitive_substrings:
        assert needle not in log_text, f"'{needle}' がアプリケーションログに含まれている"
