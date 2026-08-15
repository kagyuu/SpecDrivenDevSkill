"""U001結合確認用の薄いスモークテスト。docs/P007-impl-direction/U001-foundation-and-auth.md U001-T6。

docs/P002-frontend-spec.md §7.1(ログイン〜カレンダー初期表示シーケンス)のうち、
本スプリント範囲であるログイン〜ルーム一覧取得の部分を一気通貫で確認する。
"""


def test_login_me_rooms_flow(client):
    login_resp = client.post(
        "/api/auth/login", json={"employee_id": "user001", "password": "TestPassw0rd!"}
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["user"]["employee_id"] == "user001"

    me_resp = client.get("/api/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["role"] == "general"

    rooms_resp = client.get("/api/rooms")
    assert rooms_resp.status_code == 200
    assert rooms_resp.json() == []
