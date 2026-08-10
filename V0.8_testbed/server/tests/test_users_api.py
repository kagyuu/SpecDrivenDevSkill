"""Unit tests for U005-T2 (docs/P007-impl-direction/U005-user-management-and-hardening.md).

Target: GET/POST/PUT/DELETE /api/users
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


def _login_admin(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"employee_id": ADMIN_ID, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200


def _create_general_user(client: TestClient, employee_id: str = "u001") -> dict:
    response = client.post(
        "/api/users",
        json={"employee_id": employee_id, "name": "一般 太郎", "password": "Password1!", "role": "general"},
    )
    assert response.status_code == 201
    return response.json()


def test_admin_can_create_list_update_and_deactivate_user(client: TestClient):
    _login_admin(client)

    created = _create_general_user(client)
    assert created["employee_id"] == "u001"
    assert "password_hash" not in created

    listing = client.get("/api/users")
    assert listing.status_code == 200
    assert any(u["employee_id"] == "u001" for u in listing.json())

    update_response = client.put(
        "/api/users/u001",
        json={"name": "一般 次郎", "password": None, "role": "general", "is_active": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "一般 次郎"

    delete_response = client.delete("/api/users/u001")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"employee_id": "u001", "is_active": False}


def test_general_user_cannot_access_admin_user_endpoints(client: TestClient):
    _login_admin(client)
    _create_general_user(client)
    client.post("/api/auth/logout")

    login_response = client.post(
        "/api/auth/login", json={"employee_id": "u001", "password": "Password1!"}
    )
    assert login_response.status_code == 200

    assert client.get("/api/users").status_code == 403
    assert (
        client.post(
            "/api/users",
            json={"employee_id": "u002", "name": "x", "password": "Password1!", "role": "general"},
        ).status_code
        == 403
    )
    assert (
        client.put(
            "/api/users/u001",
            json={"name": "x", "password": None, "role": "general", "is_active": True},
        ).status_code
        == 403
    )
    assert client.delete("/api/users/u001").status_code == 403


def test_create_user_with_duplicate_employee_id_returns_400(client: TestClient):
    _login_admin(client)
    _create_general_user(client)

    response = client.post(
        "/api/users",
        json={"employee_id": "u001", "name": "別 太郎", "password": "Password1!", "role": "general"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_self_deactivation_returns_400_with_self_deactivation_code(client: TestClient):
    _login_admin(client)

    response = client.put(
        "/api/users/admin",
        json={"name": "システム管理者", "password": None, "role": "admin", "is_active": False},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SELF_DEACTIVATION_FORBIDDEN"


def test_deactivating_one_of_two_admins_via_api_succeeds(client: TestClient):
    """docs/P007-impl-direction/U005-user-management-and-hardening.md U005-T1
    の異常系項目「管理者が2名いる状態での1名無効化は成功すること(境界値)」の
    API経由での確認。

    ★実施メモ: LAST_ADMIN_PROTECTED を「自分以外の管理者」が引き起こすケースを
    このAPI経由で再現するテストは書いていない - 有効な管理者が1名しかいない
    状態では、その管理者以外は管理者専用APIを一切呼び出せない
    (Depends(require_admin))ため、無効化を試みる呼び出し元は必ず対象自身になり、
    常にSELF_DEACTIVATION_FORBIDDENが先に発生する
    (test_self_deactivation_returns_400_with_self_deactivation_code参照)。
    LAST_ADMIN_PROTECTED自体の発火は、任意の requesting_user_id を渡せる
    Service層のUnitTestで直接確認済み
    (test_user_service.py::test_deactivating_last_active_admin_raises_last_admin_protected)。
    """
    _login_admin(client)
    client.post(
        "/api/users",
        json={"employee_id": "admin2", "name": "管理者2", "password": "Password1!", "role": "admin"},
    )

    response = client.put(
        "/api/users/admin2",
        json={"name": "管理者2", "password": None, "role": "admin", "is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
