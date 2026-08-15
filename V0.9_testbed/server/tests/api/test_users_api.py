def _login(client, employee_id):
    resp = client.post("/api/auth/login", json={"employee_id": employee_id, "password": "TestPassw0rd!"})
    assert resp.status_code == 200


def test_post_user_as_admin_succeeds_and_hides_password(client):
    _login(client, "admin001")
    resp = client.post(
        "/api/users",
        json={"employee_id": "user099", "name": "新人太郎", "role": "general", "initial_password": "Passw0rd1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "password_hash" not in body
    assert "initial_password" not in body


def test_post_user_duplicate_employee_id_returns_409(client):
    _login(client, "admin001")
    resp = client.post(
        "/api/users",
        json={"employee_id": "user001", "name": "重複太郎", "role": "general", "initial_password": "Passw0rd1"},
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "DUPLICATE_EMPLOYEE_ID"


def test_delete_user_self_deactivation_forbidden(client):
    _login(client, "admin001")
    me = client.get("/api/me").json()

    resp = client.delete(f"/api/users/{me['id']}")
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "CANNOT_DEACTIVATE_SELF"


def test_delete_user_other_user_succeeds(client):
    _login(client, "admin001")
    created = client.post(
        "/api/users",
        json={"employee_id": "user099", "name": "新人太郎", "role": "general", "initial_password": "Passw0rd1"},
    ).json()

    resp = client.delete(f"/api/users/{created['id']}")
    assert resp.status_code == 204


def test_users_endpoints_forbidden_for_general_user(client):
    _login(client, "user001")
    assert client.get("/api/users").status_code == 403
    assert client.post(
        "/api/users",
        json={"employee_id": "x", "name": "x", "role": "general", "initial_password": "Passw0rd1"},
    ).status_code == 403
