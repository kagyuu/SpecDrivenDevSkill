"""T004 — 既存DBに対する再起動とマイグレーション差分適用。

同じDBファイルを意図的に使い回す(P008 3章の例外)。実際にサーバープロセスを
起動・停止して確認するため、`uvicorn` をサブプロセスとして起動する。
"""

from __future__ import annotations

import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = SERVER_DIR / "migrations"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class T004RestartMigrationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        # 手順0(事前準備): DBファイルを削除する。以降は同じファイルを使い回す
        self.db_path = os.path.join(self._tmp.name, "app.db")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.port = _free_port()

    def _start_server(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SERVER_DIR / "src")
        env["DB_PATH"] = self.db_path
        env["INITIAL_ADMIN_ID"] = "admin001"
        env["INITIAL_ADMIN_PASSWORD"] = "Passw0rd!23"
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "meeting_room.main:app",
             "--port", str(self.port), "--log-level", "warning"],
            cwd=str(SERVER_DIR), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        deadline = time.time() + 20
        while time.time() < deadline:
            if process.poll() is not None:
                self.fail(f"サーバーが起動せず終了した: {process.stdout.read()[-2000:]}")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/", timeout=1):
                    return process
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.2)
        process.kill()
        self.fail("サーバーの起動待ちがタイムアウトした")

    def _stop(self, process):
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()

    def _counts(self):
        conn = sqlite3.connect(self.db_path)
        try:
            migrations = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
            users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            admins = conn.execute(
                "SELECT COUNT(*) FROM users WHERE user_id = 'admin001'"
            ).fetchone()[0]
            return migrations, users, admins
        finally:
            conn.close()

    def test_restart_applies_no_new_migrations(self):
        migration_files = len(list(MIGRATIONS_DIR.glob("*.sql")))

        # 手順1: 1回目の起動
        process = self._start_server()
        first = self._counts()
        self._stop(process)  # 手順2: 停止
        self.assertEqual(first[0], migration_files, "schema_migrations の行数 = マイグレーション数")
        self.assertEqual(first[2], 1, "初期管理者が1件")

        # 手順3: 同じDBファイルのまま再起動
        process = self._start_server()
        # 手順4: 行数が増えていない
        second = self._counts()
        self.assertEqual(second, first, "再起動で schema_migrations / users が増えていない")

        # 手順5: 初期管理者でログインできる
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/auth/login",
            data=json.dumps({"user_id": "admin001", "password": "Passw0rd!23"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)
        self._stop(process)

        # 手順6: 3回目の起動
        process = self._start_server()
        third = self._counts()
        self._stop(process)
        self.assertEqual(third, first, "3回目の起動でも行数が増えていない")


if __name__ == "__main__":
    unittest.main()
