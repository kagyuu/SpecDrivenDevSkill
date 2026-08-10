"""Unit tests for U001-T4 (docs/P007-impl-direction/U001-foundation-and-auth.md).

Target: POST /api/auth/login, POST /api/auth/logout, GET /api/me
(FastAPI's TestClient, per this task's own 【Unit Test内容】).

Each test gets an isolated on-disk SQLite DB via the DATABASE_PATH env var
(app/db/connection.py reads it at call time, both for the app's lifespan
migration hook and for app/dependencies.py's get_db) so these tests never
touch server/data/app.db. COOKIE_SECURE=false so the Secure-flagged
Set-Cookie (docs/P002-frontend-spec.md 2章) is not dropped over the
http-only TestClient transport.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN_ID = "admin"
ADMIN_PASSWORD = "ChangeMe123!"  # server/migrations/002_seed_admin.sql


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("COOKIE_SECURE", "false")
    with TestClient(app) as test_client:
        yield test_client


def test_login_success_then_me_returns_user(client: TestClient):
    login_response = client.post(
        "/api/auth/login",
        json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD},
    )

    assert login_response.status_code == 200
    assert "session_id" in login_response.cookies
    body = login_response.json()
    assert body == {
        "employee_id": ADMIN_ID,
        "name": "システム管理者",
        "role": "admin",
    }

    me_response = client.get("/api/me")

    assert me_response.status_code == 200
    assert me_response.json() == body


def test_login_wrong_password_returns_401(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"employee_id": ADMIN_ID, "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_without_cookie_returns_401(client: TestClient):
    response = client.get("/api/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_logout_then_me_with_same_cookie_returns_401(client: TestClient):
    client.post(
        "/api/auth/login",
        json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD},
    )

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {}

    me_response = client.get("/api/me")
    assert me_response.status_code == 401


def test_logout_without_prior_login_is_idempotent(client: TestClient):
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {}


def test_login_missing_fields_returns_400_validation_error(client: TestClient):
    response = client.post(
        "/api/auth/login", json={"employee_id": "", "password": ""}
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["fields"]["employee_id"] == "社員IDを入力してください"
    assert body["error"]["fields"]["password"] == "パスワードを入力してください"
