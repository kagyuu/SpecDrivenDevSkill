"""P103 integration test T001 (docs/P008-test-direction/T001-login-success-session.md).

Confirms a correct login completes the full APIハンドラ→Service→Repository→DB
chain: Set-Cookie is issued, a real row lands in the sessions table with a
~8h expiry, and the resulting Cookie authenticates GET /api/me. Unlike
server/tests/test_auth_api.py (U001-T4 unit test, which only checks HTTP
responses), this test also queries the SQLite file directly to confirm the
DB side of the integration.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN_ID = "admin"
ADMIN_PASSWORD = "ChangeMe123!"


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture()
def client(db_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("COOKIE_SECURE", "false")
    with TestClient(app) as test_client:
        yield test_client


def test_login_success_creates_session_row_and_authenticates_me(
    client: TestClient, db_path: Path
):
    # 手順1
    login_response = client.post(
        "/api/auth/login", json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD}
    )
    assert login_response.status_code == 200

    # 手順2
    assert "session_id" in login_response.cookies
    session_id = login_response.cookies["session_id"]

    # 手順3
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT user_id, expires_at FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["user_id"] == "admin"
    expires_at = datetime.fromisoformat(row["expires_at"])
    expected = datetime.now(timezone.utc) + timedelta(hours=8)
    assert abs((expires_at - expected).total_seconds()) < 60  # within 1 minute

    # 手順4
    me_response = client.get("/api/me")
    assert me_response.status_code == 200
    assert me_response.json() == {
        "employee_id": "admin",
        "name": "システム管理者",
        "role": "admin",
    }
