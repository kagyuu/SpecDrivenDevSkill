"""結合テスト共通の起動処理(P008 3章「開始時にDBファイルを削除して作り直す」)。"""

from __future__ import annotations

import os
import tempfile
import unittest

from starlette.testclient import TestClient

from meeting_room import main
from tests.fixtures import seed


class IntegrationTestCase(unittest.TestCase):
    """DBファイルを作り直してアプリを起動し、基準データセットを投入する。

    HTTPクライアントは `httpx`(Starlette の TestClient 経由)を用いる(P006 1.1)。
    `Secure` 属性付きCookieを保持させるため https スキームで駆動する。
    """

    seed_rooms = False

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = os.path.join(self._tmp.name, "app.db")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.app = main.create_app(db_path=self.db_path)
        seed.seed_users(self.db_path)
        if self.seed_rooms:
            seed.seed_rooms(self.db_path)
        self.client = TestClient(self.app, base_url="https://testserver")
        self.addCleanup(self.client.close)

    def login(self, user_id: str, password: str = seed.PASSWORD):
        self.client.cookies.clear()
        return self.client.post(
            "/api/auth/login", json={"user_id": user_id, "password": password}
        )

    def db(self):
        from meeting_room import db as db_module

        conn = db_module.connect(self.db_path)
        self.addCleanup(conn.close)
        return conn
