"""docs/P009-acceptance-direction/A003-cross-cutting-authorization.md

docs/P002-frontend-spec.md §6の認可の外部契約表を、実装全体を通してシステムテスト相当で確認する。
"""

from __future__ import annotations

from tests.api.conftest import insert_room


def _login(client, employee_id):
    resp = client.post("/api/auth/login", json={"employee_id": employee_id, "password": "TestPassw0rd!"})
    assert resp.status_code == 200


def test_step1_non_owner_cannot_edit_or_delete_others_reservation(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "A003"},
    ).json()
    client.post("/api/auth/logout")

    _login(client, "user002")
    put_resp = client.put(
        f"/api/reservations/{created['id']}",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "改ざん"},
    )
    delete_resp = client.delete(f"/api/reservations/{created['id']}")
    assert put_resp.status_code == 403
    assert delete_resp.status_code == 403


def test_step2_general_user_forbidden_from_all_admin_apis(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user002")

    checks = [
        client.post("/api/rooms", json={"name": "x", "capacity": 1}),
        client.put(f"/api/rooms/{room_id}", json={"name": "x", "capacity": 1}),
        client.delete(f"/api/rooms/{room_id}"),
        client.get("/api/users"),
        client.post("/api/users", json={"employee_id": "zz1", "name": "z", "role": "general", "initial_password": "Passw0rd1"}),
        client.put("/api/users/1", json={"name": "z", "role": "general", "is_active": True}),
        client.delete("/api/users/1"),
    ]
    for resp in checks:
        assert resp.status_code == 403, f"{resp.request.method} {resp.request.url} -> {resp.status_code}"


def test_step3_admin_can_perform_all_of_the_above(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "A003b"},
    ).json()
    client.post("/api/auth/logout")

    _login(client, "admin001")
    assert client.put(
        f"/api/reservations/{created['id']}",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "管理者編集"},
    ).status_code == 200
    assert client.delete(f"/api/reservations/{created['id']}").status_code == 204

    new_room = client.post("/api/rooms", json={"name": "A003会議室", "capacity": 5})
    assert new_room.status_code == 201
    room_id2 = new_room.json()["id"]
    assert client.put(f"/api/rooms/{room_id2}", json={"name": "A003会議室改", "capacity": 5}).status_code == 200
    assert client.delete(f"/api/rooms/{room_id2}").status_code == 204

    assert client.get("/api/users").status_code == 200
    new_user = client.post(
        "/api/users",
        json={"employee_id": "zz2", "name": "z", "role": "general", "initial_password": "Passw0rd1"},
    )
    assert new_user.status_code == 201
    user_id = new_user.json()["id"]
    assert client.put(f"/api/users/{user_id}", json={"name": "z2", "role": "general", "is_active": True}).status_code == 200
    assert client.delete(f"/api/users/{user_id}").status_code == 204


def test_step4_unauthenticated_gets_401_on_all_protected_apis(client, db_path):
    room_id = insert_room(db_path)
    checks = [
        client.get("/api/me"),
        client.get("/api/rooms"),
        client.post("/api/rooms", json={"name": "x", "capacity": 1}),
        client.get("/api/reservations", params={"date_from": "2026-08-01", "date_to": "2026-08-31"}),
        client.post(
            "/api/reservations",
            json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "x"},
        ),
        client.get("/api/users"),
    ]
    for resp in checks:
        assert resp.status_code == 401, f"{resp.request.method} {resp.request.url} -> {resp.status_code}"
