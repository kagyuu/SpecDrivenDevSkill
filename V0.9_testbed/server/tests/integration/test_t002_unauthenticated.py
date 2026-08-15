"""docs/P008-test-direction/T002-unauthenticated-access.md

未認証・無効(期限切れ/削除済み)セッションでの保護APIアクセスが、一貫して401
UNAUTHENTICATEDになることを結合確認する。
"""

from __future__ import annotations

import sqlite3


def test_me_without_cookie_is_unauthenticated(client):
    resp = client.get("/api/me")
    assert resp.status_code == 401
    assert resp.json() == {"error_code": "UNAUTHENTICATED", "message": "ログインが必要です"}


def test_me_after_logout_is_unauthenticated(client):
    client.post("/api/auth/login", json={"employee_id": "user001", "password": "TestPassw0rd!"})
    client.post("/api/auth/logout")

    resp = client.get("/api/me")
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "UNAUTHENTICATED"


def test_expired_session_is_unauthenticated(client, db_path):
    client.post("/api/auth/login", json={"employee_id": "user001", "password": "TestPassw0rd!"})

    # セッションのexpires_atを過去日時に直接書き換える(手順3: セッション期限切れの模擬)。
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE sessions SET expires_at = '2000-01-01T00:00:00+00:00'")
    conn.commit()
    conn.close()

    resp = client.get("/api/rooms")
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "UNAUTHENTICATED"
