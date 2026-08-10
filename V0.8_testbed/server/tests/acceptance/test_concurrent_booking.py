"""P201 acceptance test A005 (docs/P009-acceptance-direction/A005-concurrent-booking-prevention.md).

Real HTTP requests over the network against a real, separately-started
uvicorn process (not the in-process TestClient used elsewhere) - this is
the whole point of this test per its own 目的: verifying exclusive control
holds under genuine concurrent HTTP load, not just within one Python
process/thread.

Per this task's own ★FIXME★, uses 30 concurrent HTTP clients sharing one
authenticated admin session (same cookie) rather than 30 distinct user
accounts - what matters is 30 concurrent request sources hitting the same
slot, not that they are different users.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest

SERVER_DIR = Path(__file__).resolve().parent.parent.parent
PYTHON_EXE = SERVER_DIR / ".venv" / "Scripts" / "python.exe"
PORT = 8731
BASE_URL = f"http://127.0.0.1:{PORT}"


@pytest.fixture()
def running_server(tmp_path: Path):
    db_path = tmp_path / "acceptance_concurrent.db"
    env = {**os.environ, "DATABASE_PATH": str(db_path), "COOKIE_SECURE": "false"}
    process = subprocess.Popen(
        [str(PYTHON_EXE), "-m", "uvicorn", "app.main:app", "--port", str(PORT)],
        cwd=str(SERVER_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                response = httpx.get(f"{BASE_URL}/health", timeout=1)
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("server did not become ready")
        yield
    finally:
        process.send_signal(signal.SIGTERM if sys.platform != "win32" else signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_thirty_concurrent_requests_for_the_same_slot_create_only_one_reservation(running_server):
    login_response = httpx.post(
        f"{BASE_URL}/api/auth/login",
        json={"employee_id": "admin", "password": "ChangeMe123!"},
        timeout=10,
    )
    assert login_response.status_code == 200
    session_cookie = login_response.cookies["session_id"]

    room_response = httpx.post(
        f"{BASE_URL}/api/rooms",
        json={"name": "第一会議室", "capacity": 8, "equipment": [], "description": None},
        cookies={"session_id": session_cookie},
        timeout=10,
    )
    assert room_response.status_code == 201
    room_id = room_response.json()["room_id"]

    body = {
        "room_id": room_id,
        "date": "2099-01-01",
        "start_time": "15:00",
        "end_time": "16:00",
        "title": "同時実行テスト",
        "participant_user_ids": [],
        "attendee_count": None,
        "notes": None,
    }

    def attempt(_: int) -> int:
        with httpx.Client(cookies={"session_id": session_cookie}, timeout=10) as client:
            response = client.post(f"{BASE_URL}/api/reservations", json=body)
            return response.status_code

    # 手順1: 30並列でPOSTを送信する
    with ThreadPoolExecutor(max_workers=30) as executor:
        statuses = list(executor.map(attempt, range(30)))

    # 手順2
    status_counts: dict[int, int] = {}
    for status in statuses:
        status_counts[status] = status_counts.get(status, 0) + 1

    # 手順3
    list_response = httpx.get(
        f"{BASE_URL}/api/reservations",
        params={"date_from": "2099-01-01", "date_to": "2099-01-01", "room_id": room_id},
        cookies={"session_id": session_cookie},
        timeout=10,
    )
    reservation_count = len(list_response.json())

    assert status_counts.get(201, 0) == 1, f"expected exactly one 201, got distribution {status_counts}"
    assert reservation_count == 1, f"expected exactly one reservation row, got {reservation_count}"
