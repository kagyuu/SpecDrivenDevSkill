from tests.api.conftest import insert_room


def _login(client, employee_id="user001"):
    resp = client.post("/api/auth/login", json={"employee_id": employee_id, "password": "TestPassw0rd!"})
    assert resp.status_code == 200


def test_post_reservation_success(client, db_path):
    room_id = insert_room(db_path)
    _login(client)

    resp = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例MTG",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "定例MTG"
    assert body["room_id"] == room_id


def test_post_reservation_invalid_time_range(client, db_path):
    room_id = insert_room(db_path)
    _login(client)

    resp = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "10:00", "title": "会議"},
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "INVALID_TIME_RANGE"


def test_post_reservation_capacity_exceeded(client, db_path):
    room_id = insert_room(db_path, capacity=5)
    _login(client)

    resp = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "会議",
            "expected_attendees": 6,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "CAPACITY_EXCEEDED"


def test_post_reservation_conflict(client, db_path):
    room_id = insert_room(db_path)
    _login(client)
    client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "会議1"},
    )

    resp = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:30", "end_time": "11:30", "title": "会議2"},
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "RESERVATION_CONFLICT"


def test_post_reservation_back_to_back_is_not_conflict(client, db_path):
    room_id = insert_room(db_path)
    _login(client)
    client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "会議1"},
    )

    resp = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "11:00", "end_time": "12:00", "title": "会議2"},
    )
    assert resp.status_code == 201


def test_get_my_reservations_upcoming_filter(client, db_path):
    room_id = insert_room(db_path)
    _login(client)
    client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2099-01-01", "start_time": "10:00", "end_time": "11:00", "title": "未来の会議"},
    )

    resp = client.get("/api/reservations/mine", params={"period": "upcoming"})
    assert resp.status_code == 200
    titles = [r["title"] for r in resp.json()]
    assert "未来の会議" in titles


def test_put_reservation_owner_can_update(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "旧件名"},
    ).json()

    resp = client.put(
        f"/api/reservations/{created['id']}",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "新件名"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "新件名"


def test_put_reservation_non_owner_forbidden(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "件名"},
    ).json()

    client.post("/api/auth/logout")
    _login(client, "user002")
    resp = client.put(
        f"/api/reservations/{created['id']}",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "改ざん"},
    )
    assert resp.status_code == 403
    assert resp.json()["error_code"] == "FORBIDDEN"


def test_put_reservation_admin_can_edit_others(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "件名"},
    ).json()

    client.post("/api/auth/logout")
    _login(client, "admin001")
    resp = client.put(
        f"/api/reservations/{created['id']}",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "管理者による修正"},
    )
    assert resp.status_code == 200


def test_put_reservation_missing_returns_404(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    resp = client.put(
        "/api/reservations/9999",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "件名"},
    )
    assert resp.status_code == 404


def test_put_reservation_conflicting_time_returns_409(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "既存予約"},
    )
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "13:00", "end_time": "14:00", "title": "移動対象"},
    ).json()

    resp = client.put(
        f"/api/reservations/{created['id']}",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:30", "end_time": "11:30", "title": "移動対象"},
    )
    assert resp.status_code == 409


def test_put_reservation_same_slot_does_not_conflict_with_itself(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "旧"},
    ).json()

    resp = client.put(
        f"/api/reservations/{created['id']}",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "新"},
    )
    assert resp.status_code == 200


def test_delete_reservation_owner_can_delete(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "削除対象"},
    ).json()

    resp = client.delete(f"/api/reservations/{created['id']}")
    assert resp.status_code == 204

    get_resp = client.get(f"/api/reservations/{created['id']}")
    assert get_resp.status_code == 404


# ※CR-001により追加。閲覧範囲のマスキング(docs/P008-test-direction/T010-*.md、
# docs/P003-backend-spec.md 「internal_memo のマスキング」参照)。


def test_post_reservation_returns_internal_memo_to_owner(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")

    resp = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例MTG",
            "internal_memo": "非公開メモ",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["internal_memo"] == "非公開メモ"


def test_get_reservation_owner_sees_internal_memo(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例MTG",
            "internal_memo": "非公開メモ",
        },
    ).json()

    resp = client.get(f"/api/reservations/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["internal_memo"] == "非公開メモ"


def test_get_reservation_admin_sees_internal_memo(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例MTG",
            "internal_memo": "非公開メモ",
        },
    ).json()

    client.post("/api/auth/logout")
    _login(client, "admin001")
    resp = client.get(f"/api/reservations/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["internal_memo"] == "非公開メモ"


def test_get_reservation_non_owner_non_admin_gets_null_internal_memo(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例MTG",
            "internal_memo": "非公開メモ",
        },
    ).json()

    client.post("/api/auth/logout")
    _login(client, "user002")
    resp = client.get(f"/api/reservations/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["internal_memo"] is None


def test_list_reservations_non_owner_non_admin_gets_null_internal_memo(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例MTG",
            "internal_memo": "非公開メモ",
        },
    )

    client.post("/api/auth/logout")
    _login(client, "user002")
    resp = client.get(
        "/api/reservations", params={"date_from": "2026-08-12", "date_to": "2026-08-12"}
    )
    assert resp.status_code == 200
    bodies = resp.json()
    assert len(bodies) == 1
    assert bodies[0]["internal_memo"] is None


def test_put_reservation_updates_internal_memo_for_owner(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "旧件名",
            "internal_memo": "旧メモ",
        },
    ).json()

    resp = client.put(
        f"/api/reservations/{created['id']}",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "新件名",
            "internal_memo": "新メモ",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["internal_memo"] == "新メモ"


def test_post_reservation_internal_memo_over_300_chars_is_rejected(client, db_path):
    # ※注意: この欠陥は既存(CR-001と無関係)。docs/P002-frontend-spec.md §2が定める
    # カスタムエラー形式({"error_code": "VALIDATION_ERROR", ...}, HTTP 400)ではなく、
    # FastAPI/Pydantic既定のバリデーションエラー形式({"detail": [...]}, HTTP 422)が
    # 実際に返る(docs/P007-impl-direction.md 未解決事項に記録済み、CR-001のスコープ外の
    # ため本CRでは修正しない)。ここでは実際の挙動をそのままテストする。
    room_id = insert_room(db_path)
    _login(client, "user001")

    resp = client.post(
        "/api/reservations",
        json={
            "room_id": room_id,
            "date": "2026-08-12",
            "start_time": "10:00",
            "end_time": "11:00",
            "title": "定例MTG",
            "internal_memo": "あ" * 301,
        },
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()


def test_delete_reservation_non_owner_forbidden(client, db_path):
    room_id = insert_room(db_path)
    _login(client, "user001")
    created = client.post(
        "/api/reservations",
        json={"room_id": room_id, "date": "2026-08-12", "start_time": "10:00", "end_time": "11:00", "title": "件名"},
    ).json()

    client.post("/api/auth/logout")
    _login(client, "user002")
    resp = client.delete(f"/api/reservations/{created['id']}")
    assert resp.status_code == 403
