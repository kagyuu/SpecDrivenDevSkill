"""P201 acceptance test A009 (docs/P009-acceptance-direction/A009-restart-resilience.md).

Required, not optional per this task's own note ("省略・NOT RUN化は原則として
認められない"). Uses a real subprocess and a real, persistent (non-temp)
SQLite file, stopping and restarting the server process 3 times total to
confirm the migration mechanism (server/app/db/migration.py) is genuinely
idempotent across real restarts, not just the "apply twice within one
Python process" check already covered by
server/tests/test_migration.py::test_apply_pending_migrations_is_idempotent.
"""

from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

import httpx

SERVER_DIR = Path(__file__).resolve().parent.parent.parent
PYTHON_EXE = SERVER_DIR / ".venv" / "Scripts" / "python.exe"
PORT = 8732
BASE_URL = f"http://127.0.0.1:{PORT}"
DB_PATH = SERVER_DIR / "data" / "acceptance-test-restart.db"


def _start_server() -> subprocess.Popen:
    env = {**os.environ, "DATABASE_PATH": str(DB_PATH), "COOKIE_SECURE": "false"}
    process = subprocess.Popen(
        [str(PYTHON_EXE), "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
        cwd=str(SERVER_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            response = httpx.get(f"{BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                return process
        except httpx.HTTPError:
            pass
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"server process exited early:\n{output}")
        time.sleep(0.2)
    process.kill()
    raise RuntimeError("server did not become ready within 20s")


def _stop_server(process: subprocess.Popen) -> str:
    """正常停止(SIGTERM)し、起動ログ全文を返す。"""
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    return process.stdout.read() if process.stdout else ""


def test_the_server_survives_three_consecutive_restarts_with_data_intact():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    logs: list[str] = []
    try:
        # 1回目起動 + データ投入
        process = _start_server()
        login = httpx.post(
            f"{BASE_URL}/api/auth/login",
            json={"employee_id": "admin", "password": "ChangeMe123!"},
            timeout=10,
        )
        assert login.status_code == 200
        session_cookie = login.cookies["session_id"]

        room_response = httpx.post(
            f"{BASE_URL}/api/rooms",
            json={"name": "第一会議室", "capacity": 8, "equipment": [], "description": None},
            cookies={"session_id": session_cookie},
            timeout=10,
        )
        assert room_response.status_code == 201
        room_id = room_response.json()["room_id"]

        reservation_response = httpx.post(
            f"{BASE_URL}/api/reservations",
            json={
                "room_id": room_id,
                "date": "2099-01-01",
                "start_time": "10:00",
                "end_time": "11:00",
                "title": "再起動確認予約",
                "participant_user_ids": [],
                "attendee_count": None,
                "notes": None,
            },
            cookies={"session_id": session_cookie},
            timeout=10,
        )
        assert reservation_response.status_code == 201

        # 手順1: 正常停止
        logs.append(_stop_server(process))

        # 2回目・3回目起動(手順2〜6)
        for attempt in (2, 3):
            process = _start_server()
            health = httpx.get(f"{BASE_URL}/health", timeout=5)
            assert health.status_code == 200, f"attempt {attempt}: /health did not return 200"

            login = httpx.post(
                f"{BASE_URL}/api/auth/login",
                json={"employee_id": "admin", "password": "ChangeMe123!"},
                timeout=10,
            )
            assert login.status_code == 200, f"attempt {attempt}: login failed"
            session_cookie = login.cookies["session_id"]

            rooms = httpx.get(
                f"{BASE_URL}/api/rooms",
                cookies={"session_id": session_cookie},
                timeout=10,
            ).json()
            assert any(r["name"] == "第一会議室" for r in rooms), (
                f"attempt {attempt}: seeded room missing after restart"
            )

            reservations = httpx.get(
                f"{BASE_URL}/api/reservations",
                params={"date_from": "2099-01-01", "date_to": "2099-01-01"},
                cookies={"session_id": session_cookie},
                timeout=10,
            ).json()
            assert any(r["title"] == "再起動確認予約" for r in reservations), (
                f"attempt {attempt}: seeded reservation missing after restart"
            )

            log = _stop_server(process)
            logs.append(log)
            assert "duplicate column" not in log
            assert "Traceback" not in log
    finally:
        if DB_PATH.exists():
            DB_PATH.unlink()
