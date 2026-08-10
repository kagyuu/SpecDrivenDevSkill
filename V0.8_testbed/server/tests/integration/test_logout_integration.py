"""P103 integration test T003 (docs/P008-test-direction/T003-logout-session-invalidation.md).

Confirms logout actually deletes the session row from the DB (not just
returns 200), and that the now-invalid Cookie is rejected by a subsequent
request, and that calling logout again with the same (now-invalid) Cookie
is still idempotent (200).
"""

from __future__ import annotations

import sqlite3
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


def test_logout_deletes_session_row_and_invalidates_subsequent_requests(
    client: TestClient, db_path: Path
):
    login_response = client.post(
        "/api/auth/login", json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD}
    )
    session_id = login_response.cookies["session_id"]

    # 手順1
    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200

    # 手順2
    conn = sqlite3.connect(str(db_path))
    row = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    conn.close()
    assert row[0] == 0

    # 手順3
    me_response = client.get("/api/me")
    assert me_response.status_code == 401
    assert me_response.json()["error"]["code"] == "UNAUTHORIZED"

    # 手順4
    second_logout_response = client.post("/api/auth/logout")
    assert second_logout_response.status_code == 200
