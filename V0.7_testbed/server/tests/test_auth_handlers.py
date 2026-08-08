"""U001-T4 単体テスト — 認証API3本と認可ヘルパ(P002 5.4 / P003 4.3 / 6.1)。"""

import tempfile
import types
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from meeting_room import auth, db, main, security
from meeting_room.errors import ApiError
from meeting_room.repositories import sessions_repo, users_repo

NOW = "2026-08-05T00:00:00Z"


class AuthHandlersTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        self.app = main.create_app(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)
        self._add_user("user001", "山田 太郎", "general", True)
        self._add_user("adminx001", "管理 太郎", "admin", True)
        self._add_user("user003", "無効 三郎", "general", False)
        # `Secure` 属性付きCookieを保持・送信させるため https スキームで駆動する
        self.client = TestClient(self.app, base_url="https://testserver")
        self.addCleanup(self.client.close)

    def _add_user(self, user_id, name, role, is_active, password="Passw0rd!23"):
        with db.transaction(self.conn):
            users_repo.insert(
                self.conn, user_id, name, security.hash_password(password), role, is_active, NOW
            )

    def _login(self, user_id="user001", password="Passw0rd!23"):
        return self.client.post("/api/auth/login", json={"user_id": user_id, "password": password})


class LoginApiTest(AuthHandlersTestBase):
    # 正常系: API-01 の成功応答とCookie属性(P002 5.4)
    def test_login_success_sets_cookie(self):
        res = self._login()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.json(), {"user": {"user_id": "user001", "name": "山田 太郎", "role": "general"}}
        )
        set_cookie = res.headers["set-cookie"]
        for attr in ("sid=", "HttpOnly", "SameSite=Lax", "Secure", "Path=/"):
            self.assertIn(attr, set_cookie)
        self.assertEqual(sessions_repo.count(self.conn), 1)

    # 正常系: API-03 はログイン中ユーザーを返す
    def test_me_returns_user(self):
        self._login()
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(set(res.json()["user"].keys()), {"user_id", "name", "role"})
        self.assertEqual(res.json()["user"]["user_id"], "user001")

    # 正常系: API-02 の後は同じCookieで 401
    def test_logout_then_me_is_401(self):
        self._login()
        res = self.client.post("/api/auth/logout")
        self.assertEqual(res.status_code, 204)
        self.assertIn("Max-Age=0", res.headers["set-cookie"])
        self.assertEqual(sessions_repo.count(self.conn), 0)
        again = self.client.get("/api/me")
        self.assertEqual(again.status_code, 401)
        self.assertEqual(again.json()["error"]["code"], "UNAUTHENTICATED")

    # 異常系: user_id の形式違反は 400 VALIDATION_ERROR(日本語)
    def test_user_id_validation(self):
        for bad in ("abc", "a" * 21, "user_001"):
            with self.subTest(user_id=bad):
                res = self._login(user_id=bad)
                self.assertEqual(res.status_code, 400)
                body = res.json()["error"]
                self.assertEqual(body["code"], "VALIDATION_ERROR")
                self.assertEqual(body["details"][0]["field"], "user_id")
                self.assertEqual(
                    body["details"][0]["message"], "ユーザーIDは半角英数字4〜20文字で入力してください。"
                )

    # 異常系: パスワードの文字数違反は 400
    def test_password_length_validation(self):
        for bad in ("a" * 7, "a" * 65):
            with self.subTest(length=len(bad)):
                res = self._login(password=bad)
                self.assertEqual(res.status_code, 400)
                detail = res.json()["error"]["details"][0]
                self.assertEqual(detail["field"], "password")
                self.assertEqual(detail["message"], "パスワードは8〜64文字で入力してください。")

    # 異常系: 未入力は必須メッセージ
    def test_missing_fields(self):
        res = self.client.post("/api/auth/login", json={})
        self.assertEqual(res.status_code, 400)
        messages = {d["field"]: d["message"] for d in res.json()["error"]["details"]}
        self.assertEqual(messages["user_id"], "ユーザーIDを入力してください。")
        self.assertEqual(messages["password"], "パスワードを入力してください。")

    # 異常系: 存在しないID・誤パスワード・無効ユーザーは同一の 401 AUTH_FAILED
    def test_auth_failures_are_indistinguishable(self):
        responses = [
            self._login(user_id="nosuchuser"),
            self._login(password="WrongPass123"),
            self._login(user_id="user003"),
        ]
        bodies = set()
        for res in responses:
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.json()["error"]["code"], "AUTH_FAILED")
            bodies.add(res.json()["error"]["message"])
        self.assertEqual(bodies, {"ユーザーIDまたはパスワードが正しくありません。"})

    # 異常系: Cookieなしの /api/me は 401 UNAUTHENTICATED
    def test_me_without_cookie(self):
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["error"]["code"], "UNAUTHENTICATED")

    # 異常系: 無操作タイムアウトを超えたセッションは 401 になり行が消える
    def test_idle_expired_session_is_rejected(self):
        self._login()
        from meeting_room.services import auth_service

        nine_hours_ago = auth_service.shift(security.now_utc(), -9 * 3600)
        with db.transaction(self.conn):
            self.conn.execute("UPDATE sessions SET last_accessed_at = ?", (nine_hours_ago,))
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(sessions_repo.count(self.conn), 0)

    # 異常系: 絶対有効期限切れのセッションは 401
    def test_absolutely_expired_session_is_rejected(self):
        self._login()
        with db.transaction(self.conn):
            self.conn.execute("UPDATE sessions SET expires_at = ?", ("2020-01-01T00:00:00Z",))
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 401)


class _StubRequest:
    """`auth.require_*` を直接検証するための最小限のリクエスト。"""

    def __init__(self, db_path: str, sid: str | None):
        self.app = types.SimpleNamespace(state=types.SimpleNamespace(db_path=db_path))
        self.cookies = {"sid": sid} if sid else {}
        self.state = types.SimpleNamespace()


class RequireHelpersTest(AuthHandlersTestBase):
    def _session_for(self, user_id):
        from meeting_room.services import auth_service

        with db.transaction(self.conn):
            session_id, _ = auth_service.login(self.conn, user_id, "Passw0rd!23")
        return session_id

    # 正常系: require_login は request.state.user を設定する
    def test_require_login_sets_state_user(self):
        request = _StubRequest(self.db_path, self._session_for("user001"))
        user = auth.require_login(request)
        self.assertEqual(user["user_id"], "user001")
        self.assertEqual(request.state.user["user_id"], "user001")

    # 正常系: 管理者は require_admin を通る
    def test_require_admin_allows_admin(self):
        request = _StubRequest(self.db_path, self._session_for("adminx001"))
        self.assertEqual(auth.require_admin(request)["role"], "admin")

    # 異常系: 一般ユーザーの require_admin は 403 FORBIDDEN
    def test_require_admin_rejects_general_user(self):
        request = _StubRequest(self.db_path, self._session_for("user001"))
        with self.assertRaises(ApiError) as ctx:
            auth.require_admin(request)
        self.assertEqual(ctx.exception.status, 403)
        self.assertEqual(ctx.exception.code, "FORBIDDEN")

    # 異常系: 未認証は 401 UNAUTHENTICATED
    def test_require_login_without_cookie(self):
        with self.assertRaises(ApiError) as ctx:
            auth.require_login(_StubRequest(self.db_path, None))
        self.assertEqual(ctx.exception.status, 401)
        self.assertEqual(ctx.exception.code, "UNAUTHENTICATED")

    # 異常系: 予約者でも管理者でもなければ 403
    def test_require_owner_or_admin(self):
        request = _StubRequest(self.db_path, self._session_for("user001"))
        self.assertEqual(auth.require_owner_or_admin(request, "user001")["user_id"], "user001")
        other = _StubRequest(self.db_path, self._session_for("user001"))
        with self.assertRaises(ApiError) as ctx:
            auth.require_owner_or_admin(other, "someoneelse")
        self.assertEqual(ctx.exception.status, 403)
        # 管理者は他人の予約でも通る
        admin_request = _StubRequest(self.db_path, self._session_for("adminx001"))
        self.assertEqual(
            auth.require_owner_or_admin(admin_request, "user001")["user_id"], "adminx001"
        )


if __name__ == "__main__":
    unittest.main()


class AccessLogTest(AuthHandlersTestBase):
    """P003 4.4 — 認証済みリクエストのログに `user_id` が載り、`sid` は載らないこと。"""

    def test_log_contains_user_id_and_no_sid(self):
        self._login()
        with self.assertLogs("meeting_room.access", level="INFO") as captured:
            self.client.get("/api/me")
        import json as _json

        record = _json.loads(captured.output[-1].split(":", 2)[-1])
        self.assertEqual(record["user_id"], "user001")
        self.assertEqual(record["path"], "/api/me")
        self.assertNotIn("sid", captured.output[-1])
