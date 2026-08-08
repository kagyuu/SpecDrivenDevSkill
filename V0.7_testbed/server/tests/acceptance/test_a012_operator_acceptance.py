"""A012 — 運用者視点の受け入れシナリオ。

docs/P009-acceptance-direction/A012-operator-acceptance.md
"""

from __future__ import annotations

import json
import os
import signal
import tempfile
import unittest
from datetime import datetime, timedelta

from tests.acceptance.support import ServerProcess

ADMIN_ID = "ops0001"
ADMIN_PASSWORD = "OpsPassw0rd!"
NEW_USER_ID = "ops1002"
NEW_USER_PASSWORD = "Passw0rd!23"
REQUIRED_LOG_FIELDS = ("ts", "level", "method", "path", "status", "duration_ms", "user_id")


def _date(offset: int) -> str:
    return (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")


class A012OperatorAcceptanceTest(unittest.TestCase):
    def setUp(self):
        # 事前準備1: DBファイルを削除する(まっさらな状態からの初期セットアップ)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = os.path.join(self._tmp.name, "app.db")
        # 事前準備2: サーバーの標準出力をファイルに退避する
        self.log_path = os.path.join(self._tmp.name, "server.log")
        self.server = None
        self.addCleanup(self._stop)

    def _stop(self):
        if self.server is not None:
            rc = self.server.stop(signal.SIGTERM)
            self.server = None
            return rc
        return None

    def _start(self):
        self.server = ServerProcess(
            self.db_path,
            env_extra={
                "INITIAL_ADMIN_ID": ADMIN_ID,
                "INITIAL_ADMIN_PASSWORD": ADMIN_PASSWORD,
            },
            log_path=self.log_path,
        )
        self.server.start()
        return self.server

    def _log_records(self):
        with open(self.log_path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        records = []
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith("{"):
                continue
            records.append(json.loads(stripped))  # JSONとしてパースできること(手順5)
        return records, lines

    def test_operator_acceptance(self):
        # 手順1: 環境変数を指定して起動 → ops0001 が作られる(既定値 admin001 ではない)
        server = self._start()
        from meeting_room import db as db_module

        conn = db_module.connect(self.db_path)
        try:
            admins = [
                row["user_id"]
                for row in conn.execute("SELECT user_id FROM users WHERE role = 'admin'")
            ]
        finally:
            conn.close()
        self.assertEqual(admins, [ADMIN_ID], f"初期管理者が環境変数どおりでない: {admins}")

        # 手順2: 初期管理者でログイン → 200
        admin = server.client()
        res = admin.login(ADMIN_ID, ADMIN_PASSWORD)
        self.assertEqual(res.status, 200, res.text)

        # 手順3: 会議室1件、ユーザー1件を登録する(初期セットアップ相当)
        res = admin.post(
            "/api/rooms", {"name": "第1会議室", "capacity": 8, "equipment": "TV", "description": ""}
        )
        self.assertEqual(res.status, 201, res.text)
        room_id = res.json()["room"]["room_id"]
        res = admin.post(
            "/api/users",
            {
                "user_id": NEW_USER_ID,
                "name": "運用 花子",
                "role": "general",
                "password": NEW_USER_PASSWORD,
            },
        )
        self.assertEqual(res.status, 201, res.text)

        # 手順4: 一般ユーザーで予約を1件作る
        user = server.client()
        self.assertEqual(user.login(NEW_USER_ID, NEW_USER_PASSWORD).status, 200)
        res = user.post(
            "/api/reservations",
            {
                "room_id": room_id,
                "reserved_date": _date(1),
                "start_time": "13:00",
                "end_time": "14:00",
                "title": "運用確認",
                "attendee_user_ids": [],
                "attendee_count": None,
                "note": "",
            },
        )
        self.assertEqual(res.status, 201, res.text)
        reservation_id = res.json()["reservation"]["reservation_id"]

        # 手順6: 意図的に 404 と 403 を発生させる
        self.assertEqual(user.get("/api/reservations/999999").status, 404)
        self.assertEqual(user.get("/api/users?scope=management").status, 403)

        # 手順5: ログの検査(1リクエスト1行のJSON、必要項目が揃っている、秘密を含まない)
        records, lines = self._log_records()
        self.assertTrue(records, "アクセスログが1行もない")
        for record in records:
            for field in REQUIRED_LOG_FIELDS:
                self.assertIn(field, record, record)
        joined = "\n".join(lines)
        self.assertNotIn(ADMIN_PASSWORD, joined, "ログに初期管理者パスワードがある")
        self.assertNotIn(NEW_USER_PASSWORD, joined, "ログに利用者パスワードがある")
        self.assertNotIn("password", joined.lower(), "ログに password の文字列がある")
        sid_value = user.cookie.split("=", 1)[1]
        self.assertNotIn(sid_value, joined, "ログにセッションIDの値がある")
        # 1リクエスト1行: POST /api/auth/login のログ行数 = 実際のログイン回数(admin/user の2回)
        login_lines = [r for r in records if r["path"] == "/api/auth/login"]
        self.assertEqual(len(login_lines), 2, f"ログイン2回に対しログ{len(login_lines)}行")
        # 1リクエスト1行: 予約登録(1回)に対してもログは1行
        create_lines = [
            r for r in records if r["path"] == "/api/reservations" and r["method"] == "POST"
        ]
        self.assertEqual(len(create_lines), 1, f"予約登録1回に対しログ{len(create_lines)}行")

        # 手順6の検証: error_code に NOT_FOUND / FORBIDDEN が記録されている
        codes = {r.get("error_code") for r in records}
        self.assertIn("NOT_FOUND", codes, codes)
        self.assertIn("FORBIDDEN", codes, codes)

        # 手順7: 停止 → 再起動 → 手順3・4のデータが残っている
        self.assertIsNotNone(self._stop())
        server = self._start()
        admin = server.client()
        self.assertEqual(admin.login(ADMIN_ID, ADMIN_PASSWORD).status, 200)
        rooms = admin.get("/api/rooms").json()["rooms"]
        self.assertIn("第1会議室", [r["name"] for r in rooms])
        users = admin.get("/api/users?scope=management").json()["users"]
        self.assertIn(NEW_USER_ID, [u["user_id"] for u in users])
        self.assertEqual(admin.get(f"/api/reservations/{reservation_id}").status, 200)

        # 手順8: 書き込めない DB_PATH では起動が失敗する(中途半端に起動しない)
        blocker = os.path.join(self._tmp.name, "blocker")
        with open(blocker, "w", encoding="utf-8") as handle:
            handle.write("これはディレクトリではない")
        bad = ServerProcess(os.path.join(blocker, "app.db"))
        with self.assertRaises(RuntimeError) as caught:
            bad.start(timeout=15.0)
        self.assertIn("起動", str(caught.exception))
        self.assertIsNotNone(bad.proc.poll(), "プロセスが終了していない")
        self.assertNotEqual(bad.proc.returncode, 0, "異常終了していない")
        bad.stop()


if __name__ == "__main__":
    unittest.main()
