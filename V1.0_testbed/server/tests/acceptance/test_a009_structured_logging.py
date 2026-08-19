"""docs/P009-acceptance-direction/A009-structured-logging.md

標準出力への構造化ログ(JSON Lines)出力が実際に行われていることを確認する。
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from tests.acceptance.server_process_helper import start_server, stop_server

PORT = 8003
DB_PATH = Path(__file__).resolve().parents[2] / "data" / "a009_logging_test.db"
LOG_PATH = Path(__file__).resolve().parents[2] / "data" / "a009_logging_test.log"


def _request(base_url, method, path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(f"{base_url}{path}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


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


def _json_lines(log_path: Path) -> list[dict]:
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    parsed = []
    for line in lines:
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        parsed.append(json.loads(line))
    return parsed


def test_login_success_and_failure_produce_structured_json_logs():
    process, log_file, base_url = start_server(DB_PATH, PORT, LOG_PATH)
    try:
        status_success = _request(
            base_url, "POST", "/api/auth/login",
            {"employee_id": "user001", "password": "TestPassw0rd!"},
        )
        assert status_success == 200

        status_failure = _request(
            base_url, "POST", "/api/auth/login",
            {"employee_id": "user001", "password": "WrongPassword1"},
        )
        assert status_failure == 401
    finally:
        stop_server(process, log_file)

    entries = _json_lines(LOG_PATH)
    assert entries, "ログファイルにJSON行が1件も無い"

    request_entries = [e for e in entries if e.get("event") == "request"]
    login_entries = [e for e in request_entries if e.get("path") == "/api/auth/login"]
    assert len(login_entries) == 2, f"ログイン関連のリクエストログが2件見つからない(実際: {len(login_entries)}件)"

    for entry in login_entries:
        assert "status_code" in entry
        assert "timestamp" in entry

    failure_entries = [e for e in login_entries if e.get("status_code") == 401]
    assert failure_entries, "失敗したログインのログ行が見つからない"
    for entry in failure_entries:
        assert "error_code" in entry, (
            "失敗時のログ行に error_code 相当のフィールドが含まれていない: " + json.dumps(entry, ensure_ascii=False)
        )
