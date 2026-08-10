"""P201 acceptance test A007 (docs/P009-acceptance-direction/A007-security-crosscheck.md).

Uses TestClient (in-process) since this scenario is about response
content/headers and DB storage format, not real-network timing/concurrency
(unlike A005/A009 which specifically need a real subprocess).
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


def test_password_is_never_stored_in_plaintext(client: TestClient, db_path: Path):
    # 手順1
    login_response = client.post(
        "/api/auth/login", json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD}
    )
    assert login_response.status_code == 200

    conn = sqlite3.connect(str(db_path))
    row = conn.execute(
        "SELECT password_hash FROM users WHERE user_id = ?", (ADMIN_ID,)
    ).fetchone()
    conn.close()
    assert row is not None
    password_hash = row[0]
    assert password_hash != ADMIN_PASSWORD
    assert password_hash.startswith("scrypt$")
    parts = password_hash.split("$")
    assert len(parts) == 3


def test_login_cookie_has_httponly_and_samesite_lax(client: TestClient):
    # 手順2
    response = client.post(
        "/api/auth/login", json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD}
    )
    set_cookie = response.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie
    assert "samesite=lax" in set_cookie.lower()


def test_requests_without_a_cookie_are_rejected_for_get_endpoints(client: TestClient):
    # 手順3
    assert client.get("/api/me").status_code == 401
    assert (
        client.get(
            "/api/reservations", params={"date_from": "2099-01-01", "date_to": "2099-01-01"}
        ).status_code
        == 401
    )
    assert client.get("/api/rooms").status_code == 401


def test_requests_without_a_cookie_are_rejected_for_post_endpoints(client: TestClient):
    # 手順4
    assert (
        client.post(
            "/api/reservations",
            json={
                "room_id": 1,
                "date": "2099-01-01",
                "start_time": "10:00",
                "end_time": "11:00",
                "title": "x",
                "participant_user_ids": [],
                "attendee_count": None,
                "notes": None,
            },
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/rooms",
            json={"name": "x", "capacity": 1, "equipment": [], "description": None},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/users",
            json={"employee_id": "e9999", "name": "x", "password": "Password1!", "role": "general"},
        ).status_code
        == 401
    )
