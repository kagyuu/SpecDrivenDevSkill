"""U004-T5: 管理者専用画面・APIの横断的認可確認(結合確認用の薄いタスク)。

docs/P002-frontend-spec.md §6(認可の外部契約表)に列挙された操作を一覧化し、
一般ユーザーで呼び出すと一貫して403になることを確認する。個々のAPIの単体テストは
各タスク(U003-T3/T4, U004-T3)で既にカバーしているため、本テストは新しい業務ロジックを
実装せず、それらを横断的に再確認するのみ。
"""

import pytest

from tests.api.conftest import insert_room


def _login(client, employee_id):
    resp = client.post("/api/auth/login", json={"employee_id": employee_id, "password": "TestPassw0rd!"})
    assert resp.status_code == 200


ROOM_ADMIN_ONLY_OPS = [
    ("POST", "/api/rooms", {"name": "会議室X", "capacity": 5}),
    ("PUT", "/api/rooms/1", {"name": "会議室X", "capacity": 5}),
    ("DELETE", "/api/rooms/1", None),
]

USER_ADMIN_ONLY_OPS = [
    ("GET", "/api/users", None),
    ("POST", "/api/users", {"employee_id": "zzz", "name": "z", "role": "general", "initial_password": "Passw0rd1"}),
    ("PUT", "/api/users/1", {"name": "z", "role": "general", "is_active": True}),
    ("DELETE", "/api/users/1", None),
]


@pytest.mark.parametrize("method,path,body", ROOM_ADMIN_ONLY_OPS + USER_ADMIN_ONLY_OPS)
def test_admin_only_operations_forbidden_for_general_user(client, method, path, body):
    _login(client, "user001")
    resp = client.request(method, path, json=body)
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"


def test_editing_others_reservation_forbidden_for_general_user(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "件名"},
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


def test_admin_can_perform_all_admin_only_operations(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "admin001")

    assert client.post("/api/rooms", json={"name": "会議室Y", "capacity": 5}).status_code == 201
    assert client.put(f"/api/rooms/{room_id}", json={"name": "会議室Y改", "capacity": 5}).status_code == 200
    assert client.delete(f"/api/rooms/{room_id}").status_code == 204

    assert client.get("/api/users").status_code == 200
    created_user = client.post(
        "/api/users",
        json={"employee_id": "zzz", "name": "z", "role": "general", "initial_password": "Passw0rd1"},
    )
    assert created_user.status_code == 201
    user_id = created_user.json()["id"]
    assert client.put(f"/api/users/{user_id}", json={"name": "z2", "role": "general", "is_active": True}).status_code == 200
    assert client.delete(f"/api/users/{user_id}").status_code == 204
