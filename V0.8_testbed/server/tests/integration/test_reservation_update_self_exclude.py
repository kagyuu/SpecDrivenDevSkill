"""P103 integration test T010 (docs/P008-test-direction/T010-reservation-update-self-exclude.md).

Confirms updating a reservation while leaving its own time slot unchanged
does not trigger a false-positive 409 (the self-exclusion logic in
docs/P003-backend-spec.md 4.9.1節: exclude_reservation_id).
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


def test_updating_a_reservation_within_its_own_slot_never_returns_409(client: TestClient):
    login_response = client.post(
        "/api/auth/login", json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD}
    )
    assert login_response.status_code == 200
    room_id = client.post(
        "/api/rooms",
        json={"name": "第一会議室", "capacity": 8, "equipment": [], "description": None},
    ).json()["room_id"]
    created = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2099-01-01",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "週次定例会議",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
        },
    ).json()
    reservation_id = created["reservation_id"]

    # 手順1: 時間帯は変更せず件名のみ変更
    title_only_response = client.put(
        f"/api/reservations/{reservation_id}",
        json={
            "room_id": room_id,
            "date": "2099-01-01",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "週次定例会議(更新)",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
        },
    )
    # 手順2
    assert title_only_response.status_code == 200
    assert title_only_response.json()["title"] == "週次定例会議(更新)"

    # 手順3: 時間帯は10:00-11:00のまま、参加予定人数のみ変更
    attendee_count_response = client.put(
        f"/api/reservations/{reservation_id}",
        json={
            "room_id": room_id,
            "date": "2099-01-01",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "週次定例会議(更新)",
            "participant_user_ids": [],
            "attendee_count": 7,
            "notes": None,
        },
    )
    assert attendee_count_response.status_code == 200
    assert attendee_count_response.json()["attendee_count"] == 7
