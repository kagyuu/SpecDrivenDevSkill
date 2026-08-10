"""P103 integration test T005 (docs/P008-test-direction/T005-room-deactivate-filter.md).

Confirms the include_inactive filtering behavior end-to-end: default
listing excludes a deactivated room, an admin's include_inactive=true still
sees it, and a general user's include_inactive=true is silently ignored
(docs/P002-frontend-spec.md 4.4節).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.password import hash_password

ADMIN_ID = "admin"
ADMIN_PASSWORD = "ChangeMe123!"
GENERAL_ID = "u001"
GENERAL_PASSWORD = "GeneralPass1!"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("COOKIE_SECURE", "false")
    with TestClient(app) as test_client:
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO users (user_id, name, password_hash, role, is_active, "
            "created_at, updated_at) VALUES (?, ?, ?, 'general', 1, datetime('now'), datetime('now'))",
            (GENERAL_ID, "一般 太郎", hash_password(GENERAL_PASSWORD)),
        )
        conn.commit()
        conn.close()
        yield test_client


def _login(client: TestClient, employee_id: str, password: str) -> None:
    response = client.post(
        "/api/auth/login", json={"employee_id": employee_id, "password": password}
    )
    assert response.status_code == 200


def test_deactivated_room_is_hidden_by_default_and_visible_to_admin_only(
    client: TestClient,
):
    _login(client, ADMIN_ID, ADMIN_PASSWORD)
    room_id = client.post(
        "/api/rooms",
        json={"name": "第一会議室", "capacity": 8, "equipment": [], "description": None},
    ).json()["room_id"]

    # 手順1
    delete_response = client.delete(f"/api/rooms/{room_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False

    # 手順2
    default_listing = client.get("/api/rooms").json()
    assert room_id not in [r["room_id"] for r in default_listing]

    # 手順3
    admin_with_inactive = client.get("/api/rooms", params={"include_inactive": "true"}).json()
    matching = [r for r in admin_with_inactive if r["room_id"] == room_id]
    assert len(matching) == 1
    assert matching[0]["is_active"] is False

    # 手順4
    client.post("/api/auth/logout")
    _login(client, GENERAL_ID, GENERAL_PASSWORD)
    general_with_inactive = client.get("/api/rooms", params={"include_inactive": "true"}).json()
    assert room_id not in [r["room_id"] for r in general_with_inactive]
