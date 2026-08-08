"""U002-T3 単体テスト — ユーザーAPI(API-08〜API-11。P002 5.6)。"""

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from meeting_room import db, main, security
from meeting_room.repositories import users_repo

NOW = "2026-08-05T00:00:00Z"
NEW_USER = {"user_id": "user900", "name": "新規 太郎", "role": "general", "password": "Passw0rd!23"}


class UserApiTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = str(Path(self._tmp.name) / "app.db")
        self.app = main.create_app(db_path=self.db_path)
        self.conn = db.connect(self.db_path)
        self.addCleanup(self.conn.close)
        self._add("user001", "山田 太郎", "general", True)
        self._add("user002", "鈴木 花子", "general", True)
        self._add("user003", "無効 三郎", "general", False)
        # `admin001` は起動時のシードで作成済み(P003 3.6)。追加しない。
        self.client = TestClient(self.app, base_url="https://testserver")
        self.addCleanup(self.client.close)

    def _add(self, user_id, name, role, is_active):
        with db.transaction(self.conn):
            users_repo.insert(
                self.conn, user_id, name, security.hash_password("Passw0rd!23"), role,
                is_active, NOW,
            )

    def login(self, user_id, password="Passw0rd!23"):
        self.client.cookies.clear()
        res = self.client.post("/api/auth/login", json={"user_id": user_id, "password": password})
        return res


class UserApiTest(UserApiTestBase):
    # 正常系: 登録は 201。レスポンスにパスワードを含めない
    def test_create_user(self):
        self.login("admin001")
        res = self.client.post("/api/users", json=NEW_USER)
        self.assertEqual(res.status_code, 201)
        user = res.json()["user"]
        self.assertEqual(user["user_id"], "user900")
        self.assertNotIn("password", user)
        self.assertNotIn("password_hash", user)
        self.assertTrue(
            users_repo.find_by_id_with_hash(self.conn, "user900")["password_hash"].startswith("scrypt$")
        )
        # 登録したユーザーでログインできる
        self.assertEqual(self.login("user900").status_code, 200)

    # 正常系: 更新で氏名・権限が変わる
    def test_update_user(self):
        self.login("admin001")
        res = self.client.put(
            "/api/users/user001", json={"name": "山田 次郎", "role": "admin", "is_active": True}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user"]["name"], "山田 次郎")
        self.assertEqual(res.json()["user"]["role"], "admin")

    # 正常系: password を指定した更新後、新しいパスワードでログインできる
    def test_update_password(self):
        self.login("admin001")
        res = self.client.put(
            "/api/users/user001",
            json={"name": "山田 太郎", "role": "general", "is_active": True, "password": "NewPassw0rd!"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.login("user001", "NewPassw0rd!").status_code, 200)

    # 正常系: 無効化は 204 で当該ユーザーのセッションが消える
    def test_deactivate_user_kills_session(self):
        self.login("user001")
        user_cookies = dict(self.client.cookies)
        self.login("admin001")
        self.assertEqual(self.client.delete("/api/users/user001").status_code, 204)
        self.client.cookies.clear()
        for name, value in user_cookies.items():
            self.client.cookies.set(name, value)
        self.assertEqual(self.client.get("/api/me").status_code, 401)

    # 正常系: scope=attendee_candidates は一般ユーザーでも呼べ、キーが2つだけ
    def test_attendee_candidates_scope(self):
        self.login("user001")
        res = self.client.get("/api/users?scope=attendee_candidates")
        self.assertEqual(res.status_code, 200)
        users = res.json()["users"]
        self.assertEqual([u["user_id"] for u in users], ["admin001", "user001", "user002"])
        for user in users:
            self.assertEqual(set(user.keys()), {"user_id", "name"})

    # 異常系: 入力値の検証
    def test_validation_errors(self):
        self.login("admin001")
        cases = [
            ({**NEW_USER, "user_id": "abc"}, "user_id"),
            ({**NEW_USER, "user_id": "user_900"}, "user_id"),
            ({**NEW_USER, "name": "あ" * 51}, "name"),
            ({**NEW_USER, "role": "owner"}, "role"),
            ({**NEW_USER, "password": "short"}, "password"),
        ]
        for body, field in cases:
            with self.subTest(field=field):
                res = self.client.post("/api/users", json=body)
                self.assertEqual(res.status_code, 400)
                self.assertEqual(res.json()["error"]["details"][0]["field"], field)

    # 異常系: 既存ID(有効・無効)は 409 DUPLICATE_KEY
    def test_duplicate_user_id(self):
        self.login("admin001")
        for existing in ("user001", "user003"):
            with self.subTest(user_id=existing):
                res = self.client.post("/api/users", json={**NEW_USER, "user_id": existing})
                self.assertEqual(res.status_code, 409)
                self.assertEqual(res.json()["error"]["code"], "DUPLICATE_KEY")

    # 異常系: 最後の有効な管理者の降格・無効化、自分自身の無効化は 409
    def test_constraint_violations(self):
        self.login("admin001")
        res = self.client.put(
            "/api/users/admin001", json={"name": "初期管理者", "role": "general", "is_active": True}
        )
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["code"], "CONSTRAINT_VIOLATION")
        res = self.client.delete("/api/users/admin001")
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.json()["error"]["message"], "自分自身を無効化することはできません。")

    # 異常系: 一般ユーザーの管理操作は 403
    def test_general_user_is_forbidden(self):
        self.login("user001")
        for res in (
            self.client.get("/api/users"),
            self.client.get("/api/users?scope=management"),
            self.client.post("/api/users", json=NEW_USER),
            self.client.put("/api/users/user002", json={"name": "x", "role": "general", "is_active": True}),
            self.client.delete("/api/users/user002"),
        ):
            self.assertEqual(res.status_code, 403)
            self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    # 異常系: 存在しない user_id は 404、無効ユーザーの再削除は 204
    def test_missing_and_idempotent(self):
        self.login("admin001")
        self.assertEqual(
            self.client.put("/api/users/nosuchuser", json={"name": "x", "role": "general", "is_active": True}).status_code,
            404,
        )
        self.assertEqual(self.client.delete("/api/users/nosuchuser").status_code, 404)
        self.assertEqual(self.client.delete("/api/users/user003").status_code, 204)

    # 正常系: 一覧は user_id 昇順で無効ユーザーも含む(既定 include_inactive=true)
    def test_list_users_default_includes_inactive(self):
        self.login("admin001")
        res = self.client.get("/api/users")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            [u["user_id"] for u in res.json()["users"]],
            ["admin001", "user001", "user002", "user003"],
        )
        res = self.client.get("/api/users?include_inactive=false")
        self.assertEqual(len(res.json()["users"]), 3)


if __name__ == "__main__":
    unittest.main()
