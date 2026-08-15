def test_login_success_then_me(client):
    resp = client.post("/api/auth/login", json={"employee_id": "user001", "password": "TestPassw0rd!"})
    assert resp.status_code == 200
    assert resp.cookies.get("session_id") is not None

    me_resp = client.get("/api/me")
    assert me_resp.status_code == 200
    body = me_resp.json()
    assert body["employee_id"] == "user001"
    assert body["role"] == "general"


def test_login_wrong_password_returns_auth_failed(client):
    resp = client.post("/api/auth/login", json={"employee_id": "user001", "password": "WrongPassword1"})
    assert resp.status_code == 401
    body = resp.json()
    assert body["error_code"] == "AUTH_FAILED"
    assert body["message"] == "社員IDまたはパスワードが正しくありません"


def test_login_unknown_employee_id_same_message(client):
    resp = client.post("/api/auth/login", json={"employee_id": "no_such_user", "password": "TestPassw0rd!"})
    assert resp.status_code == 401
    assert resp.json()["message"] == "社員IDまたはパスワードが正しくありません"


def test_me_without_cookie_is_unauthenticated(client):
    resp = client.get("/api/me")
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "UNAUTHENTICATED"


def test_logout_then_me_is_unauthenticated(client):
    client.post("/api/auth/login", json={"employee_id": "user001", "password": "TestPassw0rd!"})
    logout_resp = client.post("/api/auth/logout")
    assert logout_resp.status_code == 204

    me_resp = client.get("/api/me")
    assert me_resp.status_code == 401
