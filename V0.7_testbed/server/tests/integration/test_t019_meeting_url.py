"""T019 — ※CR-001 オンライン会議URLの登録・更新・削除と入力検証(API)。

定義: docs/P008-test-direction/T019-meeting-url.md
仕様: docs/P002-frontend-spec.md 3.3 / 5.3 / 5.7、docs/P003-backend-spec.md 3.5 / 4.2 / 6.4

手順1〜11は `TestClient`(P006 1.1)で実行する。手順12は**実際のOSプロセスを同じDBファイルに対して
起動する**ことで「2回目の初期化」を確認する(1回目の初期化は手順1〜11のアプリ生成時に完了している)。
`ALTER TABLE ... ADD COLUMN` は `IF NOT EXISTS` を持たないため、この確認は必須である
(P006 3.3 V-O-01 / V-O-02)。
"""

from __future__ import annotations

import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from meeting_room import db as db_module
from tests.integration.support import IntegrationTestCase

SERVER_DIR = Path(__file__).resolve().parents[2]

LENGTH_MESSAGE = "オンライン会議URLは500文字以内で入力してください。"
SCHEME_MESSAGE = "オンライン会議URLは http:// または https:// で始まるURLを入力してください。"


def _date(offset_days: int) -> str:
    return (datetime.now() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class T019MeetingUrlTest(IntegrationTestCase):
    seed_rooms = True

    def _body(self, **overrides):
        payload = {
            "room_id": self.room_a["room_id"],
            "reserved_date": _date(2),
            "start_time": "09:00",
            "end_time": "10:00",
            "title": "打合せ",
            "attendee_user_ids": [],
            "attendee_count": None,
            "note": "",
        }
        payload.update(overrides)
        return payload

    def _meeting_url_errors(self, res):
        return [
            d["message"]
            for d in res.json()["error"].get("details", [])
            if d["field"] == "meeting_url"
        ]

    def _migration_count(self):
        conn = sqlite3.connect(self.db_path)
        try:
            return conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
        finally:
            conn.close()

    def setUp(self):
        super().setUp()
        self.assertEqual(self.login("user001").status_code, 200)
        self.room_a = self.client.get("/api/rooms").json()["rooms"][0]
        self.assertEqual(self.room_a["name"], "会議室A")
        # 基準データセットの既存予約(meeting_url 未登録)を、004 適用前と同じ状態で1件作る。
        # 列を明示せずINSERTすることで、DEFAULT '' が効くことを確認する。
        conn = self.db()
        with db_module.transaction(conn):
            conn.execute(
                "INSERT INTO reservations(room_id, user_id, reserved_date, start_time,"
                " end_time, title, attendee_count, note, created_at, updated_at)"
                " VALUES (?, 'user001', ?, '10:00', '11:00', '定例会議', NULL, '',"
                " '2026-08-05T00:00:00Z', '2026-08-05T00:00:00Z')",
                (self.room_a["room_id"], _date(1)),
            )
        self.existing_id = conn.execute(
            "SELECT reservation_id FROM reservations WHERE title = '定例会議'"
        ).fetchone()["reservation_id"]

    def test_t019_meeting_url(self):
        # 手順1: 既存予約(URL未登録)を API-14 で取得 → 空文字であること
        res = self.client.get(f"/api/reservations/{self.existing_id}")
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["reservation"]["meeting_url"], "")

        # 手順2: meeting_url のキー自体を送らずに登録 → 201、空文字
        payload = self._body()
        payload.pop("meeting_url", None)
        res = self.client.post("/api/reservations", json=payload)
        self.assertEqual(res.status_code, 201, res.text)
        self.assertEqual(res.json()["reservation"]["meeting_url"], "")

        # 手順3: https:// のURLで登録 → 201
        url = "https://example.com/meet/abc"
        res = self.client.post(
            "/api/reservations",
            json=self._body(start_time="11:00", end_time="12:00", meeting_url=url),
        )
        self.assertEqual(res.status_code, 201, res.text)
        target_id = res.json()["reservation"]["reservation_id"]
        self.assertEqual(res.json()["reservation"]["meeting_url"], url)

        # 手順4: API-14 で取得 → 同じ値
        res = self.client.get(f"/api/reservations/{target_id}")
        self.assertEqual(res.json()["reservation"]["meeting_url"], url)

        # 手順5: API-16 で http:// のURLに更新 → 置き換わる
        put_body = self._body(start_time="11:00", end_time="12:00")
        res = self.client.put(
            f"/api/reservations/{target_id}",
            json={**put_body, "meeting_url": "http://example.com/meet/xyz"},
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["reservation"]["meeting_url"], "http://example.com/meet/xyz")

        # 手順6: API-16 で空文字に更新 → URLが削除される(全置換更新)
        res = self.client.put(
            f"/api/reservations/{target_id}", json={**put_body, "meeting_url": ""}
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["reservation"]["meeting_url"], "")

        created_before = len(
            self.client.get(
                f"/api/reservations?date_from={_date(2)}&date_to={_date(2)}"
            ).json()["reservations"]
        )

        # 手順7: スキームなし → 400、field=meeting_url、スキームのメッセージ
        res = self.client.post(
            "/api/reservations",
            json=self._body(start_time="13:00", end_time="14:00", meeting_url="example.com/meet"),
        )
        self.assertEqual(res.status_code, 400, res.text)
        self.assertEqual(res.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn(SCHEME_MESSAGE, self._meeting_url_errors(res))

        # 手順8: ftp:// → 400(同じメッセージ)
        res = self.client.post(
            "/api/reservations",
            json=self._body(
                start_time="13:00", end_time="14:00", meeting_url="ftp://example.com/meet"
            ),
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn(SCHEME_MESSAGE, self._meeting_url_errors(res))

        # 手順9: 501文字 → 400、文字数のメッセージ
        url501 = "https://" + "a" * 493
        self.assertEqual(len(url501), 501)
        res = self.client.post(
            "/api/reservations",
            json=self._body(start_time="13:00", end_time="14:00", meeting_url=url501),
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn(LENGTH_MESSAGE, self._meeting_url_errors(res))

        # 手順7〜9で予約が作られていないこと
        self.assertEqual(
            len(
                self.client.get(
                    f"/api/reservations?date_from={_date(2)}&date_to={_date(2)}"
                ).json()["reservations"]
            ),
            created_before,
        )

        # 手順10: 500文字ちょうど → 201
        url500 = "https://" + "a" * 492
        self.assertEqual(len(url500), 500)
        res = self.client.post(
            "/api/reservations",
            json=self._body(start_time="13:00", end_time="14:00", meeting_url=url500),
        )
        self.assertEqual(res.status_code, 201, res.text)
        self.assertEqual(len(res.json()["reservation"]["meeting_url"]), 500)

        # 手順11: API-12(一覧)の各要素に meeting_url キーがある
        res = self.client.get(f"/api/reservations?date_from={_date(2)}&date_to={_date(2)}")
        self.assertEqual(res.status_code, 200)
        reservations = res.json()["reservations"]
        self.assertGreater(len(reservations), 0)
        for reservation in reservations:
            self.assertIn("meeting_url", reservation)
            self.assertIsInstance(reservation["meeting_url"], str)

        # 手順12: 同じDBファイルに対して2回目の起動(実プロセス)が成功する
        self.assertEqual(self._migration_count(), 4, "004 までが適用済み")
        port = _free_port()
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SERVER_DIR / "src")
        env["DB_PATH"] = self.db_path
        env["INITIAL_ADMIN_ID"] = "admin001"
        env["INITIAL_ADMIN_PASSWORD"] = "Passw0rd!23"
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "meeting_room.main:app",
             "--port", str(port), "--log-level", "warning"],
            cwd=str(SERVER_DIR), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        try:
            deadline = time.time() + 20
            started = False
            while time.time() < deadline:
                if process.poll() is not None:
                    self.fail(
                        "2回目の起動が失敗した(duplicate column name 等): "
                        f"{process.stdout.read()[-2000:]}"
                    )
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1):
                        started = True
                        break
                except (urllib.error.URLError, ConnectionError, OSError):
                    time.sleep(0.2)
            self.assertTrue(started, "2回目の起動待ちがタイムアウトした")

            # 2回目の起動でも API-12 が使える(ログインしてから呼ぶ)
            login = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/auth/login",
                data=json.dumps({"user_id": "user001", "password": "Passw0rd!23"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(login, timeout=5) as response:
                self.assertEqual(response.status, 200)
                cookie = response.headers.get("set-cookie", "").split(";")[0]
            listing = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/reservations"
                f"?date_from={_date(2)}&date_to={_date(2)}",
                headers={"Cookie": cookie},
            )
            with urllib.request.urlopen(listing, timeout=5) as response:
                self.assertEqual(response.status, 200)
                body = json.loads(response.read().decode("utf-8"))
            self.assertTrue(all("meeting_url" in r for r in body["reservations"]))
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()

        # 004 が二重適用されていない
        self.assertEqual(self._migration_count(), 4, "再起動で schema_migrations が増えていない")


if __name__ == "__main__":
    unittest.main()
