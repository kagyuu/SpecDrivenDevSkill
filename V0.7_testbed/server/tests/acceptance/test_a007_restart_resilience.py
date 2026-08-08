"""A007 — 再起動耐性とデータ永続(運用観点 V-O-01 / V-O-02。必須)。

docs/P009-acceptance-direction/A007-restart-resilience.md
**同じDBファイルを使い回す**(他のテストのように途中で作り直さない)ため、
`AcceptanceTestCase` は使わず独自にプロセスを起動・停止する。
"""

from __future__ import annotations

import os
import signal
import tempfile
import unittest

from pathlib import Path

from tests.acceptance.support import ServerProcess
from tests.fixtures import seed

#: ※CR-001 マイグレーションファイルの本数(004-meeting-url.sql を含む)
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"

ERROR_MARKERS = (
    "Traceback",
    "duplicate column name",
    "already exists",
    "OperationalError",
    "IntegrityError",
)


def _date(offset: int) -> str:
    from datetime import datetime, timedelta

    return (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")


class A007RestartResilienceTest(unittest.TestCase):
    def setUp(self):
        # 手順(事前準備)1: DBファイルを削除する。以降、同じDBファイルを使い回す
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = os.path.join(self._tmp.name, "app.db")
        self.log_path = os.path.join(self._tmp.name, "server.log")
        for suffix in ("", "-wal", "-shm"):
            if os.path.exists(self.db_path + suffix):
                os.remove(self.db_path + suffix)
        self.server = None
        self.addCleanup(self._stop)

    def _stop(self, sig=signal.SIGTERM):
        if self.server is not None:
            rc = self.server.stop(sig)
            self.server = None
            return rc
        return None

    def _start(self):
        self.server = ServerProcess(self.db_path, log_path=self.log_path)
        self.server.start()
        return self.server

    def _counts(self):
        from meeting_room import db as db_module

        conn = db_module.connect(self.db_path)
        try:
            return (
                conn.execute("SELECT COUNT(*) AS c FROM schema_migrations").fetchone()["c"],
                conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"],
                conn.execute("SELECT COUNT(*) AS c FROM reservations").fetchone()["c"],
                conn.execute(
                    "SELECT COUNT(*) AS c FROM users WHERE role = 'admin'"
                ).fetchone()["c"],
            )
        finally:
            conn.close()

    def _log(self) -> str:
        if not os.path.exists(self.log_path):
            return ""
        with open(self.log_path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def _assert_no_startup_error(self, label: str):
        log = self._log()
        for marker in ERROR_MARKERS:
            self.assertNotIn(marker, log, f"{label}: 起動ログにエラー痕跡 '{marker}' がある\n{log}")

    def test_restart_resilience(self):
        # ---- 1回目の起動 ----
        server = self._start()
        migrations_1, users_1, _, admins_1 = self._counts()
        self.assertGreater(migrations_1, 0, "マイグレーションが1件も適用されていない")
        # ※CR-001: 004-meeting-url.sql(ALTER TABLE ... ADD COLUMN)を含む4本が適用されている。
        # ADD COLUMN は IF NOT EXISTS を持たないため、以降の再起動でこの本数が増えず、
        # かつ起動が成功することが、差分適用の冪等性の確認そのものになる(P006 3.3 V-O-01/V-O-02)。
        self.assertEqual(
            migrations_1,
            len(list(MIGRATIONS_DIR.glob("*.sql"))),
            "適用済みマイグレーション数がファイル数と一致しない",
        )
        self._assert_no_startup_error("1回目")

        # 手順2: 基準データセットと user001 の予約1件を投入する
        seed.seed_users(self.db_path)
        seed.seed_rooms(self.db_path)
        client = server.client()
        self.assertEqual(client.login("user001").status, 200)
        room_id = client.get("/api/rooms").json()["rooms"][0]["room_id"]
        res = client.post(
            "/api/reservations",
            {
                "room_id": room_id,
                "reserved_date": _date(1),
                "start_time": "10:00",
                "end_time": "11:00",
                "title": "再起動をまたぐ予約",
                "attendee_user_ids": [],
                "attendee_count": None,
                "note": "",
            },
        )
        self.assertEqual(res.status, 201, res.text)
        reservation_id = res.json()["reservation"]["reservation_id"]
        migrations_seeded, users_seeded, reservations_seeded, admins_seeded = self._counts()
        self.assertEqual(reservations_seeded, 1)

        # 手順3〜7: 停止 → 同じDBファイルのまま起動、を2回繰り返す(合計3回起動)
        for attempt in (2, 3):
            label = f"{attempt}回目"
            rc = self._stop(signal.SIGTERM)
            self.assertIsNotNone(rc, f"{label}: 停止できていない")
            self.assertTrue(
                os.path.exists(self.db_path), f"{label}: 停止でDBファイルが消えている"
            )
            server = self._start()
            self._assert_no_startup_error(label)

            migrations_n, users_n, reservations_n, admins_n = self._counts()
            # 手順5: schema_migrations が増えていない / 初期管理者が二重に作られていない
            self.assertEqual(
                migrations_n, migrations_seeded, f"{label}: schema_migrations が増えている"
            )
            self.assertEqual(users_n, users_seeded, f"{label}: users の行数が変わっている")
            self.assertEqual(admins_n, admins_seeded, f"{label}: 管理者が二重に作られている")
            self.assertEqual(reservations_n, 1, f"{label}: 予約が失われている")

            # 手順6: ログインして予約が取得できる
            client = server.client()
            self.assertEqual(client.login("user001").status, 200, f"{label}: ログインできない")
            mine = client.get("/api/reservations/mine?period=upcoming")
            self.assertEqual(mine.status, 200, mine.text)
            ids = [r["reservation_id"] for r in mine.json()["reservations"]]
            self.assertIn(reservation_id, ids, f"{label}: 予約が取得できない")
            rooms = client.get("/api/rooms").json()["rooms"]
            self.assertEqual(len(rooms), 2, f"{label}: 有効な会議室が2件でない")

        # 手順8: WALファイル(*.db-wal / *.db-shm)が残っている状態で停止・起動できる。
        # SQLiteは最終接続のクローズ時にWALをチェックポイントして削除するため、
        # WALを「残す」には接続を1本開いたままにする必要がある(テスト側で保持する)。
        from meeting_room import db as db_module

        holder = db_module.connect(self.db_path)
        self.addCleanup(holder.close)
        self.assertEqual(holder.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        holder.execute("SELECT COUNT(*) FROM reservations").fetchone()
        self.assertTrue(
            os.path.exists(self.db_path + "-wal"), "WALファイルが作られていない(WAL未設定?)"
        )
        self.assertTrue(os.path.exists(self.db_path + "-shm"), "SHMファイルが作られていない")
        self._stop(signal.SIGTERM)
        self.assertTrue(os.path.exists(self.db_path + "-wal"), "停止後にWALが消えている")
        server = self._start()
        self._assert_no_startup_error("4回目(WAL残存)")
        client = server.client()
        self.assertEqual(client.login("user001").status, 200)
        self.assertEqual(client.get(f"/api/reservations/{reservation_id}").status, 200)


if __name__ == "__main__":
    unittest.main()
