"""Unit tests for U003-T3 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md).

Target: GET /api/users/directory
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN_ID = "admin"
ADMIN_PASSWORD = "ChangeMe123!"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("COOKIE_SECURE", "false")
    with TestClient(app) as test_client:
        yield test_client


def test_directory_returns_active_users_for_any_logged_in_user(client: TestClient):
    login_response = client.post(
        "/api/auth/login", json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD}
    )
    assert login_response.status_code == 200

    response = client.get("/api/users/directory")

    assert response.status_code == 200
    assert response.json() == [{"employee_id": "admin", "name": "システム管理者"}]


def test_directory_entries_contain_only_employee_id_and_name(client: TestClient):
    client.post("/api/auth/login", json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD})

    entry = client.get("/api/users/directory").json()[0]

    assert set(entry.keys()) == {"employee_id", "name"}


def test_directory_without_login_returns_401(client: TestClient):
    response = client.get("/api/users/directory")

    assert response.status_code == 401
