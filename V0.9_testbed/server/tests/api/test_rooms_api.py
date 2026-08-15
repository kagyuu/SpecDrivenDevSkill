def _login(client, employee_id):
    resp = client.post("/api/auth/login", json={"employee_id": employee_id, "password": "TestPassw0rd!"})
    assert resp.status_code == 200


def test_get_rooms_requires_auth(client):
    resp = client.get("/api/rooms")
    assert resp.status_code == 401


def test_get_rooms_returns_empty_list_when_none_seeded(client):
    _login(client, "user001")
    resp = client.get("/api/rooms")
    assert resp.status_code == 200
    assert resp.json() == []


def test_post_room_as_admin_succeeds(client):
    _login(client, "admin001")
    resp = client.post("/api/rooms", json={"name": "会議室A", "capacity": 10})
    assert resp.status_code == 201
    assert resp.json()["name"] == "会議室A"


def test_post_room_as_general_user_forbidden(client):
    _login(client, "user001")
    resp = client.post("/api/rooms", json={"name": "会議室A", "capacity": 10})
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"


def test_delete_room_deactivates_and_hides_from_default_list_but_shows_with_include_inactive(client):
    _login(client, "admin001")
    room = client.post("/api/rooms", json={"name": "会議室B", "capacity": 4}).json()

    delete_resp = client.delete(f"/api/rooms/{room['id']}")
    assert delete_resp.status_code == 204

    default_list = client.get("/api/rooms").json()
    assert room["id"] not in [r["id"] for r in default_list]

    with_inactive = client.get("/api/rooms", params={"include_inactive": "true"}).json()
    assert room["id"] in [r["id"] for r in with_inactive]


def test_get_rooms_include_inactive_ignored_for_general_user(client):
    _login(client, "admin001")
    room = client.post("/api/rooms", json={"name": "会議室C", "capacity": 4}).json()
    client.delete(f"/api/rooms/{room['id']}")
    client.post("/api/auth/logout")

    _login(client, "user001")
    resp = client.get("/api/rooms", params={"include_inactive": "true"})
    assert resp.status_code == 200
    assert room["id"] not in [r["id"] for r in resp.json()]


def test_put_room_updates_fields(client):
    _login(client, "admin001")
    room = client.post("/api/rooms", json={"name": "会議室D", "capacity": 4}).json()

    resp = client.put(f"/api/rooms/{room['id']}", json={"name": "会議室D(改)", "capacity": 8})
    assert resp.status_code == 200
    assert resp.json()["capacity"] == 8
