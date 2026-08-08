"""A010 — セキュリティの横断確認(V-N-03〜06)。

docs/P009-acceptance-direction/A010-security-checks.md
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from tests.acceptance.base import PASSWORD, AcceptanceTestCase, day
from tests.acceptance.support import ServerProcess


class A010SecurityTest(AcceptanceTestCase):
    def setUp(self):
        super().setUp()
        rooms = self.room_ids()
        self.room_a = rooms["会議室A"]
        self.room_b = rooms["会議室B"]
        self.admin = self.new_client()
        self.assertEqual(self.admin.login("admin001").status, 200)
        self.user = self.new_client()
        self.assertEqual(self.user.login("user001").status, 200)
        res = self.user.post(
            "/api/reservations", self.reservation_body(self.room_a, day(1), "10:00", "11:00")
        )
        self.assertEqual(res.status, 201, res.text)
        self.reservation_id = res.json()["reservation"]["reservation_id"]

    # ---- 手順1 ----
    def test_step1_password_hashes(self):
        rows = list(self.db().execute("SELECT user_id, password_hash FROM users"))
        self.assertGreaterEqual(len(rows), 4)
        hashes = set()
        for row in rows:
            self.assertTrue(
                row["password_hash"].startswith("scrypt$"),
                f"{row['user_id']}: {row['password_hash'][:20]}",
            )
            self.assertNotIn(PASSWORD, row["password_hash"], row["user_id"])
            hashes.add(row["password_hash"])
        # 同じパスワードでもユーザーごとに値が異なる(ソルトが個別)
        same_password_users = [r["password_hash"] for r in rows if r["user_id"].startswith("user")]
        self.assertEqual(
            len(set(same_password_users)),
            len(same_password_users),
            "同じパスワードのユーザーでハッシュが重複している",
        )

    # ---- 手順2・手順7 ----
    def test_step2_no_password_in_responses(self):
        responses = []
        admin, user = self.admin, self.user
        calls = [
            ("GET /api/me", user.get("/api/me")),
            ("GET /api/rooms", user.get("/api/rooms")),
            ("GET /api/rooms?include_inactive", admin.get("/api/rooms?include_inactive=true")),
            ("GET /api/users?scope=management", admin.get("/api/users?scope=management")),
            (
                "GET /api/users?scope=attendee_candidates",
                user.get("/api/users?scope=attendee_candidates"),
            ),
            (
                "POST /api/users",
                admin.post(
                    "/api/users",
                    {
                        "user_id": "sec00001",
                        "name": "検査 太郎",
                        "role": "general",
                        "password": PASSWORD,
                    },
                ),
            ),
            (
                "PUT /api/users/sec00001",
                admin.put(
                    "/api/users/sec00001",
                    {"name": "検査 太郎", "role": "general", "is_active": True, "password": PASSWORD},
                ),
            ),
            (
                "POST /api/rooms",
                admin.post("/api/rooms", {"name": "会議室Z", "capacity": 3}),
            ),
            (
                "PUT /api/rooms",
                admin.put(f"/api/rooms/{self.room_b}", {"name": "会議室B", "capacity": 4}),
            ),
            (
                "GET /api/reservations",
                user.get(f"/api/reservations?date_from={day(0)}&date_to={day(6)}"),
            ),
            ("GET /api/reservations/mine", user.get("/api/reservations/mine?period=upcoming")),
            (
                "GET /api/reservations/{id}",
                user.get(f"/api/reservations/{self.reservation_id}"),
            ),
            (
                "PUT /api/reservations/{id}",
                user.put(
                    f"/api/reservations/{self.reservation_id}",
                    self.reservation_body(self.room_a, day(1), "10:00", "11:00", title="更新後"),
                ),
            ),
            ("POST /api/auth/login", self.new_client().login("user002")),
        ]
        for label, res in calls:
            with self.subTest(api=label):
                self.assertLess(res.status, 400, f"{label}: {res.status} {res.text}")
                self.assertNotIn("password", res.text.lower(), f"{label} の本文にpassword")
                responses.append((label, res))

        # 手順7: attendee_candidates に role が含まれない
        users = self.user.get("/api/users?scope=attendee_candidates").json()["users"]
        self.assertTrue(users)
        for entry in users:
            self.assertEqual(sorted(entry.keys()), ["name", "user_id"], entry)

    # ---- 手順3 ----
    def test_step3_cookie_attributes(self):
        res = self.new_client().login("user001")
        cookie_header = "; ".join(res.set_cookies)
        for attribute in ("HttpOnly", "SameSite=Lax", "Secure", "Path=/"):
            self.assertIn(attribute, cookie_header, cookie_header)

    # ---- 手順4 ----
    def test_step4_admin_apis_forbidden_for_general_user(self):
        calls = [
            ("POST /api/rooms", lambda: self.user.post("/api/rooms", {"name": "X", "capacity": 2})),
            (
                "PUT /api/rooms/{id}",
                lambda: self.user.put(f"/api/rooms/{self.room_b}", {"name": "会議室B", "capacity": 4}),
            ),
            ("DELETE /api/rooms/{id}", lambda: self.user.delete(f"/api/rooms/{self.room_b}")),
            ("GET /api/users?scope=management", lambda: self.user.get("/api/users?scope=management")),
            (
                "POST /api/users",
                lambda: self.user.post(
                    "/api/users",
                    {"user_id": "nope0001", "name": "駄目", "role": "general", "password": PASSWORD},
                ),
            ),
            (
                "PUT /api/users/{id}",
                lambda: self.user.put(
                    "/api/users/user002", {"name": "鈴木 花子", "role": "general", "is_active": True}
                ),
            ),
            ("DELETE /api/users/{id}", lambda: self.user.delete("/api/users/user002")),
            (
                "GET /api/rooms?include_inactive=true",
                lambda: self.user.get("/api/rooms?include_inactive=true"),
            ),
        ]
        for label, call in calls:
            with self.subTest(api=label):
                res = call()
                self.assertEqual(res.status, 403, f"{label}: {res.status} {res.text}")
                self.assertEqual(res.error_code(), "FORBIDDEN", label)

    # ---- 手順6 ----
    def test_step6_logs_have_no_secrets(self):
        self.new_client().login("user001")
        self.user.get("/api/me")
        log = self.server_log()
        self.assertNotIn(PASSWORD, log, "ログに平文パスワードがある")
        self.assertNotIn("password", log.lower(), "ログに password の文字列がある")
        sid_value = self.user.cookie.split("=", 1)[1]
        self.assertTrue(sid_value)
        self.assertNotIn(sid_value, log, "ログにセッションIDの値がある")
        records = self.log_records()
        self.assertTrue(records, "アクセスログが1行もない")
        for record in records:
            self.assertNotIn("sid", record, record)


class A010InternalErrorTest(unittest.TestCase):
    """手順5・手順6(5xx側): 意図的に500を発生させ、本文とログを検査する。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = os.path.join(self._tmp.name, "app.db")
        self.log_path = os.path.join(self._tmp.name, "server.log")
        self.server = ServerProcess(self.db_path, log_path=self.log_path)
        self.server.start()
        self.addCleanup(self.server.stop)

    def test_internal_error_leaks_nothing(self):
        client = self.server.client()
        self.assertEqual(client.login("admin001").status, 200)
        # DBファイルを壊して内部例外を誘発する(SQLiteが "file is not a database" を投げる)
        for suffix in ("-wal", "-shm"):
            path = self.db_path + suffix
            if os.path.exists(path):
                os.remove(path)
        with open(self.db_path, "wb") as handle:
            handle.write(b"this is not a sqlite database" * 64)

        res = client.get("/api/rooms")
        self.assertEqual(res.status, 500, f"500 を誘発できなかった: {res.status} {res.text}")
        payload = res.json()
        self.assertEqual(payload["error"]["code"], "INTERNAL_ERROR", payload)
        body = res.text
        for leak in ("Traceback", "SELECT", "sqlite3", ".py", "/tmp/", "File \""):
            self.assertNotIn(leak, body, f"応答本文に内部情報 '{leak}' が漏れている: {body}")
        self.assertEqual(
            sorted(payload["error"].keys()), ["code", "message"], payload["error"]
        )

        # 手順6: 5xxのログには stack が含まれる(サーバー側には残す)
        with open(self.log_path, "r", encoding="utf-8", errors="replace") as handle:
            records = [
                json.loads(line)
                for line in handle.read().splitlines()
                if line.strip().startswith("{")
            ]
        errors = [r for r in records if r["status"] >= 500]
        self.assertTrue(errors, "5xxのアクセスログがない")
        self.assertIn("stack", errors[-1], errors[-1])
        self.assertEqual(errors[-1]["level"], "ERROR")


if __name__ == "__main__":
    unittest.main()
