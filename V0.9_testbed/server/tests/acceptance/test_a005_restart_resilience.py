"""docs/P009-acceptance-direction/A005-restart-resilience.md

永続化された同一のSQLiteファイルに対して実際にプロセスを3回起動し、マイグレーションが
冪等であること・データが失われないことを確認する。
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from tests.acceptance.server_process_helper import start_server, stop_server

PORT = 8002
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "a005_restart_test.db"
LOG_PATH = Path(__file__).resolve().parents[2] / "data" / "a005_restart_test.log"


class _Session:
    """Cookieの `Secure` 属性はプレーンHTTPでは(ブラウザの仕様として正しく)送出されない。

    本テストが確認したいのはマイグレーション・データ永続化の挙動であり、Cookieの
    Secure属性ポリシーの検証ではないため、`http.cookiejar` のオリジン/スキーム制約を
    経由せず、レスポンスの `Set-Cookie` からトークン値を取り出して次リクエストの
    `Cookie` ヘッダーに手動で載せる(ブラウザのセキュリティ挙動を意図的にバイパスする、
    テスト内部専用の単純化)。
    """

    def __init__(self, base_url: str):
        self.base_url = base_url
        self._cookie_value: str | None = None

    def request(self, method: str, path: str, body: dict | None = None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(f"{self.base_url}{path}", data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self._cookie_value:
            req.add_header("Cookie", f"session_id={self._cookie_value}")

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                self._capture_cookie(resp.headers.get("Set-Cookie"))
                return resp.status, json.loads(resp.read().decode("utf-8") or "null")
        except urllib.error.HTTPError as exc:
            self._capture_cookie(exc.headers.get("Set-Cookie"))
            return exc.code, json.loads(exc.read().decode("utf-8") or "null")

    def _capture_cookie(self, set_cookie_header: str | None) -> None:
        if not set_cookie_header:
            return
        match = re.search(r"session_id=([^;]+)", set_cookie_header)
        if match:
            self._cookie_value = match.group(1)


@pytest.fixture(autouse=True)
def _cleanup_db_files():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    for path in (DB_PATH, LOG_PATH):
        if path.exists():
            path.unlink()
    yield
    for path in (DB_PATH, LOG_PATH):
        if path.exists():
            path.unlink()


def test_three_consecutive_restarts_preserve_data_and_do_not_error():
    room_id = None

    for round_number in range(1, 4):
        process, log_file, base_url = start_server(DB_PATH, PORT, LOG_PATH)
        try:
            log_contents_at_startup = LOG_PATH.read_text(encoding="utf-8", errors="replace")
            assert "duplicate column" not in log_contents_at_startup.lower(), (
                f"{round_number}回目の起動でマイグレーションエラーの疑いのあるログが出力された"
            )
            assert "Traceback" not in log_contents_at_startup, (
                f"{round_number}回目の起動時にトレースバックが出力された"
            )

            session = _Session(base_url)
            status, _ = session.request(
                "POST", "/api/auth/login",
                {"employee_id": "admin001", "password": "TestPassw0rd!"},
            )
            assert status == 200, f"{round_number}回目の起動後のログインに失敗した"

            if round_number == 1:
                status, room = session.request("POST", "/api/rooms", {"name": "会議室Z", "capacity": 8})
                assert status == 201, f"会議室登録に失敗: {status} {room}"
                room_id = room["id"]

                status, res = session.request(
                    "POST", "/api/reservations",
                    {
                        "room_id": room_id,
                        "date": "2026-08-20",
                        "start_time": "15:00",
                        "end_time": "16:00",
                        "title": "再起動確認用",
                    },
                )
                assert status == 201, f"予約登録に失敗: {status} {res}"
            else:
                status, rooms = session.request("GET", "/api/rooms")
                assert status == 200
                assert any(r["id"] == room_id and r["name"] == "会議室Z" for r in rooms), (
                    f"{round_number}回目の起動後、会議室データが失われている"
                )

                status, reservations = session.request(
                    "GET", "/api/reservations?date_from=2026-08-20&date_to=2026-08-20"
                )
                assert status == 200
                assert any(r["title"] == "再起動確認用" for r in reservations), (
                    f"{round_number}回目の起動後、予約データが失われている"
                )
        finally:
            stop_server(process, log_file)
