"""Unit tests for U003-T3 (docs/P007-impl-direction/U003-reservation-core-and-calendar.md).

Target: GET/POST /api/reservations

U004-T2 appends tests for GET/PUT/DELETE /api/reservations/{id} and GET
/api/reservations/mine at the end of this file, per that task's own
作成・編集対象ファイル ("test_reservations_api.py(追加テスト)").
"""

from __future__ import annotations

import sqlite3
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
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO users (user_id, name, password_hash, role, is_active, "
            "created_at, updated_at) VALUES (?, ?, ?, 'general', 1, datetime('now'), datetime('now'))",
            (GENERAL_ID, "一般 太郎", hash_password(GENERAL_PASSWORD)),
        )
        conn.commit()
        conn.close()
        yield test_client


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200


def _login_general(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"employee_id": GENERAL_ID, "password": GENERAL_PASSWORD}
    )
    assert response.status_code == 200


def _create_room(client: TestClient, capacity: int = 8) -> int:
    response = client.post(
        "/api/rooms",
        json={"name": "会議室A", "capacity": capacity, "equipment": [], "description": None},
    )
    assert response.status_code == 201
    return response.json()["room_id"]


def test_create_reservation_returns_201_with_detail_shape(client: TestClient):
    _login(client)
    room_id = _create_room(client)

    response = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例会議",
            "participant_user_ids": [],
            "attendee_count": 3,
            "notes": None,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["room_id"] == room_id
    assert body["organizer_user_id"] == ADMIN_ID
    assert body["editable"] is True
    assert body["title"] == "定例会議"


def test_list_reservations_includes_room_and_organizer_names_and_excludes_details(
    client: TestClient,
):
    _login(client)
    room_id = _create_room(client)
    client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例会議",
            "participant_user_ids": [],
            "attendee_count": 3,
            "notes": "非公開メモ",
        },
    )

    response = client.get(
        "/api/reservations", params={"date_from": "2026-08-10", "date_to": "2026-08-10"}
    )

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["room_name"] == "会議室A"
    assert items[0]["organizer_name"] == "システム管理者"
    # docs/P002-frontend-spec.md 4.6節: attendee_count/notes/participants must
    # NOT be included in the lightweight calendar list response.
    assert "attendee_count" not in items[0]
    assert "notes" not in items[0]


def test_unauthenticated_requests_return_401(client: TestClient):
    assert (
        client.get("/api/reservations", params={"date_from": "2026-08-10", "date_to": "2026-08-10"}).status_code
        == 401
    )
    assert (
        client.post(
            "/api/reservations",
            json={
                "room_id": 1,
                "date": "2026-08-10",
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


def test_create_reservation_validation_error_returns_400_with_fields(client: TestClient):
    _login(client)
    room_id = _create_room(client)

    response = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "11:00",
            "end_time": "10:00",
            "title": "件名",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_reservation_conflict_returns_409(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    body = {
        "room_id": room_id,
        "date": "2026-08-10",
        "start_time": "10:00",
        "end_time": "11:00",
        "title": "件名",
        "participant_user_ids": [],
        "attendee_count": None,
        "notes": None,
    }
    assert client.post("/api/reservations", json=body).status_code == 201

    response = client.post("/api/reservations", json=body)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESERVATION_CONFLICT"


def test_create_reservation_with_nonexistent_room_returns_404(client: TestClient):
    _login(client)

    response = client.post(
        "/api/reservations",
        json={
            "room_id": 9999,
            "date": "2026-08-10",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "件名",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
        },
    )

    assert response.status_code == 404


def test_list_reservations_with_date_from_after_date_to_returns_400(client: TestClient):
    _login(client)

    response = client.get(
        "/api/reservations", params={"date_from": "2026-08-11", "date_to": "2026-08-10"}
    )

    assert response.status_code == 400


# --- U004-T2 additions ----------------------------------------------------


def _create_reservation(client: TestClient, room_id: int, **overrides) -> dict:
    body = {
        "room_id": room_id,
        "date": "2026-08-10",
        "start_time": "10:00",
        "end_time": "11:00",
        "title": "定例会議",
        "participant_user_ids": [],
        "attendee_count": None,
        "notes": None,
    }
    body.update(overrides)
    response = client.post("/api/reservations", json=body)
    assert response.status_code == 201
    return response.json()


def test_get_reservation_detail_by_organizer(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    reservation = _create_reservation(client, room_id)

    response = client.get(f"/api/reservations/{reservation['reservation_id']}")

    assert response.status_code == 200
    assert response.json()["editable"] is True


def test_update_reservation_by_organizer_returns_200(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    reservation = _create_reservation(client, room_id)

    response = client.put(
        f"/api/reservations/{reservation['reservation_id']}",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "13:00",
            "end_time": "14:00",
            "title": "変更後",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["title"] == "変更後"


def test_delete_reservation_by_organizer_returns_204(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    reservation = _create_reservation(client, room_id)

    response = client.delete(f"/api/reservations/{reservation['reservation_id']}")

    assert response.status_code == 204
    assert client.get(f"/api/reservations/{reservation['reservation_id']}").status_code == 404


def test_update_and_delete_by_unrelated_general_user_return_403(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    reservation = _create_reservation(client, room_id)
    client.post("/api/auth/logout")

    _login_general(client)

    update_response = client.put(
        f"/api/reservations/{reservation['reservation_id']}",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "13:00",
            "end_time": "14:00",
            "title": "変更後",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
        },
    )
    assert update_response.status_code == 403

    delete_response = client.delete(f"/api/reservations/{reservation['reservation_id']}")
    assert delete_response.status_code == 403


def test_get_update_delete_nonexistent_reservation_return_404(client: TestClient):
    _login(client)

    assert client.get("/api/reservations/9999").status_code == 404
    assert (
        client.put(
            "/api/reservations/9999",
            json={
                "room_id": 1,
                "date": "2026-08-10",
                "start_time": "10:00",
                "end_time": "11:00",
                "title": "x",
                "participant_user_ids": [],
                "attendee_count": None,
                "notes": None,
            },
        ).status_code
        == 404
    )
    assert client.delete("/api/reservations/9999").status_code == 404


def test_update_reservation_conflict_returns_409(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    reservation = _create_reservation(client, room_id)
    _create_reservation(
        client, room_id, date="2026-08-10", start_time="13:00", end_time="14:00", title="別予約"
    )

    response = client.put(
        f"/api/reservations/{reservation['reservation_id']}",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "13:00",
            "end_time": "14:00",
            "title": "変更後",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
        },
    )

    assert response.status_code == 409


def test_my_reservations_upcoming_past_and_all(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    _create_reservation(client, room_id, date="2020-01-01", title="過去の予約")
    _create_reservation(client, room_id, date="2099-01-01", title="未来の予約")

    upcoming = client.get("/api/reservations/mine", params={"period": "upcoming"}).json()
    past = client.get("/api/reservations/mine", params={"period": "past"}).json()
    everything = client.get("/api/reservations/mine", params={"period": "all"}).json()

    assert [item["title"] for item in upcoming] == ["未来の予約"]
    assert [item["title"] for item in past] == ["過去の予約"]
    assert len(everything) == 2


def test_my_reservations_without_login_returns_401(client: TestClient):
    response = client.get("/api/reservations/mine")

    assert response.status_code == 401


# --- U003-T7/U004-T6 additions (CR-001: docs/P901-cr-direction/CR-001.md) ---


def test_create_reservation_with_meeting_url_returns_it_in_detail(client: TestClient):
    _login(client)
    room_id = _create_room(client)

    reservation = _create_reservation(
        client, room_id, meeting_url="https://example.com/meeting/123"
    )

    assert reservation["meeting_url"] == "https://example.com/meeting/123"


def test_create_reservation_without_meeting_url_returns_null(client: TestClient):
    _login(client)
    room_id = _create_room(client)

    reservation = _create_reservation(client, room_id)

    assert reservation["meeting_url"] is None


@pytest.mark.parametrize(
    "meeting_url",
    ["ftp://example.com/meeting", "example.com/meeting"],
)
def test_create_reservation_with_invalid_meeting_url_returns_400(
    client: TestClient, meeting_url: str
):
    _login(client)
    room_id = _create_room(client)

    response = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例会議",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
            "meeting_url": meeting_url,
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["fields"]["meeting_url"]


def test_create_reservation_with_501_char_meeting_url_returns_400(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    url = "https://example.com/" + "a" * (501 - len("https://example.com/"))

    response = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例会議",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
            "meeting_url": url,
        },
    )

    assert response.status_code == 400


def test_list_reservations_does_not_include_meeting_url(client: TestClient):
    """docs/P002-frontend-spec.md 4.6節: 一覧レスポンスは意図的にmeeting_urlを
    含めない(CR-001)。回帰防止。"""
    _login(client)
    room_id = _create_room(client)
    _create_reservation(client, room_id, meeting_url="https://example.com/meeting/123")

    response = client.get(
        "/api/reservations", params={"date_from": "2026-08-10", "date_to": "2026-08-10"}
    )

    assert response.status_code == 200
    assert "meeting_url" not in response.json()[0]


def test_update_reservation_changes_meeting_url(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    reservation = _create_reservation(client, room_id)

    response = client.put(
        f"/api/reservations/{reservation['reservation_id']}",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "13:00",
            "end_time": "14:00",
            "title": "変更後",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
            "meeting_url": "https://example.com/meeting/updated",
        },
    )

    assert response.status_code == 200
    assert response.json()["meeting_url"] == "https://example.com/meeting/updated"


def test_update_reservation_clears_meeting_url_with_empty_string(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    reservation = _create_reservation(
        client, room_id, meeting_url="https://example.com/meeting/123"
    )

    response = client.put(
        f"/api/reservations/{reservation['reservation_id']}",
        json={
            "room_id": room_id,
            "date": "2026-08-10",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例会議",
            "participant_user_ids": [],
            "attendee_count": None,
            "notes": None,
            "meeting_url": "",
        },
    )

    assert response.status_code == 200
    assert response.json()["meeting_url"] is None


def test_get_reservation_detail_includes_meeting_url(client: TestClient):
    _login(client)
    room_id = _create_room(client)
    reservation = _create_reservation(
        client, room_id, meeting_url="https://example.com/meeting/123"
    )

    response = client.get(f"/api/reservations/{reservation['reservation_id']}")

    assert response.status_code == 200
    assert response.json()["meeting_url"] == "https://example.com/meeting/123"
