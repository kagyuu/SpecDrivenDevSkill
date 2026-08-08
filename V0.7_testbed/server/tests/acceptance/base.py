"""受け入れ結合テストの共通 TestCase(`docs/P009-acceptance-direction.md` 3章)。

* 原則として開始時にDBファイルを作り直して基準データセットを投入する。
* 例外は A007(再起動耐性)で、同じDBファイルを使い回すため本クラスを使わない。
"""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta

from tests.acceptance.support import HttpClient, ServerProcess
from tests.fixtures import seed

PASSWORD = seed.PASSWORD


def day(offset: int) -> str:
    """固定日付を使わず、実行時の「本日」からの相対で日付を作る(P009 3章)。"""
    return (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")


class AcceptanceTestCase(unittest.TestCase):
    seed_rooms = True
    env_extra: dict = {}

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = os.path.join(self._tmp.name, "app.db")
        self.log_path = os.path.join(self._tmp.name, "server.log")
        self.server = ServerProcess(
            self.db_path, env_extra=self.env_extra, log_path=self.log_path
        )
        self.server.start()
        self.addCleanup(self.server.stop)
        # 基準データセット(P006 5章)。admin001 は起動時シードで既に存在する
        seed.seed_users(self.db_path)
        if self.seed_rooms:
            seed.seed_rooms(self.db_path)
        self.client = self.server.client()

    def new_client(self) -> HttpClient:
        return self.server.client()

    def login(self, user_id: str, password: str = PASSWORD):
        return self.client.login(user_id, password)

    def db(self):
        from meeting_room import db as db_module

        conn = db_module.connect(self.db_path)
        self.addCleanup(conn.close)
        return conn

    def room_ids(self) -> dict:
        """会議室名 → room_id(無効な会議室も含む。DBから直接引く)。"""
        return {
            row["name"]: row["room_id"]
            for row in self.db().execute("SELECT room_id, name FROM rooms")
        }

    def server_log(self) -> str:
        with open(self.log_path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def log_records(self) -> list[dict]:
        """アクセスログ行(JSON)のみを取り出す。"""
        records = []
        for line in self.server_log().splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                records.append(__import__("json").loads(line))
            except ValueError:
                continue
        return records

    def reservation_body(self, room_id, reserved_date=None, start="10:00", end="11:00", **extra):
        body = {
            "room_id": room_id,
            "reserved_date": reserved_date or day(1),
            "start_time": start,
            "end_time": end,
            "title": "打合せ",
            "attendee_user_ids": [],
            "attendee_count": None,
            "note": "",
        }
        body.update(extra)
        return body
