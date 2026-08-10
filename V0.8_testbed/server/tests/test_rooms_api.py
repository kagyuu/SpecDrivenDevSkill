"""Unit tests for U002-T2 (docs/P007-impl-direction/U002-room-management.md).

Target: GET/POST/PUT/DELETE /api/rooms
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN_ID = "admin"
ADMIN_PASSWORD = "ChangeMe123!"  # server/migrations/002_seed_admin.sql
GENERAL_ID = "u001"
GENERAL_PASSWORD = "GeneralPass1!"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("COOKIE_SECURE", "false")
    with TestClient(app) as test_client:
        # Seed a general user directly via SQL - app/repositories/user_repository.py
        # has no write methods yet (added by U005-T1), matching the same
        # workaround used in server/tests/test_auth_service.py.
        import sqlite3

        from app.security.password import hash_password

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


def test_admin_can_create_list_update_and_delete_room(client: TestClient):
    _login(client, ADMIN_ID, ADMIN_PASSWORD)

    create_response = client.post(
        "/api/rooms",
        json={"name": "会議室A", "capacity": 8, "equipment": ["プロジェクター"], "description": "3階"},
    )
    assert create_response.status_code == 201
    room = create_response.json()
    assert room["is_active"] is True
    room_id = room["room_id"]

    list_response = client.get("/api/rooms")
    assert list_response.status_code == 200
    assert [r["room_id"] for r in list_response.json()] == [room_id]

    update_response = client.put(
        f"/api/rooms/{room_id}",
        json={
            "name": "会議室A改",
            "capacity": 12,
            "equipment": [],
            "description": None,
            "is_active": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["capacity"] == 12

    delete_response = client.delete(f"/api/rooms/{room_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"room_id": room_id, "is_active": False}

    # Logically deleted room no longer appears in the default listing.
    after_delete = client.get("/api/rooms")
    assert after_delete.json() == []

    # ...but is visible to an admin who asks for include_inactive=true.
    with_inactive = client.get("/api/rooms", params={"include_inactive": "true"})
    assert [r["room_id"] for r in with_inactive.json()] == [room_id]


def test_general_user_post_put_delete_return_403(client: TestClient):
    _login(client, ADMIN_ID, ADMIN_PASSWORD)
    room_id = client.post(
        "/api/rooms", json={"name": "会議室B", "capacity": 4, "equipment": [], "description": None}
    ).json()["room_id"]
    client.post("/api/auth/logout")

    _login(client, GENERAL_ID, GENERAL_PASSWORD)

    assert (
        client.post(
            "/api/rooms", json={"name": "会議室C", "capacity": 4, "equipment": [], "description": None}
        ).status_code
        == 403
    )
    assert (
        client.put(
            f"/api/rooms/{room_id}",
            json={"name": "x", "capacity": 1, "equipment": [], "description": None, "is_active": True},
        ).status_code
        == 403
    )
    assert client.delete(f"/api/rooms/{room_id}").status_code == 403

    # A general user's include_inactive=true is silently ignored, not an error.
    listing = client.get("/api/rooms", params={"include_inactive": "true"})
    assert listing.status_code == 200


def test_unauthenticated_get_returns_401(client: TestClient):
    response = client.get("/api/rooms")

    assert response.status_code == 401


def test_update_and_delete_nonexistent_room_return_404(client: TestClient):
    _login(client, ADMIN_ID, ADMIN_PASSWORD)

    update_response = client.put(
        "/api/rooms/9999",
        json={"name": "x", "capacity": 1, "equipment": [], "description": None, "is_active": True},
    )
    assert update_response.status_code == 404

    delete_response = client.delete("/api/rooms/9999")
    assert delete_response.status_code == 404


def test_create_room_validation_error_returns_400(client: TestClient):
    _login(client, ADMIN_ID, ADMIN_PASSWORD)

    response = client.post(
        "/api/rooms", json={"name": "", "capacity": 0, "equipment": [], "description": None}
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "name" in body["error"]["fields"]
    assert "capacity" in body["error"]["fields"]
